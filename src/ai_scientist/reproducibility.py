"""Reproducibility check phase handler."""

from __future__ import annotations

from datetime import datetime, timezone

from ai_scientist.evidence_registry import record_evidence
from ai_scientist.project_handle import ResearchProjectHandle


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def handle_reproducibility_check(handle: ResearchProjectHandle, instruction: str) -> dict:
    """Create a reproducibility artifact and record it."""
    artifact = handle.reproducibility_dir / "reproducibility-check.md"
    artifact.write_text(instruction, encoding="utf-8")
    record_evidence(handle, "reproducibility-check", artifact, "markdown", _now())
    return {"phase": "reproducibility-check", "artifact_path": str(artifact)}
