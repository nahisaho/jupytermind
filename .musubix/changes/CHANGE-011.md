# CHANGE-011: explainability.explain_model signed contributions and permutation importance (#49)

## Summary

Extend `src/ai_data_scientist/explainability.py` so
`explainability.explain_model` can do more than a legacy magnitude-only global
ranking. The change keeps the existing 2-argument call behavior intact by
default, but adds:

- explicit `importance_kind` labeling for every returned ranking;
- opt-in signed local contributions with additive-consistency reporting; and
- opt-in permutation importance with configurable scoring.

The enhancement addresses issue #49's explainability gap: callers can keep the
legacy ranking where backward compatibility matters, but they also gain an
auditable route to directional/local explanations and a scale-robust global
importance method.

## Scope

- Existing feature: `ai-data-scientist-ml`.
- Touches:
  `.musubix/features/ai-data-scientist-ml/requirements.md`,
  `.musubix/features/ai-data-scientist-ml/design.md`,
  `src/ai_data_scientist/explainability.py`,
  `tests/test_explainability.py`.
- No change-record, approval-record, TDD-evidence, workflow-record, or gate
  ledger writes are included in this branch by design; those shared-evidence
  steps must be serialized later through `main`.
- SHAP support is planned as optional: if the environment already provides the
  `shap` package, the signed-contribution path may use it; otherwise the module
  falls back to native `pred_contrib`, linear additive decomposition, or an
  explicit instruction to use permutation importance/install SHAP.
- Signed local contributions are currently scoped to supported single-output
  regression and binary-classification models; multi-class provider outputs are
  intentionally left out of this draft's scope.

## Affected Requirements

Requirements: REQ-AIDS-082, REQ-AIDS-083, REQ-AIDS-084.

## Design

Design: DES-AIDS-070 (result contract + method selection), DES-AIDS-071
(signed-contribution provider normalization + additivity check),
DES-AIDS-072 (permutation-importance path). ADRs: none — each entry is a
localized extension of the existing explainability module with existing
library primitives.

## Implementation Plan

- [x] Draft requirements for default-compatibility labeling, signed
  contributions, and permutation importance.
- [x] Draft design for the result contract, provider-selection order, and
  permutation-importance execution path.
- [x] Validate requirements and manually rubber-duck review requirements/design,
  fixing validator/EARS issues found during review.
- [x] Add failing tests for the new opt-in explainability paths.
- [x] Implement `explain_model` method selection, result metadata, signed
  contributions, and permutation importance.
- [x] Run focused, module-level, and full-suite pytest coverage, confirming no
  regressions.
- [x] Cover SHAP-provider selection with mocked tests and ensure additivity is
  reported as unavailable when raw model outputs cannot be retrieved.
