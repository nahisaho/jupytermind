"""Jupyter MCP execution gateway.

Implements DES-AIDS-004: routes all analysis code execution exclusively
through the configured Jupyter MCP client, enforces execution timeouts,
and classifies unavailability/timeout failures so no partial cell is ever
persisted to the notebook.
"""

from __future__ import annotations

import concurrent.futures
from typing import Protocol

import nbformat

from ai_data_scientist.project_manager import ProjectHandle, enqueue_write

DEFAULT_TIMEOUT_MS = 30000


class MCPUnavailableError(RuntimeError):
    """The configured Jupyter MCP server or kernel could not be reached."""


class MCPExecutionTimeoutError(RuntimeError):
    """Execution did not complete within the configured timeout."""


class MCPClient(Protocol):
    """Minimal contract any Jupyter MCP transport must satisfy."""

    def execute(self, code: str) -> dict: ...


# @id CODE-AIDS-003
# @implements REQ-AIDS-003
# @design DES-AIDS-004
# @id CODE-AIDS-031
# @implements REQ-AIDS-031
# @design DES-AIDS-004
def execute_cell(client: MCPClient, code: str, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> dict:
    """Execute ``code`` exclusively through ``client`` with a hard timeout.

    Raises ``MCPExecutionTimeoutError`` if execution exceeds ``timeout_ms``
    and ``MCPUnavailableError`` if the client cannot reach the MCP server
    or kernel.
    """
    timeout_s = timeout_ms / 1000
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(client.execute, code)
        try:
            return future.result(timeout=timeout_s)
        except concurrent.futures.TimeoutError as exc:
            raise MCPExecutionTimeoutError(
                f"Execution exceeded the configured {timeout_ms}ms timeout "
                f"(実行が設定タイムアウト{timeout_ms}msを超えました)."
            ) from exc
        except ConnectionError as exc:
            raise MCPUnavailableError(
                "The configured Jupyter MCP server or kernel is unreachable "
                "(設定されたJupyter MCPサーバー/カーネルに接続できません)."
            ) from exc


# @id CODE-AIDS-030
# @implements REQ-AIDS-030
# @design DES-AIDS-004
def run_and_record(
    client: MCPClient,
    handle: ProjectHandle,
    code: str,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
) -> dict:
    """Execute ``code`` and, only on success, append a cell to the notebook.

    On failure the classified error propagates and no cell is written,
    satisfying REQ-AIDS-030 (unavailability) and REQ-AIDS-031 (timeout).
    """
    result = execute_cell(client, code, timeout_ms=timeout_ms)

    def add_cell(nb):
        cell = nbformat.v4.new_code_cell(code)
        cell["outputs"] = [
            nbformat.v4.new_output(
                "execute_result", data={"text/plain": str(result.get("output", ""))}
            )
        ]
        nb.cells.append(cell)

    enqueue_write(handle, add_cell)
    return result
