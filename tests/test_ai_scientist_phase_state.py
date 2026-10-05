"""Tests for ai_scientist lifecycle state, gate, and evidence completion."""

from __future__ import annotations

import importlib
import threading
from datetime import datetime, timezone

import pytest


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_handle(tmp_path, monkeypatch, project_name: str = "study-1"):
    monkeypatch.setenv("AI_DATA_SCIENTIST_PROJECTS_ROOT", str(tmp_path / "projects"))
    from ai_scientist.project_handle import resolve_research_project

    return resolve_research_project(project_name)


def _phase_artifact_path(handle, phase: str):
    directories = {
        "research-planning": handle.planning_dir,
        "literature-review": handle.literature_dir,
        "experimental-design": handle.design_dir,
        "data-analysis": handle.root / "notebooks",
        "manuscript-writing": handle.manuscript_dir,
        "peer-review": handle.review_dir,
        "reproducibility-check": handle.reproducibility_dir,
        "presentation": handle.presentation_dir,
    }
    directory = directories[phase]
    suffix = ".ipynb" if phase == "data-analysis" else ".md"
    return directory / f"{phase}{suffix}"


# @id TEST-AISCI-004
# @verifies REQ-AISCI-004
def test_TEST_AISCI_004_persists_eight_phase_state_across_invocations(tmp_path, monkeypatch):
    handle = _resolve_handle(tmp_path, monkeypatch)

    from ai_scientist.evidence_registry import record_evidence
    from ai_scientist.phase_state import PHASE_ORDER, load_phase_state, mark_phase_complete

    initial = load_phase_state(handle)
    assert initial.active_phase == "research-planning"
    assert initial.completed_phases == []
    assert initial.incomplete_phases == list(PHASE_ORDER[1:])

    for phase in PHASE_ORDER[:3]:
        artifact = _phase_artifact_path(handle, phase)
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(phase, encoding="utf-8")
        record_evidence(handle, phase, artifact, "note", _timestamp())
        mark_phase_complete(handle, phase)

    phase_state_module = importlib.import_module("ai_scientist.phase_state")
    importlib.reload(phase_state_module)
    persisted = phase_state_module.load_phase_state(handle)

    assert persisted.completed_phases == list(PHASE_ORDER[:3])
    assert persisted.active_phase == "data-analysis"


# @id TEST-AISCI-005
# @verifies REQ-AISCI-005
def test_TEST_AISCI_005_advances_only_to_the_next_phase_and_stops_after_final(
    tmp_path, monkeypatch
):
    handle = _resolve_handle(tmp_path, monkeypatch, "study-2")

    from ai_scientist.evidence_registry import record_evidence
    from ai_scientist.phase_state import PHASE_ORDER, load_phase_state, mark_phase_complete

    first_artifact = handle.planning_dir / "plan.md"
    first_artifact.write_text("plan", encoding="utf-8")
    record_evidence(handle, "research-planning", first_artifact, "plan", _timestamp())
    after_first = mark_phase_complete(handle, "research-planning")
    assert after_first.active_phase == "literature-review"

    for phase in PHASE_ORDER[1:]:
        artifact = _phase_artifact_path(handle, phase)
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("{}" if artifact.suffix == ".ipynb" else phase, encoding="utf-8")
        artifact_kind = "notebook" if artifact.suffix == ".ipynb" else "artifact"
        record_evidence(handle, phase, artifact, artifact_kind, _timestamp())
        final_state = mark_phase_complete(handle, phase)

    assert final_state.active_phase is None
    assert final_state.completed_phases == list(PHASE_ORDER)
    assert load_phase_state(handle).active_phase is None


