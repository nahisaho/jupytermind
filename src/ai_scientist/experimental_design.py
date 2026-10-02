"""Experimental design phase handler."""

from __future__ import annotations

from datetime import datetime, timezone

from ai_scientist.evidence_registry import record_evidence
from ai_scientist.project_handle import ResearchProjectHandle


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def handle_experimental_design(handle: ResearchProjectHandle, instruction: str) -> dict:
    """Create an experimental design artifact and record it."""
    artifact = handle.design_dir / "experimental-design.md"
    artifact.write_text(instruction, encoding="utf-8")
    record_evidence(handle, "experimental-design", artifact, "markdown", _now())
    return {"phase": "experimental-design", "artifact_path": str(artifact)}
