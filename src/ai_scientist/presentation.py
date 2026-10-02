"""Presentation-planner delegation."""

from __future__ import annotations

from datetime import datetime, timezone

from ai_scientist.evidence_registry import latest_evidence, query_evidence, record_evidence
from ai_scientist.project_handle import ResearchProjectHandle
from ai_scientist.skill_invocation import SkillInvoker

PRESENTATION_DEPENDENCY = {"skillId": "presentation-planner", "version": "0.3.0"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# @id CODE-AISCI-013
# @implements REQ-AISCI-014
# @design DES-AISCI-009
def build_presentation(handle: ResearchProjectHandle, invoker: SkillInvoker) -> dict:
    """Delegate presentation planning and record the resulting outline."""
    manuscript = latest_evidence(handle, "manuscript-writing")
    if manuscript is None:
        raise ValueError("A manuscript artifact is required before the presentation phase.")
    evidence_manifest = [
        {
            "phase": record.phase,
            "artifactPath": record.artifact_path,
            "artifactKind": record.artifact_kind,
            "createdAt": record.created_at,
            "metadata": record.metadata,
        }
        for record in query_evidence(handle)
        if record.phase != "presentation"
    ]
    response = invoker.invoke(
        PRESENTATION_DEPENDENCY["skillId"],
        PRESENTATION_DEPENDENCY["version"],
        "plan",
        {
            "manuscriptPath": manuscript.artifact_path if manuscript is not None else "",
            "evidenceManifest": evidence_manifest,
        },
    )
    artifact = handle.presentation_dir / "presentation-plan.md"
    artifact.write_text(response["content"], encoding="utf-8")
    record = record_evidence(handle, "presentation", artifact, "markdown", _now())
    return {
        "phase": "presentation",
        "artifact": {
            "phase": record.phase,
            "path": record.artifact_path,
            "metadata": record.metadata,
        },
    }
