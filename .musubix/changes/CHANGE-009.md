# CHANGE-009: DRAFT — NOT YET APPROVED — CV flexibility, configurable scoring, OOF predictions, and pluggable estimators for ai-data-scientist-ml (#48)

## Summary

DRAFT — NOT YET APPROVED.

Extend the `ai-data-scientist-ml` supervised-modeling stack so
`train_model`, `tune_or_compare`, and `run_automl` can evaluate models with
reusable cross-validation fold plans (`StratifiedKFold`, `KFold`,
`GroupKFold`), caller-selected scoring metrics (including probability-based
metrics such as `roc_auc` and `log_loss`), fold-level score reporting, and
out-of-fold (OOF) predictions/probabilities. The change also allows callers
to supply sklearn-compatible external estimators so comparisons are no
longer restricted to the built-in registry.

## Scope

- Existing feature: `ai-data-scientist-ml`.
- Touches: `.musubix/features/ai-data-scientist-ml/requirements.md`,
  `.musubix/features/ai-data-scientist-ml/design.md`,
  `src/ai_data_scientist/ml_modeling.py`,
  `src/ai_data_scientist/model_tuning.py`,
  `src/ai_data_scientist/automl.py`, and the corresponding tests in
  `tests/test_ml_modeling.py`, `tests/test_model_tuning.py`,
  `tests/test_automl.py`.
- No ADRs: DES-AIDS-062 through DES-AIDS-066 all declare `ADRs: none`
  because the change composes existing scikit-learn primitives and the
  current module boundaries rather than introducing a new architecture.
- Backward-compatibility constraint: calls that omit the new CV/scoring/
  estimator arguments keep the existing holdout split behavior, built-in
  defaults, and legacy metric keys/sort direction.

## Affected Requirements

Requirements: REQ-AIDS-074, REQ-AIDS-075, REQ-AIDS-076, REQ-AIDS-077, REQ-AIDS-078.

## Design

Design: DES-AIDS-062 (reusable fold-plan builder), DES-AIDS-063
(probability-aware supervised evaluation results), DES-AIDS-064
(shared-fold tuning comparator), DES-AIDS-065 (shared-fold AutoML
candidate ranking), DES-AIDS-066 (pluggable estimator resolver). ADRs:
none.

Requirements and design artifacts passed `musubix3` structural validation.
Because the native `rubber-duck` review agent type is not available in this
environment, they were manually self-reviewed to equivalent rigor before
implementation; the review tightened the EARS wording, clarified CV result
shape semantics, and removed ambiguity about how custom AutoML estimators
combine with the built-in registry.

## Implementation Plan

- [x] Draft and validate requirements (REQ-AIDS-074–078).
- [x] Draft and validate design (DES-AIDS-062–066).
- [x] Add tests for stratified/grouped CV, configurable scoring, reusable
  fold plans, OOF probabilities, and custom estimators.
- [x] Implement shared CV/scoring/OOF/pluggable-estimator support in
  `ml_modeling`, `model_tuning`, and `automl`.
- [x] Run impacted pytest coverage:
  `tests/test_ml_modeling.py`, `tests/test_model_tuning.py`,
  `tests/test_automl.py`, `tests/test_explainability.py`.
- [ ] Human approval of requirements/design draft.
- [ ] Shared-ledger musubix evidence recording steps (must be run later by
  the orchestrating session against serialized `main`).

## Status

Ready for orchestrating-session review and human approval; intentionally not
recorded into the shared musubix evidence ledger from this parallel
worktree.
