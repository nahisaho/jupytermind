"""Phase gate enforcement for ai_scientist."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from ai_scientist.phase_state import PHASE_ORDER, load_phase_state, record_override
from ai_scientist.project_handle import ResearchProjectHandle


@dataclass(frozen=True)
class GateDecision:
    """Outcome of a phase gate check."""

    allowed: bool
    message: str
    blocked_on: str | None = None
    override_applied: bool = False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# @id CODE-AISCI-006
# @implements REQ-AISCI-006
# @design DES-AISCI-004
# @id CODE-AISCI-008
# @implements REQ-AISCI-007
# @design DES-AISCI-004
def check_gate(
    handle: ResearchProjectHandle,
    requested_phase: str,
    override: dict[str, str] | None = None,
) -> GateDecision:
    """Allow only the active phase unless an explicit single-request override exists."""
    state = load_phase_state(handle)
    current = state.active_phase
    if requested_phase == current:
        return GateDecision(True, f"{requested_phase} is active and allowed.")

    predecessors = [
        phase
        for phase in PHASE_ORDER[: PHASE_ORDER.index(requested_phase)]
        if phase not in state.completed_phases
    ]
    if not predecessors:
        # requested_phase is an earlier phase whose own predecessors are all
        # complete (e.g. re-running an already-completed phase); there is no
        # incomplete predecessor to block on, so allow it without an override.
        return GateDecision(True, f"{requested_phase}'s predecessors are complete; allowed.")
    blocked_on = predecessors[0]

    if override is None:
        return GateDecision(
            allowed=False,
            blocked_on=blocked_on,
            message=f"Cannot run {requested_phase} because {blocked_on} is incomplete.",
        )

    record_override(
        handle,
        requested_phase=requested_phase,
        reason=override["reason"],
        incomplete_predecessors=predecessors,
        timestamp=_now(),
    )
    return GateDecision(
        allowed=True,
        blocked_on=None,
        override_applied=True,
        message=f"Override applied for {requested_phase}.",
    )
