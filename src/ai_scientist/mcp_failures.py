"""Failure classification for ai_scientist MCP access."""

from __future__ import annotations


class MCPUnavailableError(RuntimeError):
    """MCP server unavailability with explicit server/phase attribution."""

    def __init__(self, server_name: str, phase: str, error: Exception | str):
        self.server_name = server_name
        self.phase = phase
        detail = str(error)
        super().__init__(f"MCP server '{server_name}' is unreachable for phase '{phase}': {detail}")


# @id CODE-AISCI-019
# @implements REQ-AISCI-019
# @design DES-AISCI-014
def classify_mcp_failure(
    server_name: str, phase: str, error: Exception | str
) -> MCPUnavailableError:
    """Build the classified error the caller must report."""
    return MCPUnavailableError(server_name, phase, error)
