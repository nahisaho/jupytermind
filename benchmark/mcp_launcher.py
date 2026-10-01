#!/usr/bin/env python3
"""Start an isolated JupyterLab and expose it through Jupyter MCP over stdio."""

from __future__ import annotations

import argparse
import os
import secrets
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPOSITORY = Path(__file__).resolve().parents[1]
VENV_BIN = REPOSITORY / ".venv" / "bin"
JUPYTER = VENV_BIN / "jupyter"
MCP_SERVER = VENV_BIN / "jupyter-mcp-server"


def pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def server_is_ready(url: str, token: str) -> bool:
    request = Request(
        f"{url}/api/status",
        headers={"Authorization": f"token {token}"},
    )
    try:
        with urlopen(request, timeout=1) as response:
            return response.status == 200
    except (HTTPError, URLError, TimeoutError, OSError):
        return False


def stop_process(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()

    if not JUPYTER.is_file() or not MCP_SERVER.is_file():
        raise RuntimeError("Run `npx ai-data-scientist doctor` before the benchmark.")

    workspace = args.workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    args.log.parent.mkdir(parents=True, exist_ok=True)
    port = pick_free_port()
    token = secrets.token_urlsafe(32)
    jupyter_url = f"http://127.0.0.1:{port}"
    jupyter_process = None
    mcp_process = None

    def handle_shutdown(_signum: int, _frame: object) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    try:
        with args.log.open("w", encoding="utf-8") as log_file:
            jupyter_process = subprocess.Popen(
                [
                    str(JUPYTER),
                    "lab",
                    f"--port={port}",
                    f"--IdentityProvider.token={token}",
                    "--ip=127.0.0.1",
                    "--no-browser",
                    f"--ServerApp.root_dir={workspace}",
                ],
                cwd=workspace,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )

        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            if server_is_ready(jupyter_url, token):
                break
            if jupyter_process.poll() is not None:
                raise RuntimeError(f"Jupyter failed to start; inspect {args.log}.")
            time.sleep(0.5)
        else:
            raise RuntimeError(f"Jupyter did not become ready; inspect {args.log}.")

        environment = {
            **os.environ,
            "PATH": f"{VENV_BIN}{os.pathsep}{os.environ.get('PATH', '')}",
            "JUPYTER_URL": jupyter_url,
            "JUPYTER_TOKEN": token,
            "ALLOW_IMG_OUTPUT": "true",
        }
        mcp_process = subprocess.Popen(
            [str(MCP_SERVER)],
            cwd=workspace,
            env=environment,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        return mcp_process.wait()
    except KeyboardInterrupt:
        return 0
    finally:
        stop_process(mcp_process)
        stop_process(jupyter_process)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Jupyter MCP launcher: {error}", file=sys.stderr)
        raise SystemExit(1)
