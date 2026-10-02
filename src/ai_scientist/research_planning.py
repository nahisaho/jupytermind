"""Research planning phase handler."""

from __future__ import annotations

from datetime import datetime, timezone

from ai_scientist.evidence_registry import record_evidence
from ai_scientist.project_handle import ResearchProjectHandle


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def handle_research_planning(handle: ResearchProjectHandle, instruction: str) -> dict:
    """Create a planning artifact and record it as evidence."""
    artifact = handle.planning_dir / "research-plan.md"
    artifact.write_text(instruction, encoding="utf-8")
    record_evidence(handle, "research-planning", artifact, "markdown", _now())
    return {"phase": "research-planning", "artifact_path": str(artifact)}
