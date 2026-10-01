"""Tests for mcp_runtime: Jupyter MCP runtime lifecycle manager."""

from __future__ import annotations

import pytest

from ai_data_scientist.mcp_gateway import MCPUnavailableError
from ai_data_scientist.mcp_runtime import RuntimeInfo, ensure_runtime, status, stop


class _FakeLauncher:
    """In-memory RuntimeLauncher fake: no real process is ever started."""

    def __init__(self, healthy: bool = True):
        self.healthy = healthy
        self.started_jupyter = 0
        self.started_mcp_server = 0
        self.terminated: list[int] = []
        self._next_pid = 1000
        self._alive_after_terminate: set[int] = set()

    def start_jupyter(self) -> tuple[int, int, str]:
        self.started_jupyter += 1
        self._next_pid += 1
        return self._next_pid, 19000, "jupyter-tok"

    def start_mcp_server(self, jupyter_port: int, jupyter_token: str) -> tuple[int, int, str]:
        self.started_mcp_server += 1
        self._next_pid += 1
        return self._next_pid, 19001, "mcp-tok"

    def is_healthy(self, info: RuntimeInfo) -> bool:
        return self.healthy

    def terminate(self, pid: int) -> None:
        self.terminated.append(pid)

    def is_process_alive(self, pid: int) -> bool:
        return pid in self._alive_after_terminate


# @id TEST-AIDS-040
# @verifies REQ-AIDS-034
def test_TEST_AIDS_040_ensure_runtime_starts_localhost_runtime_with_random_token(tmp_path):
    state_path = tmp_path / "mcp_runtime.json"
    launcher = _FakeLauncher(healthy=True)

    info = ensure_runtime(launcher, state_path=state_path, timeout_ms=1000)

    assert launcher.started_jupyter == 1
    assert launcher.started_mcp_server == 1
    assert 0 < info.mcp_port < 65536
    assert isinstance(info.mcp_token, str) and len(info.mcp_token) > 0
    assert state_path.exists()


# @id TEST-AIDS-041
# @verifies REQ-AIDS-035
def test_TEST_AIDS_041_ensure_runtime_reuses_existing_healthy_runtime(tmp_path):
    state_path = tmp_path / "mcp_runtime.json"
    launcher = _FakeLauncher(healthy=True)

    first = ensure_runtime(launcher, state_path=state_path, timeout_ms=1000)
    second = ensure_runtime(launcher, state_path=state_path, timeout_ms=1000)

    assert second == first
    assert launcher.started_jupyter == 1
    assert launcher.started_mcp_server == 1


# @id TEST-AIDS-042
# @verifies REQ-AIDS-036
def test_TEST_AIDS_042_ensure_runtime_raises_on_startup_timeout(tmp_path):
    state_path = tmp_path / "mcp_runtime.json"
    launcher = _FakeLauncher(healthy=False)

    with pytest.raises(MCPUnavailableError):
        ensure_runtime(launcher, state_path=state_path, timeout_ms=50)

    assert not state_path.exists()
    assert len(launcher.terminated) == 2


# @id TEST-AIDS-043
# @verifies REQ-AIDS-037
def test_TEST_AIDS_043_status_and_stop_control_the_runtime(tmp_path):
    state_path = tmp_path / "mcp_runtime.json"
    launcher = _FakeLauncher(healthy=True)

    assert status(launcher, state_path=state_path) is None

    info = ensure_runtime(launcher, state_path=state_path, timeout_ms=1000)
    assert status(launcher, state_path=state_path) == info

    stop(launcher, state_path=state_path)

    assert status(launcher, state_path=state_path) is None
    assert not state_path.exists()
    assert set(launcher.terminated) == {info.jupyter_pid, info.mcp_server_pid}


# @id TEST-AIDS-050
# @verifies REQ-AIDS-041
def test_TEST_AIDS_050_stop_wait_blocks_until_processes_exit(tmp_path):
    state_path = tmp_path / "mcp_runtime.json"
    launcher = _FakeLauncher(healthy=True)
    info = ensure_runtime(launcher, state_path=state_path, timeout_ms=1000)

    result = stop(launcher, state_path=state_path, wait=True, timeout_s=1.0, poll_interval_s=0.01)

    assert result.still_running == ()
    assert set(launcher.terminated) == {info.jupyter_pid, info.mcp_server_pid}


# @id TEST-AIDS-051
# @verifies REQ-AIDS-041
def test_TEST_AIDS_051_stop_wait_reports_still_running_after_timeout(tmp_path):
    state_path = tmp_path / "mcp_runtime.json"
    launcher = _FakeLauncher(healthy=True)
    info = ensure_runtime(launcher, state_path=state_path, timeout_ms=1000)
    launcher._alive_after_terminate = {info.jupyter_pid, info.mcp_server_pid}

    result = stop(launcher, state_path=state_path, wait=True, timeout_s=0.1, poll_interval_s=0.02)

    assert set(result.still_running) == {info.jupyter_pid, info.mcp_server_pid}
