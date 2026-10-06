"""CHANGE-025 release-gate governance support functions.

Implements the concrete interfaces declared by
``.musubix/features/release-gate-governance/design.md`` for
REQ-RELGATE-001, REQ-RELGATE-002, REQ-RELGATE-003, and REQ-RELGATE-005. Each
function operates on real, caller-supplied evidence (a parsed
``gate --json`` document, the parsed ``tdd.json`` evidence file, etc.) and
performs no fabrication: it only classifies/summarizes data that genuinely
exists.
"""

from __future__ import annotations

from typing import Any

# --- REQ-RELGATE-001 -------------------------------------------------------

#: Required checks this change can actively remediate within the live
#: Copilot session (see DES-RELGATE-001).
IN_SESSION_REQUIRED_CHECKS = (
    "tdd",
    "change-history",
    "change-completeness",
    "performance",
    "commands",
)

#: Required checks that can only be resolved after the session's transcript
#: closes (musubix3 issue #63 blocks `workflow-sanitize` on a live session).
POST_SESSION_REQUIRED_CHECKS = ("workflow",)


# @id CODE-RELGATE-001
# @implements REQ-RELGATE-001
# @design DES-RELGATE-001
def assess_baseline_gate(gate_report: dict[str, Any]) -> dict[str, Any]:
    """Classify each check in a parsed ``gate --json`` report as
    in-session-remediable, post-session-only, or neither, and return the
    per-check status alongside that classification.

    Never claims readiness stronger than what ``gate_report`` itself proves.
    """
    if not isinstance(gate_report, dict):
        raise TypeError("gate_report must be a parsed gate --json object.")
    checks = {
        (check.get("name") or check.get("id")): check.get("status")
        for check in gate_report.get("checks", [])
    }
    approval_status = checks.get("approval")
    return {
        "in_session_required": list(IN_SESSION_REQUIRED_CHECKS),
        "post_session_required": list(POST_SESSION_REQUIRED_CHECKS),
        "approval_pending": approval_status != "pass",
        "statuses": checks,
    }


# @id CODE-RELGATE-101
# @implements REQ-RELGATE-001
# @design DES-RELGATE-001
def summarize_status(baseline: dict[str, Any]) -> str:
    """Render a short, honest readiness narrative from an
    ``assess_baseline_gate`` result; never asserts `pass` for a check whose
    recorded status is not literally `pass`."""
    statuses = baseline.get("statuses", {})
    lines = []
    for name in baseline.get("in_session_required", []):
        lines.append(f"{name}: {statuses.get(name, 'unknown')} (in-session)")
    for name in baseline.get("post_session_required", []):
        lines.append(f"{name}: {statuses.get(name, 'unknown')} (post-session only)")
    return "; ".join(lines)


# --- REQ-RELGATE-002 --------------------------------------------------------

#: Scopes explicitly excluded from any waiver refresh attempt per
#: ADR-0110's accepted residual risk (CHANGE-005/upstream musubix3 #55).
PERMANENTLY_EXCLUDED_WAIVER_SCOPES = frozenset(
    {
        ("CHANGE-005", "CHANGE_GREEN_UNPROVEN", "REQ-ACHEM-003"),
        ("CHANGE-005", "CHANGE_GREEN_UNPROVEN", "REQ-ACHEM-010"),
        ("CHANGE-005", "CHANGE_GREEN_UNPROVEN", "REQ-ACHEM-020"),
        ("CHANGE-005", "CHANGE_GREEN_UNPROVEN", "REQ-ACHEM-050"),
    }
)


