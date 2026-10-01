"""Cooperative run cancellation and quiescence lifecycle API.

Implements DES-AIDS-039 (REQ-AIDS-051): a process-wide, thread-safe
registry of run state that lets an external orchestrator request
cooperative cancellation of a tracked run and wait until all tracked
activity (cell executions, notebook writes, locks) has settled.

Cancellation is cooperative only: ``request_cancel`` sets a flag that
``is_cancel_requested`` exposes for callers (such as
``mcp_gateway.execute_cell``) to check *before* starting new work. It
cannot interrupt a kernel cell execution already in flight.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path

_VALID_STATES = frozenset({"running", "cancelling", "cancelled", "completed", "failed"})


@dataclass
class _RunRecord:
    notebook_path: Path
    state: str = "running"
    active_cell_executions: int = 0
    pending_notebook_writes: int = 0
    reason: str | None = None


@dataclass(frozen=True)
class RunStatus:
    """Immutable snapshot of a run's tracked lifecycle state."""

    run_id: str
    state: str
    active_cell_executions: int
    pending_notebook_writes: int
    locks_held: int
    notebook_path: str
    reason: str | None = None


class UnknownRunError(KeyError):
    """Raised when a run_id was never registered via register_run."""


_registry: dict[str, _RunRecord] = {}
_registry_guard = threading.Lock()
_QUIESCENCE_POLL_INTERVAL_S = 0.01


def _get_record(run_id: str) -> _RunRecord:
    with _registry_guard:
        record = _registry.get(run_id)
    if record is None:
        raise UnknownRunError(f"No run registered with run_id={run_id!r}.")
    return record


def _locks_held_for(notebook_path: Path) -> int:
    # project_manager keeps one threading.Lock per notebook path; a lock is
    # "held" iff it currently cannot be acquired without blocking.
    from ai_data_scientist import project_manager

    lock = project_manager._write_locks.get(notebook_path)
    if lock is None:
        return 0
    acquired = lock.acquire(blocking=False)
    if acquired:
        lock.release()
        return 0
    return 1


# @id CODE-AIDS-060
# @implements REQ-AIDS-051
# @design DES-AIDS-039
def register_run(run_id: str, notebook_path: Path | str) -> None:
    """Register a new tracked run in state "running"."""
    with _registry_guard:
        _registry[run_id] = _RunRecord(notebook_path=Path(notebook_path))


# @id CODE-AIDS-061
# @implements REQ-AIDS-051
# @design DES-AIDS-039
def mark_execution_start(run_id: str) -> None:
    """Record that a cell execution has begun for ``run_id``."""
    record = _get_record(run_id)
    with _registry_guard:
        record.active_cell_executions += 1


# @id CODE-AIDS-062
# @implements REQ-AIDS-051
# @design DES-AIDS-039
def mark_execution_end(run_id: str) -> None:
    """Record that a cell execution has finished for ``run_id``."""
    record = _get_record(run_id)
    with _registry_guard:
        record.active_cell_executions = max(0, record.active_cell_executions - 1)


# @id CODE-AIDS-063
# @implements REQ-AIDS-051
# @design DES-AIDS-039
def mark_write_start(run_id: str) -> None:
    """Record that a notebook write has begun for ``run_id``."""
    record = _get_record(run_id)
    with _registry_guard:
        record.pending_notebook_writes += 1


# @id CODE-AIDS-064
# @implements REQ-AIDS-051
# @design DES-AIDS-039
def mark_write_end(run_id: str) -> None:
    """Record that a notebook write has finished for ``run_id``."""
    record = _get_record(run_id)
    with _registry_guard:
        record.pending_notebook_writes = max(0, record.pending_notebook_writes - 1)


# @id CODE-AIDS-065
# @implements REQ-AIDS-051
# @design DES-AIDS-039
def request_cancel(run_id: str, reason: str | None = None) -> None:
    """Request cooperative cancellation of ``run_id``.

    Idempotent and safe to call on an unknown, already-cancelled, or
    already-completed/failed run_id: it never raises.
    """
    with _registry_guard:
        record = _registry.get(run_id)
        if record is None:
            return
        if record.state == "running":
            record.state = "cancelling"
        record.reason = reason


# @id CODE-AIDS-066
# @implements REQ-AIDS-051
# @design DES-AIDS-039
def is_cancel_requested(run_id: str) -> bool:
    """``True`` iff ``request_cancel`` has been called for ``run_id``."""
    record = _get_record(run_id)
    return record.state in ("cancelling", "cancelled")


def _finalize(run_id: str, state: str) -> None:
    record = _get_record(run_id)
    with _registry_guard:
        record.state = state


# @id CODE-AIDS-067
# @implements REQ-AIDS-051
# @design DES-AIDS-039
def mark_completed(run_id: str) -> None:
    """Mark ``run_id`` completed, unless it was already cancelling/cancelled."""
    record = _get_record(run_id)
    with _registry_guard:
        if record.state in ("cancelling", "cancelled"):
            record.state = "cancelled"
        else:
            record.state = "completed"


# @id CODE-AIDS-068
# @implements REQ-AIDS-051
# @design DES-AIDS-039
def mark_failed(run_id: str) -> None:
    """Mark ``run_id`` failed."""
    _finalize(run_id, "failed")


# @id CODE-AIDS-069
# @implements REQ-AIDS-051
# @design DES-AIDS-039
def get_run_status(run_id: str) -> RunStatus:
    """Return a snapshot of ``run_id``'s current tracked lifecycle state."""
    record = _get_record(run_id)
    with _registry_guard:
        return RunStatus(
            run_id=run_id,
            state=record.state,
            active_cell_executions=record.active_cell_executions,
            pending_notebook_writes=record.pending_notebook_writes,
            locks_held=_locks_held_for(record.notebook_path),
            notebook_path=str(record.notebook_path),
            reason=record.reason,
        )


# @id CODE-AIDS-070
# @implements REQ-AIDS-051
# @design DES-AIDS-039
def wait_for_quiescence(run_id: str, timeout_s: float = 30.0) -> RunStatus:
    """Poll ``run_id`` until all tracked activity settles or ``timeout_s`` elapses.

    Quiescent means ``active_cell_executions == 0``,
    ``pending_notebook_writes == 0`` and ``locks_held == 0``. Returns the
    last observed status either way (callers inspect the returned fields to
    tell quiescence from a timeout).
    """
    deadline = time.monotonic() + timeout_s
    status = get_run_status(run_id)
    while (
        status.active_cell_executions > 0
        or status.pending_notebook_writes > 0
        or status.locks_held > 0
    ):
        if time.monotonic() >= deadline:
            return status
        time.sleep(_QUIESCENCE_POLL_INTERVAL_S)
        status = get_run_status(run_id)
    return status
