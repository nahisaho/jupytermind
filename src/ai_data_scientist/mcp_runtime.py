"""Jupyter MCP runtime lifecycle manager.

Implements DES-AIDS-025: on the first execution request with no healthy
runtime registered, installs (if needed) and starts JupyterLab and the
jupyter-mcp-server inside the project's managed Python environment, bound to
127.0.0.1 with an automatically selected free port and a randomly generated
token, persists that runtime's identity to a machine-local state file so a
separate later invocation reuses it instead of starting a duplicate one, and
exposes explicit status/stop operations.
"""

from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path
from typing import Protocol

from ai_data_scientist.mcp_gateway import MCPUnavailableError

DEFAULT_STARTUP_TIMEOUT_MS = 30000
_HEALTH_POLL_INTERVAL_S = 0.2
DEFAULT_STATE_PATH = Path.home() / ".cache" / "ai-data-scientist" / "mcp_runtime.json"


@dataclasses.dataclass(frozen=True)
class RuntimeInfo:
    """Identity of a running Jupyter MCP runtime (REQ-AIDS-034).

    Two separate (port, token) pairs are tracked because JupyterLab and the
    jupyter-mcp-server (streamable-http transport) are independent processes
    with independent listeners and independent authentication: JUPYTER_TOKEN
    guards the Jupyter server itself, while the MCP token guards the MCP
    server's own HTTP endpoint that the concrete client (DES-AIDS-026) calls.
    """

    jupyter_pid: int
    jupyter_port: int
    jupyter_token: str
    mcp_server_pid: int
    mcp_port: int
    mcp_token: str


# @id CODE-AIDS-050
# @implements REQ-AIDS-041
# @design DES-AIDS-029
@dataclasses.dataclass(frozen=True)
class StopResult:
    """Outcome of a ``stop(..., wait=True)`` call (REQ-AIDS-041).

    ``still_running`` lists any recorded PIDs that were still alive when the
    bounded poll timed out; empty when every recorded process exited before
    the timeout.
    """

    still_running: tuple[int, ...]


class RuntimeLauncher(Protocol):
    """Process-management contract any Jupyter MCP runtime backend must satisfy.

    Kept as an injectable Protocol (mirroring mcp_gateway.MCPClient) so the
    lifecycle logic below is fully unit-testable without actually installing
    or starting JupyterLab/jupyter-mcp-server.
    """

    def start_jupyter(self) -> tuple[int, int, str]: ...
    def start_mcp_server(self, jupyter_port: int, jupyter_token: str) -> tuple[int, int, str]: ...
    def is_healthy(self, info: RuntimeInfo) -> bool: ...
    def terminate(self, pid: int) -> None: ...
    def is_process_alive(self, pid: int) -> bool: ...


def _read_state(state_path: Path) -> RuntimeInfo | None:
    if not state_path.exists():
        return None
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        return RuntimeInfo(**data)
    except (json.JSONDecodeError, TypeError, KeyError):
        return None


def _write_state(state_path: Path, info: RuntimeInfo) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(dataclasses.asdict(info)), encoding="utf-8")


def _clear_state(state_path: Path) -> None:
    state_path.unlink(missing_ok=True)


# @id CODE-AIDS-039
# @implements REQ-AIDS-034, REQ-AIDS-035, REQ-AIDS-036
# @design DES-AIDS-025
def ensure_runtime(
    launcher: RuntimeLauncher,
    state_path: Path = DEFAULT_STATE_PATH,
    timeout_ms: int = DEFAULT_STARTUP_TIMEOUT_MS,
) -> RuntimeInfo:
    """Return a healthy Jupyter MCP runtime, starting one only if needed.

    Reuses a still-running runtime recorded in ``state_path`` (REQ-AIDS-035).
    Otherwise starts a new localhost-only runtime with an auto-selected port
    and a random token (REQ-AIDS-034). Raises ``MCPUnavailableError`` without
    registering a partially started runtime if it does not become healthy
    within ``timeout_ms`` (REQ-AIDS-036).
    """
    existing = _read_state(state_path)
    if existing is not None and launcher.is_healthy(existing):
        return existing
    if existing is not None:
        _clear_state(state_path)

    jupyter_pid, jupyter_port, jupyter_token = launcher.start_jupyter()
    mcp_server_pid, mcp_port, mcp_token = launcher.start_mcp_server(jupyter_port, jupyter_token)
    candidate = RuntimeInfo(
        jupyter_pid=jupyter_pid,
        jupyter_port=jupyter_port,
        jupyter_token=jupyter_token,
        mcp_server_pid=mcp_server_pid,
        mcp_port=mcp_port,
        mcp_token=mcp_token,
    )

    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if launcher.is_healthy(candidate):
            _write_state(state_path, candidate)
            return candidate
        time.sleep(_HEALTH_POLL_INTERVAL_S)

    launcher.terminate(jupyter_pid)
    launcher.terminate(mcp_server_pid)
    raise MCPUnavailableError(
        "Jupyter MCP runtime did not become healthy within "
        f"{timeout_ms}ms (Jupyter MCPランタイムが{timeout_ms}ms以内に起動しませんでした)."
    )


# @id CODE-AIDS-040
# @implements REQ-AIDS-037
# @design DES-AIDS-025
def status(launcher: RuntimeLauncher, state_path: Path = DEFAULT_STATE_PATH) -> RuntimeInfo | None:
    """Return the currently running, healthy runtime, or None if none is running."""
    existing = _read_state(state_path)
    if existing is None:
        return None
    if launcher.is_healthy(existing):
        return existing
    _clear_state(state_path)
    return None


# @id CODE-AIDS-041
# @implements REQ-AIDS-037
# @design DES-AIDS-025
def stop(
    launcher: RuntimeLauncher,
    state_path: Path = DEFAULT_STATE_PATH,
    wait: bool = False,
    timeout_s: float = 5.0,
    poll_interval_s: float = 0.2,
) -> StopResult | None:
    """Terminate the recorded runtime's processes and clear the state file.

    With the default ``wait=False`` this is fire-and-forget (unchanged
    behavior): it sends SIGTERM and returns ``None`` immediately without
    confirming the processes actually exited. With ``wait=True``
    (REQ-AIDS-041), it polls ``launcher.is_process_alive`` for both recorded
    PIDs every ``poll_interval_s`` seconds until neither is alive or
    ``timeout_s`` elapses, then returns a ``StopResult`` recording any PIDs
    still alive at that point (empty when both exited cleanly).
    """
    existing = _read_state(state_path)
    if existing is None:
        return StopResult(still_running=()) if wait else None
    launcher.terminate(existing.jupyter_pid)
    launcher.terminate(existing.mcp_server_pid)
    _clear_state(state_path)

    if not wait:
        return None

    pids = [existing.jupyter_pid, existing.mcp_server_pid]
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        pids = [pid for pid in pids if launcher.is_process_alive(pid)]
        if not pids:
            break
        time.sleep(poll_interval_s)
    return StopResult(still_running=tuple(pids))
