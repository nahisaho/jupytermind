# CHANGE-008: feature_engineering aggregation/interaction/missing-flag/binning and leakage-safe fit/transform API (#51)

## Summary

Extend `ai_data_scientist.feature_engineering.engineer_features` beyond its
current `one_hot`/`scale` operations with four new operations
(`aggregate`, `interaction`, `missing_flag`, `bin`), each reporting a
structured column-name-to-definition mapping for audit/reproducibility, and
add a leakage-safe `fit_features`/`transform_features` API so
statistics-estimating transformations (currently `scale`) can be fit on a
training fold and applied to a disjoint fold without ever deriving
statistics from the held-out rows — directly addressing the CV-leakage risk
reported in #51.

- **New operations (REQ-AIDS-015, amended)**: `aggregate` (row-wise
  `mean`/`sum`/`count_eq` via `groupby(...).transform(...)`), `interaction`
  (two-column string-concatenation with `"__"` separator), `missing_flag`
  (boolean null-mask column), `bin` (explicit-edge `pandas.cut` with
  `right=True, include_lowest=True`). Every added column gets a non-empty
  `definitions` entry naming the operation and source column(s).
- **Leakage-safe fit/transform (REQ-AIDS-073, new)**: `fit_features(df,
  "scale", columns)` returns a `FittedFeatureState` holding a `StandardScaler`
  fitted only on `df[columns]`; `transform_features(fitted_state, df)`
  applies the already-fitted scaler to any `df` without recomputing
  statistics. Transforming the same fit subset reproduces the legacy
  single-call `engineer_features(df, "scale", columns)` output exactly.

## Scope

- Existing feature: `ai-data-scientist-ml`.
- Touches: `src/ai_data_scientist/feature_engineering.py` and
  `tests/test_feature_engineering.py`.
- No new skill boundary; no ADRs (`DES-AIDS-013` amendment and new
  `DES-AIDS-061` both declare "ADRs: none" — pandas/scikit-learn supply the
  transformation primitives directly, consistent with the project's
  established narrow-bugfix/extension convention).
- **Known pre-existing gap, explicitly out of scope**: REQ-AIDS-015's
  Statement names "feature selection" among the supported transformation
  kinds, but no `operation` value or acceptance criterion for it has ever
  existed (true before CHANGE-008 as well — the original statement and
  DES-AIDS-013 never implemented it). This gap is not introduced or
  widened by CHANGE-008 and is not addressed here; it is documented
  transparently rather than silently implemented as unplanned scope
  (mirroring the CHANGE-006 `CHANGE_COMPLETENESS_ADR` disclosure
  precedent). Tracked for a future change if prioritized.
- The remaining feature-enhancement issues (#48, #49, #50, #46) are
  explicitly out of scope for this change; tracked separately per the
  user-approved priority ordering (#51 → #48 → #50 → #49 → #46).

## Affected Requirements

Requirements: REQ-AIDS-015 (amended), REQ-AIDS-073 (new).

## Design

Design: DES-AIDS-013 (amended — new `operation` values, `**params`
contract, backward-compatible `definitions` field on `FeatureResult`),
DES-AIDS-061 (new — `fit_features`/`transform_features` leakage-safe API,
`FittedFeatureState` dataclass). ADRs: none for both (see each entry's
"ADRs: none" justification).

Both requirements.md and design.md passed `musubix3` structural validation
and two rounds of native `rubber-duck` review each (requirements: fixed a
non-deterministic leakage-test criterion, a dropped "feature selection"
scope word, and under-specified binning edge semantics, plus non-blocking
fixes for `count_eq`/interaction/definitions/compatibility ambiguity;
design: fixed a missing per-operation parameter-passing contract, a
camelCase/snake_case naming inconsistency, an ambiguous `FittedFeatureState`
representation, and a missing notebook-cell execution integration
reference). The second design review confirmed all 5 blocking issues
resolved except the pre-existing "feature selection" gap noted above,
which was a deliberate scope decision, not an oversight.

## Implementation Plan

- [x] Requirements (REQ-AIDS-015 amended, REQ-AIDS-073 new): drafted,
  validated, rubber-duck reviewed (2 rounds), approved.
- [x] Design (DES-AIDS-013 amended, DES-AIDS-061 new): drafted, validated,
  rubber-duck reviewed (2 rounds), approved.
- [ ] TDD Red/Green per requirement.
- [ ] `trace build`/`trace check --strict`, `graph index`/`graph gate`.
- [ ] Quality gate (`gate --changed --json`, `status --json`).
- [ ] Release approval (human sign-off via `ask_user`, presenting exact
  files/hash/residual risks).
- [ ] Commit, push, close #51.

## Status

In progress — TDD phase starting.
