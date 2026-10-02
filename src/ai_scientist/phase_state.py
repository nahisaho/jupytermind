"""Persistent phase state for ai_scientist projects."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from uuid import uuid4

from ai_scientist.completion_gate import validate_completion_evidence
from ai_scientist.project_handle import ResearchProjectHandle

PHASE_ORDER = (
    "research-planning",
    "literature-review",
    "experimental-design",
    "data-analysis",
    "manuscript-writing",
    "peer-review",
    "reproducibility-check",
    "presentation",
)
DEFAULT_STATE_PATH = ".ai_scientist_phase_state.json"


@dataclass(frozen=True)
class OverrideRecord:
    """A durable single-request override audit record."""

    request_id: str
    timestamp: str
    requested_phase: str
    reason: str
    incomplete_predecessors: list[str]


@dataclass(frozen=True)
class PhaseState:
    """Persisted lifecycle state."""

    active_phase: str | None
    completed_phases: list[str]
    incomplete_phases: list[str]
    overrides: list[OverrideRecord] = field(default_factory=list)


def _state_path(handle: ResearchProjectHandle) -> Path:
    return handle.root / DEFAULT_STATE_PATH


def _initial_state() -> PhaseState:
    return PhaseState(
        active_phase=PHASE_ORDER[0],
        completed_phases=[],
        incomplete_phases=list(PHASE_ORDER[1:]),
        overrides=[],
    )


def _read_state(handle: ResearchProjectHandle) -> PhaseState:
    path = _state_path(handle)
    if not path.exists():
        return _initial_state()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return PhaseState(
        active_phase=payload["active_phase"],
        completed_phases=payload["completed_phases"],
        incomplete_phases=payload["incomplete_phases"],
        overrides=[OverrideRecord(**item) for item in payload.get("overrides", [])],
    )


def _write_state(handle: ResearchProjectHandle, state: PhaseState) -> None:
    path = _state_path(handle)
    temp_path = path.with_suffix(".tmp")
    temp_path.write_text(
        json.dumps(
            {
                "active_phase": state.active_phase,
                "completed_phases": state.completed_phases,
                "incomplete_phases": state.incomplete_phases,
                "overrides": [asdict(record) for record in state.overrides],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    temp_path.replace(path)


# @id CODE-AISCI-004
# @implements REQ-AISCI-004
# @design DES-AISCI-003
def load_phase_state(handle: ResearchProjectHandle) -> PhaseState:
    """Load or initialize the project's phase state."""
    state = _read_state(handle)
    if not _state_path(handle).exists():
        _write_state(handle, state)
    return state


def active_phase(handle: ResearchProjectHandle) -> str | None:
    """Return the current active phase."""
    return load_phase_state(handle).active_phase


def _next_phase(phase: str) -> str | None:
    index = PHASE_ORDER.index(phase)
    if index + 1 >= len(PHASE_ORDER):
        return None
    return PHASE_ORDER[index + 1]


# @id CODE-AISCI-005
# @implements REQ-AISCI-005
# @design DES-AISCI-003
def mark_phase_complete(handle: ResearchProjectHandle, phase: str) -> PhaseState:
    """Mark ``phase`` complete when it is the active phase and matching evidence exists."""
    if phase not in PHASE_ORDER:
        raise ValueError(f"Unknown phase: {phase!r}.")
    state = load_phase_state(handle)
    if phase != state.active_phase:
        raise ValueError(
            f"Cannot complete {phase}: it is not the active phase ({state.active_phase})."
        )
    if not validate_completion_evidence(handle, phase):
        raise ValueError(f"Cannot complete {phase} without matching evidence.")
    completed = list(state.completed_phases)
    if phase not in completed:
        completed.append(phase)
    next_active = _next_phase(phase)
    incomplete = [item for item in PHASE_ORDER if item not in completed and item != next_active]
    updated = PhaseState(
        active_phase=next_active,
        completed_phases=completed,
        incomplete_phases=incomplete,
        overrides=state.overrides,
    )
    _write_state(handle, updated)
    return updated


# @id CODE-AISCI-007
# @implements REQ-AISCI-007
# @design DES-AISCI-004
def record_override(
    handle: ResearchProjectHandle,
    requested_phase: str,
    reason: str,
    incomplete_predecessors: list[str],
    timestamp: str,
) -> OverrideRecord:
    """Persist one override audit entry without mutating active phase."""
    state = load_phase_state(handle)
    record = OverrideRecord(
        request_id=str(uuid4()),
        timestamp=timestamp,
        requested_phase=requested_phase,
        reason=reason,
        incomplete_predecessors=incomplete_predecessors,
    )
    updated = PhaseState(
        active_phase=state.active_phase,
        completed_phases=state.completed_phases,
        incomplete_phases=state.incomplete_phases,
        overrides=[*state.overrides, record],
    )
    _write_state(handle, updated)
    return record


def list_overrides(handle: ResearchProjectHandle) -> list[OverrideRecord]:
    """Return persisted override audit records."""
    return load_phase_state(handle).overrides
