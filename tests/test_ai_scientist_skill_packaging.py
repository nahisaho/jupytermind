"""Tests for ai_scientist packaging, manifest verification, and orchestration."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest


def _resolve_root(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_DATA_SCIENTIST_PROJECTS_ROOT", str(tmp_path / "projects"))
    return tmp_path / "projects"


class _RecordingMcpClient:
    def execute(self, code: str) -> dict:
        return {"status": "ok", "output": f"executed: {code}"}

    def call_tool(self, tool_name: str, args: dict) -> dict:
        return {"content": f"tool:{tool_name}", "args": args}


class _FakeSkillInvoker:
    def invoke(self, skill_id: str, version: str, mode: str, payload: dict) -> dict:
        if skill_id == "tech-writer":
            return {"content": "# Title\n\n## Summary\nDraft."}
        if skill_id == "presentation-planner":
            return {"content": "Presentation brief"}
        return {"content": "査読コメント"}


def _contains_japanese(text: str) -> bool:
    return re.search(r"[\u3040-\u30ff\u3400-\u9fff\uff66-\uff9f]", text) is not None


def _load_package_files() -> list[str]:
    return json.loads(Path("package.json").read_text("utf-8"))["files"]


def _load_npm_pack_dry_run_paths() -> set[str]:
    result = subprocess.run(
        ["npm", "pack", "--dry-run", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    return {entry["path"] for pack in payload for entry in pack["files"]}


# @id TEST-AISCI-001
# @verifies REQ-AISCI-001
def test_TEST_AISCI_001_dispatch_responds_in_same_language_across_phases(tmp_path, monkeypatch):
    _resolve_root(tmp_path, monkeypatch)

    from ai_scientist.orchestrator import dispatch

    prompts = [
        ("研究計画を作ってください。", "research-planning", "ja"),
        ("Create a research plan.", "research-planning", "en"),
        ("文献を調べてください。", "literature-review", "ja"),
        ("Search the literature.", "literature-review", "en"),
        ("実験設計をまとめて。", "experimental-design", "ja"),
        ("Draft the experimental design.", "experimental-design", "en"),
        ("このデータを分析してください。", "data-analysis", "ja"),
        ("Analyze this dataset.", "data-analysis", "en"),
        ("原稿を書いてください。", "manuscript-writing", "ja"),
        ("Write the manuscript.", "manuscript-writing", "en"),
    ]

    for index, (instruction, phase, expected_language) in enumerate(prompts):
        project_name = f"lang-project-{index}"
        result = dispatch(
            instruction,
            project_name=project_name,
            requested_phase=phase,
            override_reason="language check",
            skill_invoker=_FakeSkillInvoker(),
            mcp_client=_RecordingMcpClient(),
        )
        assert result["language"] == expected_language
        if expected_language == "ja":
            assert _contains_japanese(result["message"])
        else:
            assert not _contains_japanese(result["message"])


# @id TEST-AISCI-028
# @verifies REQ-AISCI-001
def test_TEST_AISCI_028_dispatch_parses_phase_from_instruction_before_responding(
    tmp_path, monkeypatch
):
    _resolve_root(tmp_path, monkeypatch)

    from ai_scientist.orchestrator import dispatch

    result = dispatch(
        "Search the literature for prior oncology studies.",
        project_name="phase-parse-study",
        override_reason="Need literature context before drafting the plan.",
        skill_invoker=_FakeSkillInvoker(),
        mcp_client=_RecordingMcpClient(),
    )

    assert result["language"] == "en"
    assert result["phase"] == "literature-review"
    assert result["result"]["artifact_path"].endswith("literature/literature-review.md")


# @id TEST-AISCI-023
# @verifies REQ-AISCI-023
def test_TEST_AISCI_023_loads_phase_manifest_and_verifies_repo_skill_registry():
    from ai_scientist.manifest import (
        DEFAULT_MANIFEST_PATH,
        load_phase_manifest,
        scan_repo_skill_registry,
        verify_manifest_against_registry,
    )

    manifest = load_phase_manifest(DEFAULT_MANIFEST_PATH)
    assert set(manifest) == {
        "research-planning",
        "literature-review",
        "experimental-design",
        "data-analysis",
        "manuscript-writing",
        "peer-review",
        "reproducibility-check",
        "presentation",
    }

    peer_review = manifest["peer-review"]["skillDependencies"]
    assert set(peer_review) == {"ja", "en"}
    assert peer_review["ja"] == {"skillId": "japanese-prose", "version": "0.3.0"}
    assert peer_review["en"] == {"skillId": "tech-writer", "version": "0.3.0"}

    registry = scan_repo_skill_registry()
    verify_manifest_against_registry(manifest, registry)


# @id TEST-AISCI-036
# @verifies REQ-AISCI-023
def test_TEST_AISCI_036_dispatch_uses_the_manifest_declared_phase_handler(tmp_path, monkeypatch):
    _resolve_root(tmp_path, monkeypatch)

    import ai_scientist.orchestrator as orchestrator
    from ai_scientist.manifest import load_phase_manifest

    manifest = load_phase_manifest()
    manifest["research-planning"] = {
        **manifest["research-planning"],
        "modulePath": "ai_scientist.literature_review",
        "functionName": "handle_literature_review",
    }
    monkeypatch.setattr(orchestrator, "load_phase_manifest", lambda: manifest)

    result = orchestrator.dispatch(
        "Create a research plan.",
        project_name="manifest-routing-study",
        requested_phase="research-planning",
        skill_invoker=_FakeSkillInvoker(),
    )

    assert result["phase"] == "research-planning"
    assert result["result"]["artifact_path"].endswith("literature/literature-review.md")


# @id TEST-AISCI-024
# @verifies REQ-AISCI-024
def test_TEST_AISCI_024_has_linked_tests_for_every_requirement_without_skips():
    requirements_path = Path(".musubix/features/ai-scientist/requirements.md")
    test_paths = sorted(Path("tests").glob("test_ai_scientist*.py"))

    requirement_ids = {
        match.group(1)
        for match in re.finditer(r"## (REQ-AISCI-\d{3})", requirements_path.read_text("utf-8"))
    }
    verifies = {}
    skipped_text = []
    for path in test_paths:
        text = path.read_text(encoding="utf-8")
        skipped_text.append(text)
        for match in re.finditer(r"# @verifies (REQ-AISCI-\d{3})", text):
            verifies.setdefault(match.group(1), set()).add(path.name)

    assert requirement_ids == {f"REQ-AISCI-{index:03d}" for index in range(1, 26)}
    assert requirement_ids.issubset(set(verifies))
    assert "test_TEST_AISCI_008_integration_delegates_data_analysis_to_ai_data_scientist" in (
        Path("tests/test_ai_scientist_delegation.py").read_text(encoding="utf-8")
    )
    assert all(
        re.search(r"^\s*@pytest\.mark\.skip", text, re.MULTILINE) is None for text in skipped_text
    )


# @id TEST-AISCI-048
# @verifies REQ-AISCI-025
def test_TEST_AISCI_048_npm_package_ships_skill_payloads_with_matching_python_sources():
    package_files = _load_package_files()

    assert ".github/skills/ai-scientist" in package_files
    assert "src/ai_scientist/**/*.py" in package_files

    for entry in package_files:
        match = re.fullmatch(r"\.github/skills/([^/]+)", entry)
        if match is None:
            continue
        package_dir = Path("src") / match.group(1).replace("-", "_")
        if not (package_dir / "__init__.py").exists():
            continue
        assert f"{package_dir.as_posix()}/**/*.py" in package_files

    packed_paths = _load_npm_pack_dry_run_paths()
    assert ".github/skills/ai-scientist/SKILL.md" in packed_paths
    assert ".github/skills/ai-scientist/manifest.json" in packed_paths

    source_paths = {path.as_posix() for path in Path("src/ai_scientist").rglob("*.py")}
    assert source_paths.issubset(packed_paths)
