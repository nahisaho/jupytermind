# CHANGE-025: Remediate the repairable share of repo-wide release-gate debt, and disclose the one upstream-blocked residual risk

## Summary

This change is classified as a **defect correction / remediation** for
pre-existing repository-wide musubix3 evidence debt. Multiple unrelated changes
(CHANGE-022, CHANGE-023, CHANGE-024) were blocked at
`npx musubix3 approval record release` by the same full-repository gate
failures that also reproduce on clean `main` (`6662b7c`): `workflow`, `tdd`,
`change-history`, `change-completeness`, and `performance`.

The mission of CHANGE-025 is to repair every evidence-debt item that is
actually repairable without weakening requirements or fabricating evidence,
and to honestly document what remains unfixable:

- refresh legitimately still-needed historical change waivers whose snapshots
  have gone stale;
- backfill or re-record authoritative TDD evidence for uncovered/stale legacy
  requirements and tests;
- restore deterministic performance provenance for the pytest pass-rate gate;
- remediate, in this active session, every required non-approval gate check
  that is actually fixable before the transcript closes (`tdd`,
  `change-history`, `change-completeness`, `performance`, `commands`);
- prepare the workflow follow-up that must be completed in a later session,
  after this transcript is closed, because musubix3 issue #63 prevents
  `WORKFLOW_INVOCATION_UNVERIFIED` from clearing while the current session is
  still live;
- disclose, rather than attempt to fix, `CHANGE-003`'s permanent
  `CHANGE_PHASE_ORDER:quality is not after green` diagnostic (tracked
  upstream at `nahisaho/musubix3#56`, reopened): it is neither re-recordable
  nor waivable in the installed musubix3 CLI, so it is an **unresolved,
  repository-wide blocker on `approval record release` for every change,
  including CHANGE-025 itself**, until musubix3 ships a fix. CHANGE-025 does
  **not** claim to restore a fully passing repository gate or to make any
  change's release approval succeed; it reduces the repairable debt and
  makes the remaining, upstream-blocked risk explicit and tracked.

## Scope

- New governance/process feature: `release-gate-governance`
- In scope:
  - `.musubix/features/release-gate-governance/requirements.md`
  - follow-on `design.md` / ADR work for the remediation procedure
  - historical musubix evidence files implicated by the failing checks
  - any directly related tests or support code genuinely required to make the
    evidence truthful and reproducible
- Out of scope:
  - weakening or deleting legacy requirements to silence gate failures
  - fabricating human approvals or rubber-duck review results
  - changes in sibling worktrees `jupytermind-change022/023/024`

## Affected Requirements

Requirements: REQ-RELGATE-001, REQ-RELGATE-002, REQ-RELGATE-003, REQ-RELGATE-004, REQ-RELGATE-005

## Impact

Confirmed firsthand on this worktree before remediation:

- `npx musubix3 gate --json` reports required-check failures for `workflow`,
  `tdd`, `change-history`, `change-completeness`, `performance`, `commands`,
  and `approval`.
- `workflow`: 48 unreconciled declarations, currently surfaced as
  `WORKFLOW_INVOCATION_UNVERIFIED`; per musubix3 issue #63, this specific
  diagnostic cannot be cleared until this Copilot session has ended and a later
  session runs `workflow-verify` / `workflow waiver record-all` against the
  finished transcript.
- `tdd`: `REQ-AIMS-040` uncovered plus stale fingerprints for
  `TEST-AIDS-021`, `TEST-AIDS-022`, `TEST-AIDS-096`, `TEST-AIDS-097`,
  `TEST-AIDS-098`, and `TEST-AIDS-099`.
- `change-history` / `change-completeness`: stale waivers for
  `CHANGE-005:CHANGE_GREEN_UNPROVEN:REQ-ACHEM-003/010/020/050` and
  `CHANGE-001:{CHANGE_RED_UNPROVEN,CHANGE_GREEN_UNPROVEN,CHANGE_COMPLETENESS_TDD}:REQ-AISCI-004/017/024`.
- `performance`: missing unique provenance for `REQ-AIDS-013` /
  `TEST-AIDS-PYTEST-001`.
- `commands`: skipped because this worktree currently lacks `.venv/bin/ruff`
  and `.venv/bin/pytest`, so dependency restoration is part of truthful
  verification readiness.

## Status

