"""Evidence-based completion validation."""

from ai_scientist.evidence_registry import query_evidence
from ai_scientist.project_handle import ResearchProjectHandle


# @id CODE-AISCI-021
# @implements REQ-AISCI-020
# @design DES-AISCI-017
def validate_completion_evidence(handle: ResearchProjectHandle, phase: str) -> bool:
    """Require at least one correctly attributed evidence record for ``phase``."""
    return any(
        record.project == handle.name and record.phase == phase and bool(record.created_at)
        for record in query_evidence(handle, phase)
    )
