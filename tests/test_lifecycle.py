"""Tests for the run lifecycle API (REQ-AIDS-051)."""

import threading
import time

import pytest

from ai_data_scientist import lifecycle


@pytest.fixture(autouse=True)
def _clean_registry():
    yield
    lifecycle._registry.clear()


# @id TEST-AIDS-074
# @verifies REQ-AIDS-051
def test_TEST_AIDS_074_tracked_activity_reported_until_settled(tmp_path):
    notebook_path = tmp_path / "proj.ipynb"
    lifecycle.register_run("run-1", notebook_path)
    lifecycle.mark_execution_start("run-1")
    lifecycle.mark_write_start("run-1")

    status = lifecycle.get_run_status("run-1")
    assert status.active_cell_executions >= 1
    assert status.pending_notebook_writes >= 1

    lifecycle.mark_execution_end("run-1")
    lifecycle.mark_write_end("run-1")
    lifecycle.mark_completed("run-1")

    settled = lifecycle.wait_for_quiescence("run-1", timeout_s=5)
    assert settled.active_cell_executions == 0
    assert settled.pending_notebook_writes == 0
    assert settled.locks_held == 0


# @id TEST-AIDS-075
# @verifies REQ-AIDS-051
def test_TEST_AIDS_075_cancel_is_idempotent_and_safe_on_completed_run(tmp_path):
    notebook_path = tmp_path / "proj.ipynb"
    lifecycle.register_run("run-2", notebook_path)
    lifecycle.mark_completed("run-2")

    # Cancelling an already-completed run must not raise, and must not
    # corrupt its completed state.
    lifecycle.request_cancel("run-2", reason="orchestrator timeout")
    lifecycle.request_cancel("run-2", reason="orchestrator timeout")

    status = lifecycle.get_run_status("run-2")
    assert status.state == "completed"


# @id TEST-AIDS-076
# @verifies REQ-AIDS-051
def test_TEST_AIDS_076_cancel_unknown_run_does_not_raise():
    lifecycle.request_cancel("does-not-exist", reason="noop")


# @id TEST-AIDS-077
# @verifies REQ-AIDS-051
def test_TEST_AIDS_077_second_run_reuses_notebook_after_first_reaches_quiescence(tmp_path):
    notebook_path = tmp_path / "shared.ipynb"
    lifecycle.register_run("run-a", notebook_path)
    lock = threading.Lock()
    from ai_data_scientist import project_manager

    project_manager._write_locks[notebook_path] = lock

    lock.acquire()
    lifecycle.mark_write_start("run-a")
    status = lifecycle.get_run_status("run-a")
    assert status.locks_held == 1

    def _release_soon():
        time.sleep(0.05)
        lifecycle.mark_write_end("run-a")
        lock.release()

    threading.Thread(target=_release_soon).start()
    settled = lifecycle.wait_for_quiescence("run-a", timeout_s=5)
    assert settled.locks_held == 0
    lifecycle.mark_completed("run-a")

    # A second run on the same notebook path registers and completes
    # cleanly, without any lock-acquisition error.
    lifecycle.register_run("run-b", notebook_path)
    lifecycle.mark_completed("run-b")
    assert lifecycle.get_run_status("run-b").state == "completed"


# @id TEST-AIDS-078
# @verifies REQ-AIDS-051
def test_TEST_AIDS_078_quiescence_times_out_when_execution_never_ends(tmp_path):
    notebook_path = tmp_path / "stuck.ipynb"
    lifecycle.register_run("run-stuck", notebook_path)
    lifecycle.mark_execution_start("run-stuck")

    status = lifecycle.wait_for_quiescence("run-stuck", timeout_s=0.1)
    assert status.active_cell_executions == 1
