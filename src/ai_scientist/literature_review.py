"""Literature review phase handler."""

from __future__ import annotations

from datetime import datetime, timezone

from ai_scientist.evidence_registry import record_evidence
from ai_scientist.mcp_gateway import McpGateway
from ai_scientist.project_handle import ResearchProjectHandle


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def handle_literature_review(
    handle: ResearchProjectHandle,
    instruction: str,
    gateway: McpGateway | None = None,
    server_name: str | None = None,
    tool_name: str = "literature-search",
    tool_args: dict | None = None,
) -> dict:
    """Write a literature artifact, routing external lookups only through MCP."""
    artifact = handle.literature_dir / "literature-review.md"
    content = instruction
    if gateway is not None and server_name is not None:
        tool_result = gateway.call_tool(
            server_name,
            tool_name,
            tool_args or {"query": instruction},
            phase="literature-review",
        )
        content = str(tool_result.get("content", ""))
    artifact.write_text(content, encoding="utf-8")
    record_evidence(handle, "literature-review", artifact, "markdown", _now())
    return {"phase": "literature-review", "artifact_path": str(artifact)}