# @id TEST-AISCI-006
# @verifies REQ-AISCI-006
def test_TEST_AISCI_006_blocks_out_of_order_phase_requests_with_named_predecessor(
    tmp_path, monkeypatch
):
    handle = _resolve_handle(tmp_path, monkeypatch, "study-3")

    from ai_scientist.evidence_registry import record_evidence
    from ai_scientist.phase_gate import check_gate
    from ai_scientist.phase_state import mark_phase_complete

    artifact = handle.planning_dir / "plan.md"
    artifact.write_text("plan", encoding="utf-8")
    record_evidence(handle, "research-planning", artifact, "plan", _timestamp())
    mark_phase_complete(handle, "research-planning")

    decision = check_gate(handle, "experimental-design")

    assert decision.allowed is False
    assert decision.blocked_on == "literature-review"
    assert "literature-review" in decision.message


# @id TEST-AISCI-025
# @verifies REQ-AISCI-006
def test_TEST_AISCI_025_rerunning_a_completed_earlier_phase_is_allowed_without_override(
    tmp_path, monkeypatch
):
    handle = _resolve_handle(tmp_path, monkeypatch, "study-3b")

    from ai_scientist.evidence_registry import record_evidence
    from ai_scientist.phase_gate import check_gate
    from ai_scientist.phase_state import mark_phase_complete

    for phase in ("research-planning", "literature-review"):
        artifact = _phase_artifact_path(handle, phase)
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(phase, encoding="utf-8")
        record_evidence(handle, phase, artifact, "note", _timestamp())
        mark_phase_complete(handle, phase)

    # Active phase is now experimental-design; requesting the already-completed
    # research-planning must not be blocked by blaming the later active phase.
    decision = check_gate(handle, "research-planning")

    assert decision.allowed is True
    assert decision.blocked_on is None


# @id TEST-AISCI-026
# @verifies REQ-AISCI-004
def test_TEST_AISCI_026_mark_phase_complete_rejects_a_non_active_phase(tmp_path, monkeypatch):
    handle = _resolve_handle(tmp_path, monkeypatch, "study-1b")

    from ai_scientist.evidence_registry import record_evidence
    from ai_scientist.phase_state import mark_phase_complete

    artifact = _phase_artifact_path(handle, "experimental-design")
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("design", encoding="utf-8")
    record_evidence(handle, "experimental-design", artifact, "note", _timestamp())

    with pytest.raises(ValueError):
        mark_phase_complete(handle, "experimental-design")


# @id TEST-AISCI-027
# @verifies REQ-AISCI-004
def test_TEST_AISCI_027_mark_phase_complete_rejects_an_unknown_phase_name(tmp_path, monkeypatch):
    handle = _resolve_handle(tmp_path, monkeypatch, "study-1c")

    from ai_scientist.phase_state import mark_phase_complete

    with pytest.raises(ValueError, match="Unknown phase"):
        mark_phase_complete(handle, "not-a-real-phase")


# @id TEST-AISCI-007
# @verifies REQ-AISCI-007
def test_TEST_AISCI_007_override_executes_once_without_mutating_phase_state(tmp_path, monkeypatch):
    handle = _resolve_handle(tmp_path, monkeypatch, "study-4")

    from ai_scientist.evidence_registry import record_evidence
    from ai_scientist.phase_gate import check_gate
    from ai_scientist.phase_state import (
        active_phase,
        list_overrides,
        load_phase_state,
        mark_phase_complete,
    )

    artifact = handle.planning_dir / "plan.md"
    artifact.write_text("plan", encoding="utf-8")
    record_evidence(handle, "research-planning", artifact, "plan", _timestamp())
    mark_phase_complete(handle, "research-planning")

    decision = check_gate(
        handle,
        "experimental-design",
        override={"reason": "Need to draft methods early."},
    )

    assert decision.allowed is True
    assert decision.override_applied is True
    assert active_phase(handle) == "literature-review"
    assert load_phase_state(handle).completed_phases == ["research-planning"]

    overrides = list_overrides(handle)
    assert len(overrides) == 1
    assert overrides[0].requested_phase == "experimental-design"
    assert overrides[0].reason == "Need to draft methods early."
    assert overrides[0].incomplete_predecessors == ["literature-review"]

    follow_up = check_gate(handle, "literature-review")
    assert follow_up.allowed is True


