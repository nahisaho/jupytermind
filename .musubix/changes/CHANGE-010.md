# CHANGE-010: Add paired experiment-comparison support for `experiment_evaluation` (#50)

> **DRAFT — NOT YET APPROVED**
>
> This change document is a working draft prepared for later human review in
> the orchestrating session. No musubix approval/evidence-recording commands
> have been run from this parallel worktree.

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
- [ ] Obtain human requirements/design/release approval and record official
  musubix evidence from the orchestrating session after merge serialization.
