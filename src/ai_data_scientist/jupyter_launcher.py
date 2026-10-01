"""Real Jupyter MCP runtime launcher.

Implements the production-grade RuntimeLauncher (DES-AIDS-025) backing
mcp_runtime.ensure_runtime: starts real JupyterLab and jupyter-mcp-server
processes inside the project's managed Python environment, bound to
127.0.0.1 with auto-selected free ports and random tokens, and health-checks
them over real HTTP. Verified interactively against a live jupyter-mcp-server
2.2.3 instance: JupyterLab requires ``--IdentityProvider.token``, and the
streamable-http transport requires its own ``--mcp-token`` (distinct from
JUPYTER_TOKEN) or it refuses to start.
"""

from __future__ import annotations

import os
import secrets
import signal
import socket
import subprocess
import sys
from pathlib import Path

import httpx

from ai_data_scientist.mcp_runtime import RuntimeInfo

_HEALTH_CHECK_TIMEOUT_S = 2.0


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _venv_executable(name: str) -> str:
    """Resolve ``name`` next to the current Python interpreter's venv bin dir."""
    candidate = Path(sys.executable).parent / name
    return str(candidate) if candidate.exists() else name


# @id CODE-AIDS-044
# @implements REQ-AIDS-034, REQ-AIDS-038
# @design DES-AIDS-025
class JupyterLabMCPServerLauncher:
    """Starts real JupyterLab + jupyter-mcp-server subprocesses.

    Satisfies the mcp_runtime.RuntimeLauncher Protocol with the real process
    and HTTP transport details confirmed by interactive verification against
    jupyter-mcp-server 2.2.3's streamable-http transport.
    """

    def __init__(self, working_dir: Path | None = None) -> None:
        self._working_dir = working_dir or Path.cwd()

    def start_jupyter(self) -> tuple[int, int, str]:
        port = _pick_free_port()
        token = secrets.token_urlsafe(32)
        process = subprocess.Popen(
            [
                _venv_executable("jupyter-lab"),
                f"--port={port}",
                f"--IdentityProvider.token={token}",
                "--ip=127.0.0.1",
                "--no-browser",
                f"--ServerApp.root_dir={self._working_dir}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return process.pid, port, token

    def start_mcp_server(self, jupyter_port: int, jupyter_token: str) -> tuple[int, int, str]:
        port = _pick_free_port()
        token = secrets.token_urlsafe(32)
        env = {
            "JUPYTER_URL": f"http://127.0.0.1:{jupyter_port}",
            "JUPYTER_TOKEN": jupyter_token,
        }
        process = subprocess.Popen(
            [
                _venv_executable("jupyter-mcp-server"),
                "start",
                "--transport=streamable-http",
                f"--port={port}",
                "--host=127.0.0.1",
                f"--mcp-token={token}",
            ],
            env={**os.environ, **env},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return process.pid, port, token

    def is_healthy(self, info: RuntimeInfo) -> bool:
        try:
            response = httpx.post(
                f"http://127.0.0.1:{info.mcp_port}/mcp",
                headers={
                    "Authorization": f"Bearer {info.mcp_token}",
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
                json={
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "ai-data-scientist", "version": "0.1"},
                    },
                },
                timeout=_HEALTH_CHECK_TIMEOUT_S,
            )
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    def terminate(self, pid: int) -> None:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
