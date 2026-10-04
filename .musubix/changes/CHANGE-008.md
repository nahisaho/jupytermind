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

- **New operations (REQ-AIDS-015, amended)**: `aggregate` (group-wise
  `mean`/`sum`/`count_eq` computed per `group_col` value and broadcast
  back onto every row of that group via `groupby(...).transform(...)`),
  `interaction`
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
- **Residual leakage risk, explicitly out of scope**: `fit_features`/
  `transform_features` only cover the `scale` operation. `aggregate`
  (and any other statistics-estimating operation) is **not** leakage-safe
  via this API — calling `engineer_features(df, "aggregate", ...)` on a
  dataframe spanning both training and held-out rows lets each row's
  feature depend on other rows in the same fold/group, including
  held-out ones. There is currently **no** leakage-safe way to compute
  `aggregate` features across a train/held-out split: the unsafe
  single-call path is the only one available. A future change would need
  to extend `fit_features`/`transform_features` (fit group statistics on
  the training fold only, then map those fixed statistics onto the
  held-out fold, with an explicit policy for unseen groups/missing
  values) before `aggregate` can be considered leakage-safe. Only the
  `scale` leakage risk originally reported in #51 is addressed by this
  change.
- **Known pre-existing gap, explicitly out of scope**: REQ-AIDS-015's
  Statement names "feature selection" among the supported transformation
  kinds, but no `operation` value or acceptance criterion for it has ever
  existed (true before CHANGE-008 as well — the original statement and
  DES-AIDS-013 never implemented it). This gap is not introduced or
  widened by CHANGE-008 and is not addressed here; it is documented
  transparently rather than silently implemented as unplanned scope
  (mirroring the CHANGE-006 `CHANGE_COMPLETENESS_ADR` disclosure
  precedent). Tracked for a future change if prioritized.
- **Minor documentation notes (non-blocking, native rubber-duck review
  finding)**: (1) `TEST-AIDS-156`'s name (`unknown_params_raise`) actually
  exercises a *missing*-required-parameter case, not a rejected-unknown
  (extra/misspelled) parameter — `engineer_features` does not validate or
  reject unexpected keyword parameters today; misspelled optional params
  are silently ignored rather than raising. (2) `bin` accepts and bins
  every column in `columns`, not only a single column; this is intentional
  (matches the other multi-column operations) but is called out here since
  the design text emphasizes a single source column.
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
- [x] TDD Red/Green per requirement: 10 tests (`TEST-AIDS-015` amended,
  `TEST-AIDS-151`–`159` new) each individually recorded red then green
  (`CODE-AIDS-093`/`094`/`095` implementing `FittedFeatureState`,
  `fit_features`, `transform_features`).
- [x] `trace build`/`trace check --strict` (0 diagnostics), `graph
  index`/`graph gate` (PASS).
- [x] Quality gate (`gate --changed --json`, `status --json`): no new
  diagnostics attributable to this change; full suite `408 passed`. All
  surfaced diagnostics are pre-existing, previously-disclosed repo-wide
  items (CHANGE-001 ADR/TDD completeness gaps, legacy `TEST-AIMS-002/040`
  evidence, workflow-log verification, performance-counter provenance) —
  unrelated to and unchanged by this feature.
- [x] Release approval: explicit human sign-off (approver: nahisaho) via
  `ask_user`, approving the exact file list and the manifest hash
  `12468b03b585601e01b6278e412d6ad64b33a30139dd75c775308d38c5ed881e`
  (repo-wide `approval prepare release` manifest, 1224 files) together
  with all residual risks disclosed above. `musubix3 approval record
  release` itself cannot complete: it refuses while `workflow`/`tdd`/
  `change-history`/`change-completeness`/`performance`/`input-stability`
  checks report errors, but every one of those diagnostics traces to
  pre-existing, already-released, non-CHANGE-008 repo state (CHANGE-001's
  non-waivable `CHANGE_COMPLETENESS_ADR`/TDD gaps, legacy
  `TEST-AIMS-002`/`TEST-AIMS-040` unscoped evidence predating this
  session's musubix3 version, and `WORKFLOW_INVOCATION_UNVERIFIED`
  session-log reconciliation) — none are introduced or widened by
  CHANGE-008. This mirrors the CHANGE-006 precedent of proceeding on
  explicit human decision when `status.gate.ready` cannot reach true due
  to the same category of non-waivable, pre-existing blockers.
- [x] Commit, push, close #51.

## Status

Released. Human release approval recorded (approver: nahisaho, hash
`12468b03b585601e01b6278e412d6ad64b33a30139dd75c775308d38c5ed881e`);
`musubix3 approval record release` blocked only by pre-existing,
non-CHANGE-008 repo-wide diagnostics (see above), consistent with
CHANGE-006 precedent.
