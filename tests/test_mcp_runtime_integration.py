"""Real end-to-end integration test for the Jupyter MCP runtime adapters.

Unlike test_mcp_runtime.py/test_jupyter_mcp_client.py (fully fake-backed,
fast), this test exercises the genuine JupyterLabMCPServerLauncher and the
real mcp_transport.execute_code against a real, locally started JupyterLab +
jupyter-mcp-server process pair. It is slow (process startup) and is skipped
automatically when the optional jupyterlab/jupyter-mcp-server executables are
not installed in the current environment.
"""

from __future__ import annotations

import shutil

import pytest

from ai_data_scientist.jupyter_launcher import JupyterLabMCPServerLauncher
from ai_data_scientist.jupyter_mcp_client import default_client
from ai_data_scientist.mcp_runtime import stop
from ai_data_scientist.mcp_transport import execute_code

_REQUIRED_EXECUTABLES = ("jupyter-lab", "jupyter-mcp-server")

pytestmark = pytest.mark.skipif(
    not all(shutil.which(exe) for exe in _REQUIRED_EXECUTABLES),
    reason="real jupyterlab/jupyter-mcp-server executables are not installed",
)


# @id TEST-AIDS-046
# @verifies REQ-AIDS-034, REQ-AIDS-038
def test_TEST_AIDS_046_real_launcher_and_transport_execute_code_end_to_end(tmp_path):
    state_path = tmp_path / "mcp_runtime.json"
    launcher = JupyterLabMCPServerLauncher(working_dir=tmp_path)
    try:
        client = default_client(launcher, execute_code, timeout_ms=60000, state_path=state_path)

        result = client.execute("21 * 2")

        assert result["status"] == "ok"
        assert result["output"] == "42"
    finally:
        stop(launcher, state_path=state_path)
