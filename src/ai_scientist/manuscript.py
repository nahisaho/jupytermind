"""Manuscript-writing delegation and final rendering."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ai_scientist.evidence_registry import query_evidence, record_evidence
from ai_scientist.language import detect_language
from ai_scientist.latex_renderer import render_latex
from ai_scientist.project_config import load_project_config
from ai_scientist.project_handle import ResearchProjectHandle
from ai_scientist.skill_invocation import SkillInvoker

TECH_WRITER_DEPENDENCY = {"skillId": "tech-writer", "version": "0.3.0"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _research_evidence_manifest(handle: ResearchProjectHandle) -> list[dict]:
    return [
        {
            "project": record.project,
            "phase": record.phase,
            "artifactPath": record.artifact_path,
            "artifactKind": record.artifact_kind,
            "createdAt": record.created_at,
            "metadata": record.metadata,
        }
        for record in query_evidence(handle)
        if record.phase
        in {"research-planning", "literature-review", "experimental-design", "data-analysis"}
    ]


def _write_markdown_artifact(handle: ResearchProjectHandle, content: str) -> Path:
    path = handle.manuscript_dir / "manuscript.md"
    path.write_text(content, encoding="utf-8")
    return path


# @id CODE-AISCI-010
# @implements REQ-AISCI-009
# @design DES-AISCI-006
# @id CODE-AISCI-011
# @implements REQ-AISCI-010
# @design DES-AISCI-007
# @id CODE-AISCI-022
# @implements REQ-AISCI-021, REQ-AISCI-022
# @design DES-AISCI-018
def write_manuscript(
    handle: ResearchProjectHandle, instruction: str, invoker: SkillInvoker
) -> dict:
    """Delegate manuscript drafting to tech-writer and render final format."""
    evidence_manifest = _research_evidence_manifest(handle)
    payload = {
        "project": {"name": handle.name, "root": str(handle.root)},
        "instruction": instruction,
        "evidenceManifest": evidence_manifest,
    }
    response = invoker.invoke(
        TECH_WRITER_DEPENDENCY["skillId"],
        TECH_WRITER_DEPENDENCY["version"],
        "write",
        payload,
    )
    markdown_path = _write_markdown_artifact(handle, response["content"])
    language = detect_language(instruction)
    config = load_project_config(handle)
    manuscript_format = config.get("manuscriptFormat", "markdown")
    final_path = markdown_path
    artifact_kind = "markdown"
    if manuscript_format == "latex":
        final_path = handle.manuscript_dir / "manuscript.tex"
        final_path.write_text(render_latex(markdown_path), encoding="utf-8")
        artifact_kind = "latex"
    record = record_evidence(
        handle,
        "manuscript-writing",
        final_path,
        artifact_kind,
        _now(),
        metadata={"language": language, "sourceMarkdownPath": str(markdown_path)},
    )
    return {
        "phase": "manuscript-writing",
        "artifact": {
            "phase": record.phase,
            "path": record.artifact_path,
            "metadata": record.metadata,
        },
    }