Requirements and design are approved (requirements artifact-sha256
`868c47d9a8de4ed4c9e3e18e5a5275fa7de07796fafcd1f6dbb892fb9e0e0180`; design
artifact-sha256 `80b8591f55f5bb496d62b887b5d54c8025abd186d3fdc7a04c18a21df8c0d1b7`,
re-recorded after ADR-0110 and the two `release-gate-governance` feature docs
were added). `impact`/`requirements`/`design`/`red`/`implementation` phases are
recorded for CHANGE-025. `green`/`quality` phases could not be recorded through
the normal per-requirement path because a pre-existing full-requirement-set
`red`/`implementation` phase permanently binds `batchFor` to that legacy batch
(no CLI command exists to undo/void a phase); this is waived via 12
`change waiver record` calls (`CHANGE_COMPLETENESS_TDD` x5,
`CHANGE_RED_UNPROVEN` x5, `CHANGE_PHASE_MISSING --detail phase:green`,
`CHANGE_PHASE_MISSING --detail phase:quality`), each with a reason disclosing
this session's recording-order constraint honestly.

Remediation completed and verified this session:

- `tdd`: fully passes. Fixed `REQ-AIMS-040` (REQ-RELGATE-003 regeneration),
  6 pre-existing stale tests outside the original scope
  (`TEST-AISCI-035`, `TEST-AIMS-002/949/950/980/981`), a further 8
  pre-existing stale tests discovered afterward
  (`TEST-AIDS-205/206/207/208/209/213/214/291`, all verifying
  `REQ-AIDS-056`), and completed two dangling red-only TDD cycles from an
  earlier in-session debugging round (`TEST-ACHEM-972`/`REQ-ACHEM-100` and
  the six `TEST-RELGATE-*`/`REQ-RELGATE-*` tests) with a genuine `tdd green`
  recording. Each fix used a real one-line break, verified failure, `tdd red`,
  revert, verified pass, `tdd green` cycle — never hand-edited evidence.
- `performance`: fully passes (`REQ-RELGATE-004`,
  `scripts/measure_pytest_pass_rate.py`).
- `change-history` / `change-completeness`: 34 stale waivers refreshed via
  `change waiver record` (CHANGE-001/003/014/019/021/025) after the above TDD
  work advanced their snapshotted fingerprints. `CHANGE-005`'s 4
  `CHANGE_GREEN_UNPROVEN` waivers remain permanently excluded from refresh
  per ADR-0110 (upstream `nahisaho/musubix3#55`, see residual risk below).
  `CHANGE-003:quality is not after green` (`CHANGE_PHASE_ORDER`) and
  `CHANGE-020`'s missing phases for `REQ-AISCI-023` are confirmed pre-existing
  baseline debt (present before this session's changes), out of this change's
  scope.
- An evidence-corruption incident occurred mid-session (`gate --json` executed
  configured commands against a stashed/baseline worktree, advancing the
  append-only order sequence against pre-CHANGE-025 state) and was fully
  recovered via a dangling-commit `git fsck`/`checkout` restore; the affected
  TDD cycles were then re-recorded from scratch to guarantee genuine evidence.

### Disclosed residual risks

1. **`workflow` / `WORKFLOW_INVOCATION_UNVERIFIED`** (musubix3 #63): cannot be
   cleared until this Copilot session ends and a later session runs
   `workflow-verify`/`workflow waiver record-all` against the closed
   transcript.
2. **`CHANGE-003:CHANGE_PHASE_ORDER`** (musubix3 #56): `quality` recorded
   before `green` for an earlier change; unwaivable, blocks
   `approval record release` repository-wide until fixed upstream.
3. **`CHANGE-021:CHANGE_ORDER_MIGRATION_REQUIRED` orphaned stale waiver**
   (musubix3 #55, reopened this session with regression evidence): fixing
   `TEST-ACHEM-972` genuinely resolved the underlying diagnostic, but the now
   orphaned waiver record cannot be re-recorded (`change waiver record`
   rejects scopes with no currently-firing diagnostic) nor retracted (no such
   CLI command exists), so `CHANGE_WAIVER_STALE` persists as an error. The
   issue's prior closure claimed a v0.1.20 fix that is not actually present in
   the published npm package (verified via `npm pack musubix3@0.1.20`);
   reopened with this evidence.
4. CHANGE-025's own release approval is therefore deferred until #56 and #55
   are fixed upstream and a subsequent full gate run passes; this is the
   change's disclosed residual risk, not a defect in CHANGE-025's own
   remediation.
