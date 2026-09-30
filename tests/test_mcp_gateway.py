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


# @id TEST-AIDS-037
# @verifies REQ-AIDS-003
def test_TEST_AIDS_037_run_and_record_stamps_incrementing_execution_count(tmp_path):
    handle = resolve_project("execcount-project", projects_root=tmp_path)
    ensure_notebook(handle)
    client = _RecordingClient()

    first = run_and_record(client, handle, "1 + 1")
    second = run_and_record(client, handle, "2 + 2")

    assert first["execution_count"] == 1
    assert second["execution_count"] == 2

    notebook = nbformat.read(handle.notebook_path, as_version=4)
    assert notebook.cells[0]["execution_count"] == 1
    assert notebook.cells[1]["execution_count"] == 2
    assert notebook.cells[0]["outputs"][0]["execution_count"] == 1


# @id TEST-AIDS-038
# @verifies REQ-AIDS-009
def test_TEST_AIDS_038_run_and_record_execution_count_anchors_insight_evidence(tmp_path):
    from ai_data_scientist.insight_engine import record_insight

    handle = resolve_project("execcount-insight-project", projects_root=tmp_path)
    ensure_notebook(handle)
    client = _RecordingClient()

    outcome = run_and_record(client, handle, "correlation(df, 'a', 'b')")

    record_insight(
        handle,
        insight_text="a and b show a strong positive correlation.",
        evidence_execution_count=outcome["execution_count"],
        cited_value=outcome["output"],
        claim_type="correlation",
        language="en",
    )

    notebook = nbformat.read(handle.notebook_path, as_version=4)
    code_cell, insight_cell = notebook.cells
    assert code_cell["execution_count"] == outcome["execution_count"]
    assert code_cell["execution_count"] is not None
    assert insight_cell["cell_type"] == "markdown"
