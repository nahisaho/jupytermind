"""External MCP endpoint connector."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import error, request

from ai_scientist.mcp_config import ExternalServerConfig


@dataclass(frozen=True)
class HttpMcpClient:
    """Simple HTTP MCP client used by the tests and local runtime glue."""

    endpoint: str

    def call_tool(self, tool_name: str, args: dict) -> dict:
        payload = json.dumps({"tool": tool_name, "args": args}).encode("utf-8")
        req = request.Request(
            url=f"{self.endpoint.rstrip('/')}/tool",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=3) as response:
                return json.loads(response.read().decode("utf-8"))
        except (error.URLError, ConnectionError, TimeoutError) as exc:
            raise ConnectionError(str(exc)) from exc


# @id CODE-AISCI-018
# @implements REQ-AISCI-018
# @design DES-AISCI-013
def connect_external_server(entry: ExternalServerConfig) -> HttpMcpClient:
    """Return a client without managing any process lifecycle."""
    if not isinstance(entry, ExternalServerConfig):
        raise ValueError(
            f"connect_external_server requires an external-mode config entry, got {entry!r}"
        )
    return HttpMcpClient(entry.endpoint)
