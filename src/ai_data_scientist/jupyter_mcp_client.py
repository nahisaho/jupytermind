"""Concrete Jupyter MCP client implementation.

Implements DES-AIDS-026: satisfies the mcp_gateway.MCPClient contract by
communicating with the jupyter-mcp-server runtime started by mcp_runtime, so
run_and_record can execute real code against a live Jupyter kernel without
any caller-supplied client (REQ-AIDS-038).
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from ai_data_scientist.mcp_gateway import MCPUnavailableError
from ai_data_scientist.mcp_runtime import (
    DEFAULT_STATE_PATH,
    DEFAULT_STARTUP_TIMEOUT_MS,
    RuntimeInfo,
    ensure_runtime,
)


class _Transport(Protocol):
    def __call__(self, port: int, token: str, code: str) -> dict: ...


# @id CODE-AIDS-042
# @implements REQ-AIDS-038
# @design DES-AIDS-026
class JupyterMCPClient:
    """MCPClient implementation backed by a running jupyter-mcp-server.

    ``transport`` is injected (rather than hard-coding an HTTP/stdio library
    call) so this class is unit-testable without a real jupyter-mcp-server,
    mirroring the Protocol-based testability used elsewhere in this codebase.
    Transport-level connection failures are reclassified as the same
    MCPUnavailableError already defined by mcp_gateway (DES-AIDS-004), so
    callers never see transport-specific exceptions.
    """

    def __init__(self, runtime_info: RuntimeInfo, transport: _Transport) -> None:
        self._runtime_info = runtime_info
        self._transport = transport

    def execute(self, code: str) -> dict:
        try:
            return self._transport(self._runtime_info.port, self._runtime_info.token, code)
        except OSError as exc:
            raise MCPUnavailableError(
                "Jupyter MCP server connection failed (Jupyter MCPサーバーへの接続に失敗しました)."
            ) from exc


# @id CODE-AIDS-043
# @implements REQ-AIDS-038
# @design DES-AIDS-026
def default_client(
    launcher,
    transport: _Transport,
    timeout_ms: int = DEFAULT_STARTUP_TIMEOUT_MS,
    state_path: Path = DEFAULT_STATE_PATH,
) -> JupyterMCPClient:
    """Ensure a runtime is running and return a client wired to it.

    This is the factory mcp_gateway.run_and_record uses when no caller
    supplies an explicit MCPClient, fulfilling REQ-AIDS-038's acceptance
    criterion end-to-end.
    """
    runtime_info = ensure_runtime(launcher, state_path=state_path, timeout_ms=timeout_ms)
    return JupyterMCPClient(runtime_info, transport)