# @id CODE-RELGATE-002
# @implements REQ-RELGATE-002
# @design DES-RELGATE-002
def waivers_needing_refresh(diagnostics: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    """From a list of gate diagnostic dicts (each with ``code`` and
    ``message``), extract ``(changeId, code, requirementId)`` scopes for
    ``CHANGE_RED_UNPROVEN``/``CHANGE_GREEN_UNPROVEN``/``CHANGE_COMPLETENESS_TDD``
    diagnostics that currently fire, excluding the permanently-excluded
    CHANGE-005 scopes."""
    import re

    pattern = re.compile(
        r"(CHANGE-\d+):(CHANGE_RED_UNPROVEN|CHANGE_GREEN_UNPROVEN|CHANGE_COMPLETENESS_TDD):(REQ-[A-Z0-9-]+)"
    )
    scopes: list[tuple[str, str, str]] = []
    for diagnostic in diagnostics:
        match = pattern.search(diagnostic.get("message", ""))
        if not match:
            continue
        scope = (match.group(1), match.group(2), match.group(3))
        if scope in PERMANENTLY_EXCLUDED_WAIVER_SCOPES:
            continue
        if scope not in scopes:
            scopes.append(scope)
    return scopes


# --- REQ-RELGATE-003 ---------------------------------------------------------

#: The exact target matrix from DES-RELGATE-003: requirement -> the test
#: IDs that must have a valid, non-stale authoritative Red-Green cycle.
TDD_REGEN_TARGET_MATRIX: dict[str, tuple[str, ...]] = {
    "REQ-AIMS-040": ("TEST-AIMS-040",),
    "REQ-AIDS-021-REFRESH": ("TEST-AIDS-021",),
    "REQ-AIDS-022-REFRESH": ("TEST-AIDS-022",),
    "REQ-AIDS-096-REFRESH": ("TEST-AIDS-096",),
    "REQ-AIDS-097-REFRESH": ("TEST-AIDS-097",),
    "REQ-AIDS-098-REFRESH": ("TEST-AIDS-098",),
    "REQ-AIDS-099-REFRESH": ("TEST-AIDS-099",),
}


# @id CODE-RELGATE-003
# @implements REQ-RELGATE-003
# @design DES-RELGATE-003
def verify_tdd_targets(tdd_cycles: list[dict[str, Any]]) -> dict[str, bool]:
    """Given the ``cycles`` list from ``.musubix/evidence/tdd.json``, report
    whether every TEST-ID named anywhere in ``TDD_REGEN_TARGET_MATRIX`` has
    at least one cycle with a valid Red and a valid Green phase."""
    target_test_ids = {
        test_id for test_ids in TDD_REGEN_TARGET_MATRIX.values() for test_id in test_ids
    }
    covered: dict[str, bool] = dict.fromkeys(target_test_ids, False)
    for cycle in tdd_cycles:
        test_id = cycle.get("testId")
        if test_id not in covered:
            continue
        red_valid = bool((cycle.get("red") or {}).get("valid"))
        green_valid = bool((cycle.get("green") or {}).get("valid"))
        if red_valid and green_valid:
            covered[test_id] = True
    return covered


# --- REQ-RELGATE-005 ----------------------------------------------------------

#: The exact follow-up command sequence a later session must run before
#: `workflow` can report `pass` (DES-RELGATE-005).
WORKFLOW_HANDOFF_STEPS = (
    "workflow-sanitize",
    "workflow-verify",
    "workflow waiver record-all",
    "gate --json",
)


# @id CODE-RELGATE-005
# @implements REQ-RELGATE-005
# @design DES-RELGATE-005
def prepare_workflow_handoff() -> dict[str, Any]:
    """Return the fixed post-session workflow handoff description exactly as
    specified by DES-RELGATE-005's ``prepare_workflow_handoff()`` interface."""
    return {
        "requires_closed_transcript": True,
        "follow_up_steps": list(WORKFLOW_HANDOFF_STEPS),
        "blocking_check": "workflow",
    }


# @id CODE-RELGATE-105
# @implements REQ-RELGATE-005
# @design DES-RELGATE-005
def record_live_session_limitation() -> str:
    """Return the residual-risk note for CHANGE-025's release summary,
    documenting that `workflow` cannot pass while the Copilot transcript is
    still live (musubix3 issue #63)."""
    return (
        "workflow check deferred: musubix3 issue #63 prevents "
        "workflow-sanitize from accepting a still-running Copilot session's "
        "own live transcript; a later session must run the documented "
        "post-session reconciliation procedure before `workflow` can pass."
    )
