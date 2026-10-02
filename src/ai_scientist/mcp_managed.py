"""Managed MCP process lifecycle for ai_scientist."""

from __future__ import annotations

import shlex
import socket
import subprocess
import time
from dataclasses import dataclass
from urllib import error, request

from ai_scientist.mcp_config import ManagedServerConfig
from ai_scientist.mcp_failures import classify_mcp_failure


@dataclass(frozen=True)
class RuntimeInfo:
    """Runtime identity for one managed MCP server."""

    pid: int
    port: int
    endpoint: str


_RUNTIMES: dict[str, tuple[subprocess.Popen, RuntimeInfo, str]] = {}


def _allocate_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _healthy(endpoint: str, health_check_path: str) -> bool:
    try:
        with request.urlopen(f"{endpoint}{health_check_path}", timeout=1) as response:
            return response.status == 200
    except (error.URLError, TimeoutError):
        return False


def _stop_process(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)


# @id CODE-AISCI-017
# @implements REQ-AISCI-017
# @design DES-AISCI-012
# @id CODE-AISCI-027
# @implements REQ-AISCI-019
# @design DES-AISCI-014
def ensure_managed_server(
    entry: ManagedServerConfig,
    timeout_ms: int = 30000,
    phase: str = "managed-startup",
) -> RuntimeInfo:
    """Start a managed server on first use and reuse it for the session."""
    existing = _RUNTIMES.get(entry.name)
    if existing is not None:
        process, info, health_check_path = existing
        if process.poll() is None and _healthy(info.endpoint, health_check_path):
            return info
        stop(entry.name)

    port = _allocate_port()
    endpoint = entry.endpoint_template.format(port=port)
    command = shlex.split(entry.launch_command.format(port=port))
    process = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    info = RuntimeInfo(pid=process.pid, port=port, endpoint=endpoint)
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if _healthy(endpoint, entry.health_check_path):
            _RUNTIMES[entry.name] = (process, info, entry.health_check_path)
            return info
        if process.poll() is not None:
            break
        time.sleep(0.1)
    _stop_process(process)
    raise classify_mcp_failure(entry.name, phase, "startup timeout")


def status(server_name: str) -> RuntimeInfo | None:
    """Return current runtime info when the managed server is still running."""
    existing = _RUNTIMES.get(server_name)
    if existing is None:
        return None
    process, info, health_check_path = existing
    if process.poll() is None and _healthy(info.endpoint, health_check_path):
        return info
    stop(server_name)
    return None


def stop(server_name: str) -> None:
    """Terminate only the registered managed server for ``server_name``."""
    existing = _RUNTIMES.pop(server_name, None)
    if existing is None:
        return
    process, _info, _health_check_path = existing
    _stop_process(process)