- [x] ID collision reconciliation at merge: confirmed `CODE-AIDS-106`–`110`
  and `TEST-AIDS-169`–`177` had no collisions against `main` (already
  including CHANGE-009's `CODE-AIDS-119`–`124`/`TEST-AIDS-185`–`194` and
  CHANGE-010's `CODE-AIDS-101`–`105`/`TEST-AIDS-161`–`168` ranges); no
  renumbering was necessary.
- [x] Human approval of requirements/design draft (approver: nahisaho,
  `approval record requirements`/`approval record design`, both current;
  design was re-approved once after a legitimate DES-AIDS-071 code-ID
  cross-reference edit).
- [x] Committed and rebased worktree `change-011-signed-contrib` onto
  updated `main`, merged cleanly (fast-forward, no conflicts); full suite
  `442 passed` after merge and after a ruff format fix scoped to this
  change's two files.
- [x] TDD Red/Green per requirement: 9 tests (`TEST-AIDS-169`–`177`) each
  individually recorded red (against `explainability.py` temporarily
  reverted to the pre-CHANGE-011 `main` state) then green (against the
  restored full implementation).
- [x] `trace build`/`trace check --strict` (clean), `graph index`/`graph
  gate` (PASS, no cycles).
- [x] Quality gate (`gate --changed --json`): no new diagnostics
  attributable to this change beyond the same structural category
  CHANGE-008/CHANGE-009/CHANGE-010 already disclosed —
  `change-history`/`change-completeness` report `CHANGE_RED_UNPROVEN`/
  `CHANGE_GREEN_UNPROVEN`/`CHANGE_COMPLETENESS_TDD` for
  REQ-AIDS-082–084 because this change's Red/Green evidence was recorded
  after the worktree merge rather than via genuine incremental
  step-by-step TDD (same root cause and same already-accepted precedent);
  no `CHANGE_COMPLETENESS_ADR` diagnostic applies (no ADRs declared). All
  other failing checks (`workflow`/`tdd`/`performance`/`test-identities`)
  are pre-existing, previously-disclosed repo-wide items unrelated to and
  unchanged by this feature. Full suite `442 passed`.
- [x] Release approval: explicit human sign-off (approver: nahisaho) via
  `ask_user`, approving the exact file list and the manifest hash
  `5856d5effe2282cabae95b2b770526b751855cb78fa9ae8bc7e9f6e27f486aa4` (repo-wide `approval prepare release` manifest)
  together with all residual risks disclosed above. `musubix3 approval
  record release` itself cannot complete for the same reasons as prior
  precedent — the full (non-`--changed`) gate it runs is blocked by
  pre-existing, non-CHANGE-011 diagnostics plus this change's own
  recording-order-debt from retroactive evidence recording.
- [x] Commit, push, close #49.

## Status

Released. Human release approval recorded (approver: nahisaho, hash
`5856d5effe2282cabae95b2b770526b751855cb78fa9ae8bc7e9f6e27f486aa4`); `musubix3 approval record release` blocked only by
pre-existing, non-CHANGE-011 repo-wide diagnostics plus this change's own
recording-order-debt (see above), consistent with
CHANGE-006/CHANGE-008/CHANGE-009/CHANGE-010 precedent.

## #69 Remediation

Remediation work was performed as part of issue #69 (residual, out-of-scope
debt discovered while closing #62; #62 itself never included CHANGE-011);
final human release approval remains requested/pending until recorded below.

The gate diagnostics this change already disclosed above
(`CHANGE_RED_UNPROVEN`/`CHANGE_GREEN_UNPROVEN`/`CHANGE_COMPLETENESS_TDD` for
REQ-AIDS-082/083/084, caused by retroactively-recorded rather than
incrementally-recorded TDD evidence) are all requirement-scoped waivable
codes in musubix3 v0.1.20. No `CHANGE_COMPLETENESS_ADR` diagnostic applies:
DES-AIDS-070 (`explain_model` result contract and method selection) already
cites `ADR-0053`; DES-AIDS-071 (signed-contribution provider normalization)
and DES-AIDS-072 (permutation-importance path) each explicitly declare
"ADRs: none" because they are localized extensions of the existing
`explainability.py` module using existing library primitives (no new
architectural decision to record).

Remediation performed:

1. Recorded 9 requirement-scoped waivers (3 codes ×
   REQ-AIDS-082/083/084), citing the retroactive-evidence-recording
   constraint above and issue #69.
2. Re-ran `gate --json`: all 9 diagnostics are now `warning` severity
   (waived), not `error`.
3. Ran the full test suite: all tests passed — expected, since no
   functional code changed (waiver-recording only).
4. Human release approval (`nahisaho`) is requested for the exact file set
   and `approval prepare release --json` hash presented at merge time (see
   "Debt Remediation Approval" section below, added once approval is
   obtained).

## Debt Remediation Approval

Human release approval obtained from `nahisaho` via `ask_user` for the exact
3-file change set below, matching `approval prepare release --json`
`artifactSha256 502547a79f4b0f482d7c00d57f6d82c5bd5dd586c9793451b973d07afbc55d43`:

- `.musubix/changes/CHANGE-011.md`
- `.musubix/evidence/change-waivers.json`
- `.musubix/evidence/order.json`

(`musubix3 approval record release` could not be run directly: it is blocked
repo-wide by unrelated pre-existing debt, consistent with the pattern already
established for CHANGE-001/CHANGE-017 in this same remediation effort.)