# @id TEST-AISCI-020
# @verifies REQ-AISCI-020
def test_TEST_AISCI_020_requires_phase_attributed_evidence_before_completion(tmp_path, monkeypatch):
    handle = _resolve_handle(tmp_path, monkeypatch, "study-5")

    from ai_scientist.evidence_registry import record_evidence
    from ai_scientist.phase_state import mark_phase_complete

    with pytest.raises(ValueError):
        mark_phase_complete(handle, "research-planning")

    wrong = handle.design_dir / "design.md"
    wrong.write_text("design", encoding="utf-8")
    record_evidence(handle, "experimental-design", wrong, "design", _timestamp())
    with pytest.raises(ValueError):
        mark_phase_complete(handle, "research-planning")

    correct = handle.planning_dir / "plan.md"
    correct.write_text("plan", encoding="utf-8")
    record_evidence(handle, "research-planning", correct, "plan", _timestamp())

    state = mark_phase_complete(handle, "research-planning")
    assert state.active_phase == "literature-review"


# @id TEST-AISCI-041
# @verifies REQ-AISCI-004
def test_TEST_AISCI_041_concurrent_completion_and_override_do_not_clobber_each_other(
    tmp_path, monkeypatch
):
    """DES-AISCI-003: the read-modify-write cycle must be safe across separate
    invocations. A phase completion and an override request racing on the same
    project's state file must both be preserved, not last-writer-wins.

    Regression test for jupytermind#64; closed by CHANGE-019 (ADR-0075)."""
    handle = _resolve_handle(tmp_path, monkeypatch, "study-concurrency")

    from ai_scientist.evidence_registry import record_evidence
    from ai_scientist import phase_state

    first = _phase_artifact_path(handle, "research-planning")
    first.parent.mkdir(parents=True, exist_ok=True)
    first.write_text("plan", encoding="utf-8")
    record_evidence(handle, "research-planning", first, "plan", _timestamp())
    phase_state.mark_phase_complete(handle, "research-planning")

    second = _phase_artifact_path(handle, "literature-review")
    second.parent.mkdir(parents=True, exist_ok=True)
    second.write_text("lit", encoding="utf-8")
    record_evidence(handle, "literature-review", second, "note", _timestamp())

    # Force both concurrent callers' reads to interleave: each rendezvous at
    # this barrier right after reading state but before writing it back. If
    # the read-modify-write cycle is properly serialized, only one caller can
    # ever be between its read and write at a time, so the other never
    # reaches the barrier in time and the wait simply times out alone for
    # each of them in turn. If the cycle is NOT serialized, both callers
    # reach the barrier together (a true rendezvous), proving they read the
    # same stale state concurrently -- which reproduces last-writer-wins.
    barrier = threading.Barrier(2)
    rendezvoused = threading.Event()

    def hook():
        try:
            barrier.wait(timeout=0.3)
            rendezvoused.set()
        except threading.BrokenBarrierError:
            pass

    monkeypatch.setattr(phase_state, "_after_locked_read_hook", hook)

    def complete_phase():
        phase_state.mark_phase_complete(handle, "literature-review")

    def record_an_override():
        phase_state.record_override(
            handle,
            "manuscript-writing",
            "Need an early draft before reproducibility-check.",
            ["experimental-design"],
            _timestamp(),
        )

    t_complete = threading.Thread(target=complete_phase)
    t_override = threading.Thread(target=record_an_override)
    t_complete.start()
    t_override.start()
    t_complete.join()
    t_override.join()

    assert rendezvoused.is_set() is False, (
        "both callers read state concurrently without serialization -- the "
        "read-modify-write cycle is not safe across concurrent invocations"
    )

    final = phase_state.load_phase_state(handle)
    assert final.active_phase == "experimental-design"
    assert final.completed_phases == ["research-planning", "literature-review"]
    assert len(final.overrides) == 1
    assert final.overrides[0].requested_phase == "manuscript-writing"
