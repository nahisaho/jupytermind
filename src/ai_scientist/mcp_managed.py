"""Managed MCP process lifecycle for ai_scientist."""

from __future__ import annotations

import ipaddress
import shlex
import socket
import subprocess
import threading
import time
from dataclasses import dataclass
from urllib import error, request
from urllib.parse import urlparse

from ai_scientist.mcp_config import ManagedServerConfig
from ai_scientist.mcp_failures import classify_mcp_failure


@dataclass(frozen=True)
class RuntimeInfo:
    """Runtime identity for one managed MCP server."""

    pid: int
    port: int
    endpoint: str


_RUNTIMES: dict[str, tuple[subprocess.Popen, RuntimeInfo, str]] = {}

# Per-server-name locks, guarded by a single registry lock so lock creation
# itself cannot race. Mirrors the ai_data_scientist project_manager per-path
# lock pattern, but here the lock additionally protects the entire
# check-then-start critical section in ensure_managed_server, so two
# concurrent first-use callers for the same server name cannot both observe
# "no running process" and both start a second process.
_runtime_locks: dict[str, threading.Lock] = {}
_runtime_locks_guard = threading.Lock()


def _lock_for(name: str) -> threading.Lock:
    with _runtime_locks_guard:
        lock = _runtime_locks.get(name)
        if lock is None:
            lock = threading.Lock()
            _runtime_locks[name] = lock
        return lock


def _is_loopback_host(hostname: str | None) -> bool:
    """True when ``hostname`` is a loopback address, or a name (such as
    ``localhost``) that resolves only to loopback addresses. Resolving
    rather than string-matching ``localhost`` prevents a host/DNS override
    that maps it to a non-loopback address from bypassing the check.
    A name with no resolvable addresses is rejected, not treated as safe."""
    if hostname is None:
        return False
    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        pass
    try:
        resolved = socket.getaddrinfo(hostname, None)
    except OSError:
        return False
    return bool(resolved) and all(ipaddress.ip_address(info[4][0]).is_loopback for info in resolved)


def _require_loopback_endpoint(entry: ManagedServerConfig) -> None:
    """Reject a non-loopback ``endpointTemplate`` host before any port is
    allocated or process started (DES-AISCI-012: "must bind only to
    127.0.0.1"). Closes jupytermind#66 / CHANGE-019 (ADR-0084); see
    TEST-AISCI-042.
    """
    sample_endpoint = entry.endpoint_template.format(port=0)
    hostname = urlparse(sample_endpoint).hostname
    if not _is_loopback_host(hostname):
        raise classify_mcp_failure(
            entry.name,
            "managed-startup",
            f"endpointTemplate host {hostname!r} is not loopback; "
            "managed servers must bind only to 127.0.0.1",
        )


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
    _require_loopback_endpoint(entry)
    with _lock_for(entry.name):
        existing = _RUNTIMES.get(entry.name)
        if existing is not None:
            process, info, health_check_path = existing
            if process.poll() is None and _healthy(info.endpoint, health_check_path):
                return info
            _stop_locked(entry.name)

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
            # Check our own child is still alive *before* trusting a health
            # response: an external process that stole the allocated port
            # could otherwise answer the health probe on behalf of our dead
            # child process and get cached as a legitimate managed runtime.
            if process.poll() is not None:
                break
            if _healthy(endpoint, entry.health_check_path):
                _RUNTIMES[entry.name] = (process, info, entry.health_check_path)
                return info
            time.sleep(0.1)
        _stop_process(process)
        raise classify_mcp_failure(entry.name, phase, "startup timeout")


def status(server_name: str) -> RuntimeInfo | None:
    """Return current runtime info when the managed server is still running."""
    with _lock_for(server_name):
        existing = _RUNTIMES.get(server_name)
        if existing is None:
            return None
        process, info, health_check_path = existing
        if process.poll() is None and _healthy(info.endpoint, health_check_path):
            return info
        _stop_locked(server_name)
        return None


def stop(server_name: str) -> None:
    """Terminate only the registered managed server for ``server_name``."""
    with _lock_for(server_name):
        _stop_locked(server_name)


def _stop_locked(server_name: str) -> None:
    """Terminate the registered server; caller must already hold its lock."""
    existing = _RUNTIMES.pop(server_name, None)
    if existing is None:
        return
    process, _info, _health_check_path = existing
    _stop_process(process)
