"""Tests for jupyter_mcp_client: concrete MCPClient implementation."""

from __future__ import annotations

import pytest

from ai_data_scientist.jupyter_mcp_client import JupyterMCPClient, default_client
from ai_data_scientist.mcp_gateway import MCPUnavailableError, run_and_record
from ai_data_scientist.mcp_runtime import RuntimeInfo
from ai_data_scientist.project_manager import ensure_notebook, resolve_project


class _FakeLauncher:
    def start_jupyter(self) -> tuple[int, int, str]:
        return 1001, 19000, "jupyter-tok"

    def start_mcp_server(self, jupyter_port: int, jupyter_token: str) -> tuple[int, int, str]:
        return 1002, 19001, "mcp-tok"

    def is_healthy(self, info: RuntimeInfo) -> bool:
        return True

    def terminate(self, pid: int) -> None:
        pass


def _fake_transport(port: int, token: str, code: str) -> dict:
    return {"status": "ok", "output": str(eval(code))}


def _failing_transport(port: int, token: str, code: str) -> dict:
    raise ConnectionRefusedError("no server listening")


# @id TEST-AIDS-044
# @verifies REQ-AIDS-038
def test_TEST_AIDS_044_jupyter_mcp_client_executes_via_transport_and_reclassifies_errors():
    info = RuntimeInfo(
        jupyter_pid=1,
        jupyter_port=19000,
        jupyter_token="jupyter-tok",
        mcp_server_pid=2,
        mcp_port=12345,
        mcp_token="tok",
    )

    ok_client = JupyterMCPClient(info, _fake_transport)
    assert ok_client.execute("1 + 1") == {"status": "ok", "output": "2"}

    failing_client = JupyterMCPClient(info, _failing_transport)
    with pytest.raises(MCPUnavailableError):
        failing_client.execute("1 + 1")


# @id TEST-AIDS-045
# @verifies REQ-AIDS-038
def test_TEST_AIDS_045_run_and_record_executes_via_default_client_without_custom_client(
    tmp_path,
):
    handle = resolve_project("default-client-project", projects_root=tmp_path)
    ensure_notebook(handle)

    state_path = tmp_path / "mcp_runtime.json"
    client = default_client(
        _FakeLauncher(), _fake_transport, timeout_ms=1000, state_path=state_path
    )
    result = run_and_record(client, handle, "2 + 2")

    assert result["output"] == "4"
    assert result["execution_count"] == 1
