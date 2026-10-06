"""Tests for scripts/release_gate_governance.py."""

from __future__ import annotations

import sys
from pathlib import Path

scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from release_gate_governance import (  # noqa: E402
    PERMANENTLY_EXCLUDED_WAIVER_SCOPES,
    assess_baseline_gate,
    prepare_workflow_handoff,
    record_live_session_limitation,
    summarize_status,
    verify_tdd_targets,
    waivers_needing_refresh,
)


# @id TEST-RELGATE-001
# @verifies REQ-RELGATE-001
def test_TEST_RELGATE_001_classifies_checks_and_preserves_real_statuses():
    gate_report = {
        "checks": [
            {"name": "tdd", "status": "pass"},
            {"name": "workflow", "status": "fail"},
            {"name": "performance", "status": "pass"},
        ]
    }
    baseline = assess_baseline_gate(gate_report)

    assert baseline["in_session_required"] == [
        "tdd",
        "change-history",
        "change-completeness",
        "performance",
        "commands",
    ]
    assert baseline["post_session_required"] == ["workflow"]
    assert baseline["approval_pending"] is True
    assert baseline["statuses"]["tdd"] == "pass"
    assert baseline["statuses"]["workflow"] == "fail"

    narrative = summarize_status(baseline)
    assert "tdd: pass (in-session)" in narrative
    assert "workflow: fail (post-session only)" in narrative


# @id TEST-RELGATE-002
# @verifies REQ-RELGATE-002
def test_TEST_RELGATE_002_excludes_permanently_stale_achem_scopes():
    diagnostics = [
        {
            "code": "CHANGE_WAIVER_STALE",
            "message": "Waiver for CHANGE-001:CHANGE_RED_UNPROVEN:REQ-AISCI-004 is stale.",
        },
        {
            "code": "CHANGE_WAIVER_STALE",
            "message": "Waiver for CHANGE-005:CHANGE_GREEN_UNPROVEN:REQ-ACHEM-003 is stale.",
        },
    ]
    scopes = waivers_needing_refresh(diagnostics)

    assert ("CHANGE-001", "CHANGE_RED_UNPROVEN", "REQ-AISCI-004") in scopes
    assert ("CHANGE-005", "CHANGE_GREEN_UNPROVEN", "REQ-ACHEM-003") not in scopes
    assert (
        "CHANGE-005",
        "CHANGE_GREEN_UNPROVEN",
        "REQ-ACHEM-003",
    ) in PERMANENTLY_EXCLUDED_WAIVER_SCOPES


# @id TEST-RELGATE-003
# @verifies REQ-RELGATE-003
def test_TEST_RELGATE_003_detects_covered_and_uncovered_targets():
    tdd_cycles = [
        {"testId": "TEST-AIMS-040", "red": {"valid": True}, "green": {"valid": True}},
        {"testId": "TEST-AIDS-021", "red": {"valid": True}, "green": {"valid": False}},
    ]
    covered = verify_tdd_targets(tdd_cycles)

    assert covered["TEST-AIMS-040"] is True
    assert covered["TEST-AIDS-021"] is False
    assert covered["TEST-AIDS-096"] is False


# @id TEST-RELGATE-005
# @verifies REQ-RELGATE-005
def test_TEST_RELGATE_005_prepares_handoff_and_limitation_note():
    handoff = prepare_workflow_handoff()

    assert handoff["requires_closed_transcript"] is True
    assert handoff["blocking_check"] == "workflow"
    assert handoff["follow_up_steps"] == [
        "workflow-sanitize",
        "workflow-verify",
        "workflow waiver record-all",
        "gate --json",
    ]

    note = record_live_session_limitation()
    assert "musubix3 issue #63" in note
    assert "workflow" in note
