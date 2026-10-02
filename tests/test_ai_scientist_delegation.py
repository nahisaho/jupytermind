"""Tests for ai_scientist phase delegation adapters."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_handle(tmp_path, monkeypatch, project_name: str = "delegation-study"):
    monkeypatch.setenv("AI_DATA_SCIENTIST_PROJECTS_ROOT", str(tmp_path / "projects"))
    from ai_scientist.project_handle import resolve_research_project

    return resolve_research_project(project_name)


def _seed_research_evidence(handle):
    from ai_scientist.evidence_registry import record_evidence

    phase_map = {
        "research-planning": handle.planning_dir / "plan.md",
        "literature-review": handle.literature_dir / "literature.md",
        "experimental-design": handle.design_dir / "design.md",
        "data-analysis": handle.notebook_path,
    }
    for phase, path in phase_map.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".ipynb":
            path.write_text("{}", encoding="utf-8")
            artifact_kind = "notebook"
        else:
            path.write_text(phase, encoding="utf-8")
            artifact_kind = "markdown"
        record_evidence(handle, phase, path, artifact_kind, _timestamp())


class _RecordingMcpClient:
    def __init__(self):
        self.calls: list[str] = []

    def execute(self, code: str) -> dict:
        self.calls.append(code)
        return {"status": "ok", "output": f"executed: {code}"}


class _FakeSkillInvoker:
    def __init__(self):
        self.calls: list[tuple[str, str, str, dict]] = []

    def invoke(self, skill_id: str, version: str, mode: str, payload: dict) -> dict:
        self.calls.append((skill_id, version, mode, payload))
        if skill_id == "tech-writer" and mode == "write":
            return {
                "content": "# Title\n\n## Abstract\nA summary.\n\n## Results\nStrong findings.",
            }
        if skill_id == "tech-writer" and mode == "review":
            return {"content": "English review findings"}
        if skill_id == "japanese-prose" and mode == "review":
            return {"content": "日本語の査読コメント"}
        if skill_id == "presentation-planner":
            return {"content": "Presentation brief\n\n- Slide 1"}
        raise AssertionError(f"unexpected invocation: {skill_id=} {mode=}")


# @id TEST-AISCI-008
# @verifies REQ-AISCI-008
def test_TEST_AISCI_008_integration_delegates_data_analysis_to_ai_data_scientist(
    tmp_path, monkeypatch
):
    handle = _resolve_handle(tmp_path, monkeypatch, "analysis-study")
    client = _RecordingMcpClient()

    import ai_data_scientist.project_manager as pm
    from ai_scientist.data_analysis import delegate_data_analysis
    from ai_scientist.evidence_registry import query_evidence

    seen_names: list[str] = []
    seen_handles: list[str] = []
    original_resolve_project = pm.resolve_project
    original_ensure_notebook = pm.ensure_notebook

    def spy_resolve_project(name, projects_root=None):
        seen_names.append(name)
        return original_resolve_project(name, projects_root=projects_root)

    def spy_ensure_notebook(project_handle):
        seen_handles.append(project_handle.name)
        return original_ensure_notebook(project_handle)

    monkeypatch.setattr(pm, "resolve_project", spy_resolve_project)
    monkeypatch.setattr(pm, "ensure_notebook", spy_ensure_notebook)

    result = delegate_data_analysis(handle, "1 + 1", mcp_client=client)

    assert seen_names == ["analysis-study"]
    assert seen_handles == ["analysis-study"]
    assert client.calls == ["1 + 1"]
    assert result["notebook_path"] == str(handle.notebook_path)
    assert handle.notebook_path.exists()
    assert query_evidence(handle, "data-analysis")[0].artifact_path == str(handle.notebook_path)


# @id TEST-AISCI-029
# @verifies REQ-AISCI-008
def test_TEST_AISCI_029_requires_mcp_execution_before_recording_data_analysis_evidence(
    tmp_path, monkeypatch
):
    handle = _resolve_handle(tmp_path, monkeypatch, "analysis-without-mcp")

    from ai_scientist.data_analysis import delegate_data_analysis
    from ai_scientist.evidence_registry import query_evidence

    with pytest.raises(ValueError, match="MCP client"):
        delegate_data_analysis(handle, "1 + 1", mcp_client=None)

    assert query_evidence(handle, "data-analysis") == []


# @id TEST-AISCI-009
# @verifies REQ-AISCI-009
def test_TEST_AISCI_009_delegates_manuscript_writing_to_tech_writer(tmp_path, monkeypatch):
    handle = _resolve_handle(tmp_path, monkeypatch, "manuscript-study")
    _seed_research_evidence(handle)
    invoker = _FakeSkillInvoker()

    from ai_scientist.manuscript import write_manuscript

    result = write_manuscript(handle, "Draft the manuscript.", invoker=invoker)

    assert invoker.calls[0][0:3] == ("tech-writer", "0.3.0", "write")
    payload = invoker.calls[0][3]
    assert payload["project"]["name"] == "manuscript-study"
    assert len(payload["evidenceManifest"]) == 4
    assert result["artifact"]["path"].endswith(".md")
    assert Path(result["artifact"]["path"]).read_text(encoding="utf-8").startswith("# Title")


# @id TEST-AISCI-010
# @verifies REQ-AISCI-010
def test_TEST_AISCI_010_persists_manuscript_language_metadata_from_instruction(
    tmp_path, monkeypatch
):
    handle = _resolve_handle(tmp_path, monkeypatch, "language-study")
    _seed_research_evidence(handle)
    invoker = _FakeSkillInvoker()

    from ai_scientist.manuscript import write_manuscript

    japanese = write_manuscript(handle, "この研究の原稿を書いてください。", invoker=invoker)
    english = write_manuscript(handle, "Write the manuscript in English.", invoker=invoker)

    assert japanese["artifact"]["metadata"]["language"] == "ja"
    assert english["artifact"]["metadata"]["language"] == "en"


# @id TEST-AISCI-011
# @verifies REQ-AISCI-011
def test_TEST_AISCI_011_routes_japanese_peer_review_to_japanese_prose(tmp_path, monkeypatch):
    handle = _resolve_handle(tmp_path, monkeypatch, "peer-ja")
    _seed_research_evidence(handle)
    invoker = _FakeSkillInvoker()

    from ai_scientist.manuscript import write_manuscript
    from ai_scientist.peer_review import review_manuscript

    manuscript = write_manuscript(handle, "この研究の原稿を書いてください。", invoker=invoker)
    review = review_manuscript(handle, invoker=invoker)

    assert invoker.calls[-1][0:3] == ("japanese-prose", "0.3.0", "review")
    assert invoker.calls[-1][3]["manuscriptPath"] == manuscript["artifact"]["path"]
    assert review["artifact"]["phase"] == "peer-review"
    assert review["artifact"]["path"] != manuscript["artifact"]["path"]


# @id TEST-AISCI-012
# @verifies REQ-AISCI-012
def test_TEST_AISCI_012_routes_english_peer_review_to_tech_writer(tmp_path, monkeypatch):
    handle = _resolve_handle(tmp_path, monkeypatch, "peer-en")
    _seed_research_evidence(handle)
    invoker = _FakeSkillInvoker()

    from ai_scientist.manuscript import write_manuscript
    from ai_scientist.peer_review import review_manuscript

    manuscript = write_manuscript(handle, "Write the manuscript in English.", invoker=invoker)
    review = review_manuscript(handle, invoker=invoker)

    assert invoker.calls[-1][0:3] == ("tech-writer", "0.3.0", "review")
    assert invoker.calls[-1][3]["manuscriptPath"] == manuscript["artifact"]["path"]
    assert review["artifact"]["phase"] == "peer-review"


# @id TEST-AISCI-013
# @verifies REQ-AISCI-013
def test_TEST_AISCI_013_blocks_peer_review_without_supported_language_metadata(
    tmp_path, monkeypatch
):
    handle = _resolve_handle(tmp_path, monkeypatch, "peer-block")

    from ai_scientist.evidence_registry import record_evidence
    from ai_scientist.peer_review import PeerReviewBlockedError, review_manuscript

    manuscript = handle.manuscript_dir / "draft.md"
    manuscript.write_text("# Draft", encoding="utf-8")
    record_evidence(handle, "manuscript-writing", manuscript, "markdown", _timestamp())

    with pytest.raises(PeerReviewBlockedError, match="language metadata"):
        review_manuscript(handle, invoker=_FakeSkillInvoker())

    handle_unsupported = _resolve_handle(tmp_path, monkeypatch, "peer-fr")
    manuscript2 = handle_unsupported.manuscript_dir / "draft.md"
    manuscript2.write_text("# Brouillon", encoding="utf-8")
    record_evidence(
        handle_unsupported,
        "manuscript-writing",
        manuscript2,
        "markdown",
        _timestamp(),
        metadata={"language": "fr"},
    )

    with pytest.raises(PeerReviewBlockedError, match="language metadata"):
        review_manuscript(handle_unsupported, invoker=_FakeSkillInvoker())


# @id TEST-AISCI-014
# @verifies REQ-AISCI-014
def test_TEST_AISCI_014_delegates_presentation_to_presentation_planner(tmp_path, monkeypatch):
    handle = _resolve_handle(tmp_path, monkeypatch, "presentation-study")
    _seed_research_evidence(handle)
    invoker = _FakeSkillInvoker()

    from ai_scientist.manuscript import write_manuscript
    from ai_scientist.presentation import build_presentation

    manuscript = write_manuscript(handle, "Write the manuscript in English.", invoker=invoker)
    presentation = build_presentation(handle, invoker=invoker)

    assert manuscript["artifact"]["path"] in invoker.calls[-1][3]["manuscriptPath"]
    assert invoker.calls[-1][0:3] == ("presentation-planner", "0.3.0", "plan")
    assert len(invoker.calls[-1][3]["evidenceManifest"]) == 5
    assert presentation["artifact"]["phase"] == "presentation"


# @id TEST-AISCI-030
# @verifies REQ-AISCI-014
def test_TEST_AISCI_030_blocks_presentation_until_a_manuscript_exists(tmp_path, monkeypatch):
    handle = _resolve_handle(tmp_path, monkeypatch, "presentation-blocked")
    _seed_research_evidence(handle)

    from ai_scientist.evidence_registry import query_evidence
    from ai_scientist.presentation import build_presentation

    with pytest.raises(ValueError, match="manuscript"):
        build_presentation(handle, invoker=_FakeSkillInvoker())

    assert query_evidence(handle, "presentation") == []


# @id TEST-AISCI-021
# @verifies REQ-AISCI-021
def test_TEST_AISCI_021_produces_configured_markdown_or_latex_manuscript(tmp_path, monkeypatch):
    handle_default = _resolve_handle(tmp_path, monkeypatch, "format-default")
    _seed_research_evidence(handle_default)
    invoker = _FakeSkillInvoker()

    from ai_scientist.manuscript import write_manuscript
    from ai_scientist.project_config import save_project_config

    default_result = write_manuscript(
        handle_default, "Write the manuscript in English.", invoker=invoker
    )
    assert default_result["artifact"]["path"].endswith(".md")

    handle_latex = _resolve_handle(tmp_path, monkeypatch, "format-latex")
    _seed_research_evidence(handle_latex)
    save_project_config(handle_latex, {"manuscriptFormat": "latex"})
    latex_result = write_manuscript(
        handle_latex, "Write the manuscript in English.", invoker=invoker
    )
    assert latex_result["artifact"]["path"].endswith(".tex")


# @id TEST-AISCI-022
# @verifies REQ-AISCI-022
def test_TEST_AISCI_022_renders_latex_from_tech_writer_markdown_sections(tmp_path, monkeypatch):
    handle = _resolve_handle(tmp_path, monkeypatch, "latex-study")
    _seed_research_evidence(handle)
    invoker = _FakeSkillInvoker()

    from ai_scientist.manuscript import write_manuscript
    from ai_scientist.project_config import save_project_config

    save_project_config(handle, {"manuscriptFormat": "latex"})
    result = write_manuscript(handle, "Write the manuscript in English.", invoker=invoker)

    content = Path(result["artifact"]["path"]).read_text(encoding="utf-8")
    assert "\\documentclass" in content
    assert "\\begin{document}" in content
    assert "\\section{Title}" in content
    assert "\\subsection{Abstract}" in content
    assert "A summary." in content
    assert "\\subsection{Results}" in content
    assert "Strong findings." in content


# @id TEST-AISCI-034
# @verifies REQ-AISCI-022
def test_TEST_AISCI_034_escapes_reserved_characters_in_rendered_latex(tmp_path):
    markdown = tmp_path / "draft.md"
    markdown.write_text(
        "# Results & Discussion\n\nConfidence is 95%_sure in {trial}.\n",
        encoding="utf-8",
    )

    from ai_scientist.latex_renderer import render_latex

    content = render_latex(markdown)

    assert r"\section{Results \& Discussion}" in content
    assert r"Confidence is 95\%\_sure in \{trial\}." in content
