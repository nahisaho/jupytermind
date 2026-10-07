# CHANGE-036: `train_model` warns on possible target-leakage feature columns (fixes #79)

## Summary

GitHub Issue #79 reports that `ai_data_scientist`'s target-selection and
feature-preparation pipeline has no check for target leakage: when one or
more remaining feature columns are a near-bijective/deterministic encoding
of the chosen target, the pipeline silently trains on them and reports a
perfect (or near-perfect) metric with no warning. Reproduced on a real
Kaggle dataset (`gpreda/chinese-mnist`): after ingestion/feature
preparation the dataframe has columns `suite_id, sample_id, code, value,
character`; `character` is picked as the 15-class target, and `code`/
`value` are both deterministic 1:1 encodings of it, so `train_model()`
reports `accuracy=precision=recall=1.0` with no diagnostic.

This change adds a bounded, additive leakage-detection heuristic inside
`train_model()`: any feature column that is non-constant, not a row-unique
identifier, and perfectly pure with respect to the target (every distinct
feature value maps to exactly one target value) is flagged via both a
Python `UserWarning` (so it is visibly surfaced in notebook output) and a
new `ModelResult.leakage_warnings` field, per `REQ-AIDS-101`/`DES-AIDS-101`.

## Scope

- Feature: `ai-data-scientist`
- Change type: defect correction (new requirement + design + implementation)
- Worktree: `/home/nahisaho/GitHub/jupytermind-change036`
- Branch: `change-036-target-leakage-detection`
- GitHub Issue: #79

Touched artifacts:

- `.musubix/features/ai-data-scientist/requirements.md` — new `REQ-AIDS-101`
- `.musubix/features/ai-data-scientist/design.md` — new `DES-AIDS-101`
- `src/ai_data_scientist/ml_modeling.py` — `ModelResult` gains
  `leakage_warnings`; `train_model()` gains the leakage-detection helper
  and its call site
- `tests/test_ml_modeling.py` — new regression tests covering
  `REQ-AIDS-101`'s scenarios

## Affected Requirements

Requirements: REQ-AIDS-101

## Design

DES-AIDS-101 (see design.md). No ADR: this is a bounded heuristic helper
with a single documented algorithm, not an architectural tradeoff.

## Implementation Plan

- [x] Requirements approved (`REQ-AIDS-101`)
- [x] Design approved (`DES-AIDS-101`)
- [x] Regression tests written (`TEST-AIDS-355`–`360`)
- [x] Red recorded (`musubix3 tdd red`, all 6 tests, genuine pre-implementation
      failures)
- [x] Implementation (`_detect_possible_target_leakage`/`CODE-AIDS-155` in
      `src/ai_data_scientist/ml_modeling.py`, plus `ModelResult.leakage_warnings`
      and the two call-site wirings)
- [x] Green recorded (`musubix3 tdd green`, all 6 tests; `TEST-AIDS-357` required
      a genuine second Red/Green cycle after a fixture fix)
- [x] Quality evidence recorded
- [ ] Release approval obtained
- [ ] Commit (`Fixes #79`), push, merge

## Quality Evidence

- `ruff format --check src tests`: PASS (215 files already formatted).
- `ruff check` on touched files: PASS. The heuristic's per-column
  `except Exception:` block required `# noqa: BLE001, S112` with an inline
  justification comment, following the repo's established suppression
  pattern (`cli.py:35`, `notebook_audit.py:302`, `sensitivity.py:375`,
  `visualization.py:102,599`): the detector must never let an
  unhashable-cell/duplicate-label column break training, so the exception is
  deliberately caught broadly and the column silently skipped.
- Full test suite: `692 passed, 0 failed` (686 pre-existing + 6 new
  `TEST-AIDS-355`–`360`). 5 pre-existing `test_explainability.py` tests now
  also emit the new `UserWarning` as an expected, non-regression side effect
  (their synthetic fixtures legitimately contain a perfectly-predictive
  `"important"` column).
- `musubix3 trace build` / `trace check --strict`: PASS, 0 diagnostics
  (1300 nodes, 1873 edges). One `TRACE_DUPLICATE`/`TRACE_ANNOTATION_ID`
  round-trip was found and fixed during this phase: the call site inside
  `train_model()` had mistakenly been tagged with the same `@id
  CODE-AIDS-155` as the helper function it calls; the duplicate/placeholder
  annotation block was removed from the call site, leaving the single `@id`
  on the helper definition only.
- `musubix3 graph index` / `graph gate`: PASS (224 files, 1343 imports,
  1421 symbols).
- `musubix3 gate --changed --json`: `change-history`/`change-completeness`
  surfaced the expected phase-ordering diagnostics for `REQ-AIDS-101`:
  `CHANGE_RED_UNPROVEN`, `CHANGE_GREEN_UNPROVEN`, `CHANGE_COMPLETENESS_TDD`.
  These are the same known musubix3 ordering quirk accepted in every prior
  CHANGE in this repo (CHANGE-029 through CHANGE-035): Red/Green evidence is
  necessarily recorded after the code exists to prove a genuine failure/pass,
  which post-hoc looks "unproven" relative to the change-history phase
  timestamps. Waived via `musubix3 change waiver record CHANGE-036 <code>
  --requirement REQ-AIDS-101 --approver nahisaho --confirm` for all three
  codes; downgraded from `error` to `warning` on re-run, confirmed.
  Unrelated pre-existing repo-wide `CHANGE_WAIVER_STALE` diagnostics for
  other, older CHANGEs (CHANGE-001, CHANGE-005, etc.) also appear in the
  full `gate --changed --json` output; these are pre-existing debt,
  unrelated to CHANGE-036, and out of scope for this change.

## Residual risk

- `CHANGE_COMPLETENESS_ADR` for `CHANGE-036:REQ-AIDS-101` remains an
  unwaived `error`: this diagnostic is **not** in the waivable code list
  (`change waiver record` explicitly rejects it), and this change has no
  ADR by design (a bounded heuristic helper with one documented algorithm,
  not an architectural tradeoff — see `design.md`'s `ADRs: none — ...`
  entry). This matches pre-existing, already-accepted repo debt: the
  identical unwaived diagnostic exists for `CHANGE-026:REQ-AIDS-044`.
- The leakage heuristic is intentionally narrow (3-condition groupby-purity
  check): it proves a column is a *possible* near-perfect predictor, not
  that leakage is present, and an empty `leakage_warnings` tuple is not
  proof of no leakage. This scope limitation is documented in
  `REQ-AIDS-101`'s acceptance criteria and in the warning message text
  itself.
- `APPROVAL_MISSING` for the release approval record is expected at this
  point in the workflow; it will be resolved once release approval is
  requested and recorded.

## Status

Requirements, design, regression tests, Red, implementation, Green, and
quality evidence are all complete and recorded. Ready for final rubber-duck
review of release evidence and release approval.
