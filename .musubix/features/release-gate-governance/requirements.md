---
schemaVersion: 1
feature: release-gate-governance
---
# Requirements / 要求

Feature: Repository-level release-gate debt remediation for legacy musubix3
evidence, reducing the repairable share of pre-existing baseline debt so it
no longer blocks unrelated changes, while honestly disclosing the one
currently unfixable, upstream-blocked diagnostic (`CHANGE-003`'s
`CHANGE_PHASE_ORDER`, tracked at `nahisaho/musubix3#56`) that still prevents
any change's release approval from succeeding until musubix3 ships a fix.

## REQ-RELGATE-001: Full-repository baseline gate readiness / 全体リポジトリ基準のゲート準備完了
Priority: must
Type: non-functional
Pattern: state-driven
Statement: While full-repository release-gate readiness is being assessed during CHANGE-025 remediation, the repository governance baseline shall allow `npx musubix3 gate --json` to report, for `tdd`, `performance`, and `commands`, a status of `pass`, and for `change-history` and `change-completeness`, no error-severity diagnostic other than the permanently-excluded exceptions defined in REQ-RELGATE-002 (the 4 `CHANGE-005` scopes) and the separately-tracked, currently CLI-unfixable `CHANGE-003:CHANGE_PHASE_ORDER` defect (upstream `nahisaho/musubix3#56`, outside this change's remediable scope since no supported re-record or waiver operation exists for it), on the full repository scope, so pre-existing baseline debt does not block unrelated changes on evidence that can be repaired before the session ends.
Acceptance: On a worktree whose only uncommitted changes are the CHANGE-025 artifacts being actively prepared, with the repository's configured verification tools installed, a full `npx musubix3 gate --json` run during the still-running remediation session reports `pass` for the required checks `tdd`, `performance`, and `commands`; reports `change-history` and `change-completeness` with zero error-severity diagnostics except (1) all `CHANGE_WAIVER_STALE` diagnostic instances (however many are emitted) for the four explicitly-excluded `CHANGE-005:CHANGE_GREEN_UNPROVEN:REQ-ACHEM-003/010/020/050` scopes, disclosed as accepted residual risk per REQ-RELGATE-002, and (2) the single `CHANGE_PHASE_ORDER` diagnostic for `CHANGE-003:quality is not after green`, disclosed as a permanent, out-of-scope residual risk tracked upstream at `nahisaho/musubix3#56` (reopened) because no CLI operation — re-recording or waiving — can clear it today, and CHANGE-025 does not attempt to; during that live session, `workflow` may still fail because `WORKFLOW_INVOCATION_UNVERIFIED` cannot be cleared until the transcript closes, and `approval` may still fail until CHANGE-025's own release approval is recorded. If the remediation session has already terminated and a later session reruns the documented workflow verification procedure against the finished transcript, that later full gate run also reports `workflow` as `pass`. Note: because `CHANGE_PHASE_ORDER` is error-severity and the full-repository `change-history`/`change-completeness` checks and `approval record release` evaluate without any per-diagnostic suppression, this diagnostic also blocks `approval record release` for CHANGE-025 itself and every other change until `nahisaho/musubix3#56` is fixed upstream; this requirement's acceptance is limited to the diagnostic-count criteria above, not to achieving a literal `pass` status on those two checks or a successful release approval while the defect remains unfixed upstream.

## REQ-RELGATE-002: Fresh historical change-waiver snapshots / 履歴変更waiverの最新スナップショット
Priority: must
Type: non-functional
Pattern: event-driven
Statement: When a currently-firing TDD-evidence completeness diagnostic for a staged change's requirement has no current waiver covering it, the governance evidence workflow shall record or refresh a change waiver entry scoped to that exact diagnostic/requirement and the current evidence snapshot, so full-repository gate evaluation reports it only as a waived warning, following the same re-recording procedure already used for CHANGE-009/010/012/014's #69 remediation.
Acceptance: For the 9 currently-error scopes `CHANGE-001:{CHANGE_RED_UNPROVEN,CHANGE_GREEN_UNPROVEN,CHANGE_COMPLETENESS_TDD}:REQ-AISCI-004/017/024` (each already waived once, now stale), rerunning the documented waiver re-recording procedure removes their `CHANGE_WAIVER_STALE` diagnostics. For the equivalent 9 currently-error scopes `CHANGE-019:{CHANGE_RED_UNPROVEN,CHANGE_GREEN_UNPROVEN,CHANGE_COMPLETENESS_TDD}:REQ-AISCI-004/017/024` (never previously waived, confirmed by the absence of any `CHANGE_WAIVER_STALE` diagnostic for them), recording a first-time waiver downgrades them from error to waived warning. Both sets rely on the diagnostic genuinely still firing today (confirmed by the live `gate --json` run), not on reproducing a historical test execution, since `change waiver record` only requires the target diagnostic to be currently present, not re-derived from a fresh TDD cycle. Neither set requires re-running tests or re-recording `change-record` phases, and neither weakens the underlying gate rules or rewrites historical requirement text. The 4 scopes `CHANGE-005:CHANGE_GREEN_UNPROVEN:REQ-ACHEM-003/010/020/050` are explicitly excluded from any refresh attempt: CHANGE-005.md and upstream musubix3 issue #55 document that once the root diagnostic genuinely stops firing, the CLI has no supported retract/supersede operation and permanently re-reports `CHANGE_WAIVER_STALE` regardless of remediation — this was already disclosed and accepted as residual risk at CHANGE-005's own release and remains accepted, unchanged, here.

## REQ-RELGATE-003: Fresh authoritative TDD evidence for legacy requirements / 既存要求への最新TDD根拠
Priority: must
Type: non-functional
Pattern: event-driven
Statement: When a mandatory requirement lacks a valid authoritative Red-Green cycle or a verifying test file changes after its latest passing TDD phase, the remediation workflow shall record fresh authoritative TDD evidence from the configured test command so the required `tdd` check can report `pass`.
Acceptance: After rerunning and honestly recording the affected evidence, full `npx musubix3 gate --json` output reports no `TDD_REQUIREMENT_UNCOVERED` diagnostic for `REQ-AIMS-040` and no `TDD_TEST_STALE` diagnostics for `TEST-AIDS-021`, `TEST-AIDS-022`, `TEST-AIDS-096`, `TEST-AIDS-097`, `TEST-AIDS-098`, or `TEST-AIDS-099`.

## REQ-RELGATE-004: Deterministic performance provenance for pytest pass rate / pytest合格率の決定的性能根拠
Priority: must
Type: non-functional
Pattern: event-driven
Statement: When `REQ-AIDS-013` is proven through the repository's configured pytest gate, the performance evidence shall include exactly one successful command/report provenance chain for counter `tests.pass_rate` emitted by `TEST-AIDS-PYTEST-001`, so the deterministic performance check can identify both the counter value and its originating command/report pair.
Acceptance: After running the configured test command and rebuilding evidence, full `npx musubix3 gate --json` output reports the required `performance` check as `pass` with no `PERFORMANCE_COUNTER_MISSING` or `PERFORMANCE_PROVENANCE_MISSING` diagnostics for `REQ-AIDS-013` / `TEST-AIDS-PYTEST-001`.

## REQ-RELGATE-005: Post-session workflow pass under live-session limits / ライブセッション制約下でのセッション後workflow合格
Priority: must
Type: non-functional
Pattern: unwanted-behavior
Statement: If full-repository gate evaluation includes workflow declarations produced in a still-running Copilot session whose live transcript cannot be sanitized because of musubix3 GitHub issue #63, then the governance workflow shall defer final `workflow`-check passage to a later session that runs workflow verification in compatible mode and records declaration-scoped workflow waivers against the finished transcript, as one of the independent prerequisites for any future CHANGE-025 release approval attempt (the other being an upstream fix for the separately-tracked `nahisaho/musubix3#56` blocker).
Acceptance: During the still-running remediation session, the operator records that `workflow` cannot yet pass because the transcript is live and continues remediating the other required non-approval checks. After that session terminates, a later session runs the documented compatible verification plus `npx musubix3 workflow waiver record-all`, and the next full `npx musubix3 gate --json` run reports `workflow` as `pass` with no remaining waivable workflow diagnostics.
