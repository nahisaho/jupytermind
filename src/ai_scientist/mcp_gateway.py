"""MCP gateway that attributes calls to phases."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ai_scientist.mcp_failures import MCPUnavailableError, classify_mcp_failure


class McpClient(Protocol):
    """Minimal domain-tool client contract."""

    def call_tool(self, tool_name: str, args: dict) -> dict: ...


@dataclass
class McpGateway:
    """Route all ai_scientist external tool access through configured clients."""

    clients: dict[str, McpClient]

    # @id CODE-AISCI-015
    # @implements REQ-AISCI-015
    # @design DES-AISCI-010
    def call_tool(self, server_name: str, tool_name: str, args: dict, phase: str) -> dict:
        """Call one MCP tool via the configured client or raise a classified error."""
        try:
            client = self.clients[server_name]
        except KeyError as exc:
            raise classify_mcp_failure(server_name, phase, exc) from exc
        try:
            return client.call_tool(tool_name, args)
        except Exception as exc:  # noqa: BLE001 - classified into explicit domain error
            raise classify_mcp_failure(server_name, phase, exc) from exc


__all__ = ["McpGateway", "MCPUnavailableError"]
