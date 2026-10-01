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
import secrets
import socket
import time
from pathlib import Path
from typing import Protocol

from ai_data_scientist.mcp_gateway import MCPUnavailableError

DEFAULT_STARTUP_TIMEOUT_MS = 30000
_HEALTH_POLL_INTERVAL_S = 0.2
DEFAULT_STATE_PATH = Path.home() / ".cache" / "ai-data-scientist" / "mcp_runtime.json"


@dataclasses.dataclass(frozen=True)
class RuntimeInfo:
    """Identity of a running Jupyter MCP runtime (REQ-AIDS-034)."""

    jupyter_pid: int
    mcp_server_pid: int
    port: int
    token: str


class RuntimeLauncher(Protocol):
    """Process-management contract any Jupyter MCP runtime backend must satisfy.

    Kept as an injectable Protocol (mirroring mcp_gateway.MCPClient) so the
    lifecycle logic below is fully unit-testable without actually installing
    or starting JupyterLab/jupyter-mcp-server.
    """

    def start_jupyter(self, port: int, token: str) -> int: ...
    def start_mcp_server(self, port: int, token: str) -> int: ...
    def is_healthy(self, info: RuntimeInfo) -> bool: ...
    def terminate(self, pid: int) -> None: ...


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


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

    port = _pick_free_port()
    token = secrets.token_urlsafe(32)
    jupyter_pid = launcher.start_jupyter(port, token)
    mcp_server_pid = launcher.start_mcp_server(port, token)
    candidate = RuntimeInfo(
        jupyter_pid=jupyter_pid, mcp_server_pid=mcp_server_pid, port=port, token=token
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
def stop(launcher: RuntimeLauncher, state_path: Path = DEFAULT_STATE_PATH) -> None:
    """Terminate the recorded runtime's processes and clear the state file."""
    existing = _read_state(state_path)
    if existing is None:
        return
    launcher.terminate(existing.jupyter_pid)
    launcher.terminate(existing.mcp_server_pid)
    _clear_state(state_path)
