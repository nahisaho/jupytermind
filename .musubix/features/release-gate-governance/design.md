---
schemaVersion: 1
feature: release-gate-governance
---
# Design / 設計

Repository-level governance design for remediating baseline musubix3 evidence
debt that blocks release approvals across otherwise unrelated changes. This
feature does not weaken any existing requirement or gate rule. Instead, it
defines a deterministic remediation workflow that separates:

1. checks that can be repaired truthfully inside the active CHANGE-025 session
   (`tdd`, `change-history`, `change-completeness`, `performance`, `commands`);
2. the `workflow` check, whose final pass is structurally deferred until a
   later session can verify the closed transcript (musubix3 issue #63);
3. `CHANGE-003`'s `CHANGE_PHASE_ORDER` diagnostic, a permanently unwaivable,
   unrecordable residual risk (`nahisaho/musubix3#56`, reopened) that this
   feature discloses but cannot repair, and which independently blocks
   `approval record release` for every change in the repository, including
   CHANGE-025 itself, until musubix3 ships a fix. This feature reduces
   repairable debt; it does not restore a fully passing repository gate or
   make any change's release approval succeed while that upstream defect
   persists.

## DES-RELGATE-001: Baseline gate readiness coordinator / 基準ゲート準備コーディネータ
Responsibilities: Establish the exact target end-state for CHANGE-025 by
running the full repository gate, classifying each failing required check as
either active-session-remediable or post-session workflow-only, and tracking
that classification in the CHANGE-025 evidence summary so later phases repair
the correct set without claiming stronger readiness than the CLI can prove.
Interfaces: assess_baseline_gate() -> BaselineGateStatus {in_session_required:
[`tdd`, `change-history`, `change-completeness`, `performance`, `commands`],
post_session_required: [`workflow`], approval_pending: true}; summarize_status()
-> release-gate readiness narrative for CHANGE-025.
Constraints: Must treat `workflow` as post-session-only while the current
Copilot transcript is live; must treat `approval` as a separate human-gated
step rather than a remediable verification failure.
Requirements: REQ-RELGATE-001, REQ-RELGATE-005
ADRs: ADR-0110
Depends-On: DES-RELGATE-005

## DES-RELGATE-002: Historical waiver refresh procedure / 履歴waiver更新手順
Responsibilities: Record or refresh change waivers for `CHANGE_RED_UNPROVEN`,
`CHANGE_GREEN_UNPROVEN`, and `CHANGE_COMPLETENESS_TDD` diagnostics that are
genuine, bounded, and currently present, preserving the original scope
(`changeId`, code, and requirement/detail selector) while appending a new
snapshot-hash-chained waiver entry for the current evidence state. This covers
both a true refresh (an existing waiver has gone stale) and a first-time
record (the diagnostic is currently present but never previously waived); both
use the same `change waiver record` operation, which only requires the target
diagnostic to be currently firing — not a freshly reproduced TDD cycle.
Interfaces: refresh_waiver(change_id, code, selector, reason, approver) ->
RefreshedWaiverRecord; refresh_required_stale_waivers() -> list[RefreshedWaiverRecord];
record_first_time_waivers() -> list[WaiverRecord].
Constraints: Must never create a waiver for a diagnostic that is no longer
present; must never widen a selector beyond the exact failing requirement/detail
scope; must retain the underlying gate rule and historical requirement text
unchanged; must explicitly skip the 4 permanently-stale
`CHANGE-005:CHANGE_GREEN_UNPROVEN:REQ-ACHEM-003/010/020/050` scopes (no refresh
attempt — see ADR-0110's accepted residual risk).
Target scopes: refresh the 9 `CHANGE-001:{CHANGE_RED_UNPROVEN,CHANGE_GREEN_UNPROVEN,CHANGE_COMPLETENESS_TDD}:REQ-AISCI-004/017/024`
scopes (each already has a now-stale waiver); first-time-record the equivalent
9 `CHANGE-019:{CHANGE_RED_UNPROVEN,CHANGE_GREEN_UNPROVEN,CHANGE_COMPLETENESS_TDD}:REQ-AISCI-004/017/024`
scopes (confirmed via live `gate --json` to have no prior waiver at all).
Requirements: REQ-RELGATE-002
ADRs: ADR-0110
Depends-On: none

## DES-RELGATE-003: Legacy TDD evidence regenerator / 既存TDD根拠再生成器
Responsibilities: Reconstruct authoritative Red-Green coverage for legacy
requirements/tests by selecting the configured command, running the minimal
verifying test set honestly, and recording fresh TDD evidence whenever a
requirement is uncovered or a verifying test fingerprint is stale.
Target matrix (requirement -> test IDs -> command -> expected evidence action):
| Requirement | Test ID(s) | Command | Action |
|---|---|---|---|
| REQ-AIMS-040 | TEST-AIMS-040 (configured pytest selection for ai-materials-scientist) | `test` (pytest) | Run `tdd red`/`tdd green` to replace `TDD_REQUIREMENT_UNCOVERED` with a fresh authoritative Red-Green pair |
| (fingerprint refresh only, no behavior change) | TEST-AIDS-021 | `test` (pytest) | Rerun command, record fresh Green fingerprint to clear `TDD_TEST_STALE` |
| (fingerprint refresh only, no behavior change) | TEST-AIDS-022 | `test` (pytest) | Rerun command, record fresh Green fingerprint to clear `TDD_TEST_STALE` |
| (fingerprint refresh only, no behavior change) | TEST-AIDS-096 | `test` (pytest) | Rerun command, record fresh Green fingerprint to clear `TDD_TEST_STALE` |
| (fingerprint refresh only, no behavior change) | TEST-AIDS-097 | `test` (pytest) | Rerun command, record fresh Green fingerprint to clear `TDD_TEST_STALE` |
| (fingerprint refresh only, no behavior change) | TEST-AIDS-098 | `test` (pytest) | Rerun command, record fresh Green fingerprint to clear `TDD_TEST_STALE` |
| (fingerprint refresh only, no behavior change) | TEST-AIDS-099 | `test` (pytest) | Rerun command, record fresh Green fingerprint to clear `TDD_TEST_STALE` |
Interfaces: refresh_tdd_requirement(requirement_id, test_ids, command_name) ->
TddRefreshResult {red_recorded, green_recorded, stale_fingerprints_cleared};
verify_tdd_targets() -> TddDebtStatus.
Constraints: Must use authoritative verifying tests already linked by
`@id`/`@verifies`; must not mark a requirement covered without a real passing
Green phase from the configured command; must preserve the requirement text
rather than rewriting it to match missing evidence; must process exactly the
target matrix above — no other requirement/test is in scope for this
procedure.
Requirements: REQ-RELGATE-003
ADRs: ADR-0110
Depends-On: none

## DES-RELGATE-004: Command and performance provenance rebuilder / コマンド・性能由来再構築
Responsibilities: Restore the repository's required command execution surface
(`format`, `test`) in the local worktree, rerun the configured test command so
structured reports exist again, and rebuild deterministic performance evidence
for `tests.pass_rate` with a unique command/report provenance chain bound to
`TEST-AIDS-PYTEST-001` / `REQ-AIDS-013`.
Interfaces: ensure_required_tools() -> ToolingStatus; run_required_commands() ->
CommandEvidenceStatus; rebuild_performance_evidence() -> PerformanceEvidenceStatus.
Constraints: Must derive `tests.pass_rate` from the configured authoritative
pytest command, not from a synthetic report; must leave command names and their
required status unchanged; must rebuild provenance from real command output
rather than hand-editing evidence files; before recording, must delete or
supersede any pre-existing `tests.pass_rate`/`TEST-AIDS-PYTEST-001` provenance
chain so that exactly one successful command/report provenance chain for that
counter/test pair exists afterward, per REQ-RELGATE-004 — never append a second
chain alongside a stale one.
Requirements: REQ-RELGATE-001, REQ-RELGATE-004
ADRs: ADR-0110
Depends-On: DES-RELGATE-003

## DES-RELGATE-005: Post-session workflow reconciliation handoff / セッション後workflow照合ハンドオフ
Responsibilities: Capture the fact that live-session workflow reconciliation is
incomplete by design, preserve the exact follow-up procedure to execute after
this session terminates, and constrain in-session work to compatible
verification preparation rather than impossible attempts to clear
`WORKFLOW_INVOCATION_UNVERIFIED` early.
Interfaces: prepare_workflow_handoff() -> WorkflowHandoff {
requires_closed_transcript: true,
follow_up_steps: [`workflow-sanitize`, `workflow-verify`, `workflow waiver record-all`, `gate --json`],
blocking_check: `workflow`
}; record_live_session_limitation() -> residual-risk note for CHANGE-025.
Constraints: Must not claim `workflow` is passable before the transcript is
closed; must require the later session to rerun the full gate after workflow
verification and waivers; must keep the post-session handoff explicit in the
CHANGE-025 release summary.
Requirements: REQ-RELGATE-005
ADRs: ADR-0110
Depends-On: none

ADRs: ADR-0110
Depends-On: DES-RELGATE-003
