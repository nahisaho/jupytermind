"""Tests for the Jupyter MCP execution gateway (REQ-AIDS-003/030/031)."""

import time

import nbformat
import pytest

from ai_data_scientist.mcp_gateway import (
    MCPExecutionTimeoutError,
    MCPUnavailableError,
    execute_cell,
    run_and_record,
)
from ai_data_scientist.project_manager import ensure_notebook, resolve_project


class _RecordingClient:
    """Fake MCP client that records that execution went through it."""

    def __init__(self):
        self.calls = []

    def execute(self, code):
        self.calls.append(code)
        return {"status": "ok", "output": f"executed: {code}"}


class _UnavailableClient:
    def execute(self, code):
        raise ConnectionError("kernel unreachable")


class _SlowClient:
    def execute(self, code):
        time.sleep(0.5)
        return {"status": "ok", "output": "too slow"}


# @id TEST-AIDS-003
# @verifies REQ-AIDS-003
def test_TEST_AIDS_003():
    client = _RecordingClient()
    result = execute_cell(client, "1 + 1")
    assert client.calls == ["1 + 1"]
    assert result["status"] == "ok"


# @id TEST-AIDS-030
# @verifies REQ-AIDS-030
def test_TEST_AIDS_030(tmp_path):
    handle = resolve_project("mcp-down-project", projects_root=tmp_path)
    ensure_notebook(handle)
    before = len(nbformat.read(handle.notebook_path, as_version=4).cells)

    client = _UnavailableClient()
    with pytest.raises(MCPUnavailableError):
        run_and_record(client, handle, "1 + 1")

    after = len(nbformat.read(handle.notebook_path, as_version=4).cells)
    assert after == before


# @id TEST-AIDS-031
# @verifies REQ-AIDS-031
def test_TEST_AIDS_031(tmp_path):
    handle = resolve_project("timeout-project", projects_root=tmp_path)
    ensure_notebook(handle)
    before = len(nbformat.read(handle.notebook_path, as_version=4).cells)

    client = _SlowClient()
    with pytest.raises(MCPExecutionTimeoutError):
        run_and_record(client, handle, "1 + 1", timeout_ms=50)

    after = len(nbformat.read(handle.notebook_path, as_version=4).cells)
    assert after == before
