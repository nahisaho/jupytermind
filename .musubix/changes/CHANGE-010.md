# CHANGE-010: Add paired experiment-comparison support for `experiment_evaluation` (#50)

## Summary

Add first-class paired-comparison support to
`ai_data_scientist.experiment_evaluation.evaluate_experiment` so model or
fold comparisons on the same validation rows no longer have to misuse the
legacy independent two-sample t-test. CHANGE-010 preserves the existing
`test="ttest"` behavior, adds `test="paired_t"` via
`scipy.stats.ttest_rel`, adds `test="wilcoxon"` via
`scipy.stats.wilcoxon`, and adds `test="paired_bootstrap"` for aligned
prediction or fold-score comparisons. The bootstrap path supports
caller-supplied metric functions such as ROC AUC, returns a confidence
interval (without claiming a bootstrap p-value), rejects non-finite or
misaligned paired inputs, and keeps paired resampling aligned across
control/treatment observations.

## Scope

- Existing feature: `ai-data-scientist-ml`.
- Touches: `.musubix/features/ai-data-scientist-ml/requirements.md`,
  `.musubix/features/ai-data-scientist-ml/design.md`,
  `src/ai_data_scientist/experiment_evaluation.py`, and
  `tests/test_experiment_evaluation.py`.
- Backward-compatibility constraint: existing `test="ttest"` callers must
  continue to behave identically.
- Explicitly out of scope: DeLong's test, change/evidence ledger recording,
  human approvals, and any unrelated experiment-analysis APIs.

## Affected Requirements

Requirements: REQ-AIDS-079, REQ-AIDS-080, REQ-AIDS-081.

These are new normative requirements added for CHANGE-010. REQ-AIDS-022 is
left unchanged and continues to cover the legacy independent two-sample
experiment-evaluation behavior.

## Design

Design: DES-AIDS-067 (paired hypothesis-test dispatch),
DES-AIDS-068 (paired bootstrap metric-comparison engine), DES-AIDS-069
(result payload/backward-compatible interpretation path). ADRs: none —
this change extends the existing SciPy-backed module directly without a new
architectural boundary.

## Implementation Plan

- [x] Draft REQ-AIDS-079 through REQ-AIDS-081 for paired t-test,
  Wilcoxon signed-rank, and paired bootstrap behavior.
- [x] Draft DES-AIDS-067 through DES-AIDS-069 for dispatch, bootstrap
  resampling, and result payload changes.
- [x] Self-review the requirements/design diffs in place of the unavailable
  native `rubber-duck` agent in this environment, fixing review findings
  before implementation.
- [x] Add pytest red coverage for paired t-test, Wilcoxon, unequal-length
  paired validation, paired prediction bootstrap, paired fold bootstrap,
  and bootstrap argument validation.
- [x] Extend `experiment_evaluation.py` with paired-test dispatch,
  bootstrap confidence intervals, and backward-compatible `ttest`
  preservation.
- [x] Run the module's full pytest file
  (`tests/test_experiment_evaluation.py`) to confirm green behavior.
- [x] ID collision reconciliation at merge: confirmed `CODE-AIDS-101`–`105`
  and `TEST-AIDS-161`–`168` had no collisions against `main` (already
  including CHANGE-009's `CODE-AIDS-119`–`124`/`TEST-AIDS-185`–`194`
  ranges) or against CHANGE-011/CHANGE-012's reserved ranges; no
  renumbering was necessary.
- [x] Human approval of requirements/design draft (approver: nahisaho,
  `approval record requirements`/`approval record design`, both current;
  design was re-approved once after a legitimate DES-AIDS-069 code-ID
  cross-reference edit).
- [x] Merged `change-010-paired-tests` into `main` (clean merge, no
  conflicts); full suite `433 passed` after merge and after a ruff format
  fix.
- [x] TDD Red/Green per requirement: 8 tests (`TEST-AIDS-161`–`168`) each
  individually recorded red (against `experiment_evaluation.py` temporarily
  reverted to the pre-CHANGE-010 `main` state) then green (against the
  restored full implementation).
- [x] `trace build`/`trace check --strict` (clean), `graph index`/`graph
  gate` (PASS, no cycles).
- [x] Quality gate (`gate --changed --json`): no new diagnostics
  attributable to this change beyond the same structural category
  CHANGE-008/CHANGE-009 already disclosed — `change-history`/
  `change-completeness` report `CHANGE_RED_UNPROVEN`/
  `CHANGE_GREEN_UNPROVEN`/`CHANGE_COMPLETENESS_TDD` for
  REQ-AIDS-079–081 because this change's Red/Green evidence was recorded
  after the worktree merge rather than via genuine incremental
  step-by-step TDD (same root cause and same already-accepted precedent as
  CHANGE-006/CHANGE-008/CHANGE-009); no `CHANGE_COMPLETENESS_ADR`
  diagnostic applies (no ADRs declared). All other failing checks
  (`workflow`/`tdd`/`performance`/`test-identities`) are pre-existing,
  previously-disclosed repo-wide items (CHANGE-001/003/004/005/008 ADR/TDD
  completeness gaps, legacy `TEST-AIMS-002`/`TEST-AIMS-040` evidence,
  `WORKFLOW_INVOCATION_UNVERIFIED`, performance-counter provenance) —
  unrelated to and unchanged by this feature. Full suite `433 passed`.
- [x] Release approval: explicit human sign-off (approver: nahisaho) via
  `ask_user`, approving the exact file list and the manifest hash
  `c203c6d02c6e06d607c156772ec96fdb02291071b193f6d2a076a56175826f7d` (repo-wide `approval prepare release` manifest) together
  with all residual risks disclosed above. `musubix3 approval record
  release` itself cannot complete for the same reasons as
  CHANGE-008/CHANGE-009's precedent — the full (non-`--changed`) gate it
  runs is blocked by pre-existing, non-CHANGE-010 diagnostics plus this
  change's own recording-order-debt from retroactive evidence recording.
- [x] Commit, push, close #50.

## Status

Released. Human release approval recorded (approver: nahisaho, hash
`c203c6d02c6e06d607c156772ec96fdb02291071b193f6d2a076a56175826f7d`); `musubix3 approval record release` blocked only by
pre-existing, non-CHANGE-010 repo-wide diagnostics plus this change's own
recording-order-debt (see above), consistent with
CHANGE-006/CHANGE-008/CHANGE-009 precedent.
