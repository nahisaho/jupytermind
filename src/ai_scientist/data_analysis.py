"""Data-analysis delegation to ai-data-scientist."""

from __future__ import annotations

from datetime import datetime, timezone

import ai_data_scientist.project_manager as aids_project_manager
from ai_data_scientist.mcp_gateway import run_and_record

from ai_scientist.evidence_registry import record_evidence
from ai_scientist.project_handle import ResearchProjectHandle


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# @id CODE-AISCI-009
# @implements REQ-AISCI-008
# @design DES-AISCI-005
def delegate_data_analysis(
    handle: ResearchProjectHandle,
    instruction: str,
    mcp_client=None,
) -> dict:
    """Delegate notebook setup and optional execution to ai-data-scientist."""
    if mcp_client is None:
        raise ValueError("Data-analysis requires an MCP client for ai-data-scientist execution.")
    aids_handle = aids_project_manager.resolve_project(handle.name)
    if aids_handle.root != handle.root or aids_handle.notebook_path != handle.notebook_path:
        raise ValueError("ai-data-scientist handle diverged from ai-scientist project handle.")
    notebook_path = aids_project_manager.ensure_notebook(aids_handle)
    execution = run_and_record(mcp_client, aids_handle, instruction)
    record_evidence(
        handle,
        "data-analysis",
        notebook_path,
        "notebook",
        _now(),
        metadata={"executionRoutedVia": "ai_data_scientist.mcp_gateway"},
    )
    return {
        "phase": "data-analysis",
        "notebook_path": str(notebook_path),
        "execution": execution,
    }
