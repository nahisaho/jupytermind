"""Peer-review routing based on persisted manuscript language metadata."""

from __future__ import annotations

from datetime import datetime, timezone

from ai_scientist.evidence_registry import latest_evidence, record_evidence
from ai_scientist.project_handle import ResearchProjectHandle
from ai_scientist.skill_invocation import SkillInvoker

PEER_REVIEW_DEPENDENCIES = {
    "ja": {"skillId": "japanese-prose", "version": "0.3.0"},
    "en": {"skillId": "tech-writer", "version": "0.3.0"},
}


class PeerReviewBlockedError(ValueError):
    """Peer review cannot proceed without supported manuscript language metadata."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# @id CODE-AISCI-012
# @implements REQ-AISCI-011, REQ-AISCI-012, REQ-AISCI-013
# @design DES-AISCI-008
def review_manuscript(handle: ResearchProjectHandle, invoker: SkillInvoker) -> dict:
    """Delegate peer review using the persisted manuscript language metadata."""
    manuscript = latest_evidence(handle, "manuscript-writing")
    language = manuscript.metadata.get("language") if manuscript is not None else None
    if language not in PEER_REVIEW_DEPENDENCIES:
        raise PeerReviewBlockedError(
            "Supported manuscript language metadata is required before peer-review."
        )
    dependency = PEER_REVIEW_DEPENDENCIES[language]
    response = invoker.invoke(
        dependency["skillId"],
        dependency["version"],
        "review",
        {"manuscriptPath": manuscript.artifact_path},
    )
    artifact = handle.review_dir / "peer-review.md"
    artifact.write_text(response["content"], encoding="utf-8")
    record = record_evidence(
        handle,
        "peer-review",
        artifact,
        "markdown",
        _now(),
        metadata={"language": language},
    )
    return {
        "phase": "peer-review",
        "artifact": {
            "phase": record.phase,
            "path": record.artifact_path,
            "metadata": record.metadata,
        },
    }
