# CHANGE-040: REQ-AIDS-110 Acceptance フィクスチャの修正 (fixes #84)

## Summary

GitHub Issue #84 reported that REQ-AIDS-110 (Missing-data MCAR/MAR-suggestive
heuristic diagnostic) carried two broken Acceptance fixtures: both example
input/output pairs' literal `t_statistic`/`p_value` numbers did not actually
reproduce via `scipy.stats.ttest_ind` on the stated inputs — despite the
Acceptance text claiming the values were "verified empirically in this
change" (CHANGE-039). The implementation
(`src/ai_data_scientist/missing_data_analysis.py`) and its tests
(`tests/test_missing_data_analysis.py`, `TEST-AIDS-415`/`TEST-AIDS-416`) were
already correct against the Statement/Constraints' algorithm description and
already used different, independently empirically-verified fixture values,
with an inline comment documenting the discrepancy and referencing #84.

This is a documentation/specification-only defect: no requirement obligation
or implemented behavior changed. The Acceptance section's illustrative
numeric fixtures are corrected to match reality, and the Statement text
itself gained one clarifying clause (naming `ttest_ind`'s fixed
`missing_group, observed_group` argument order), which DES-AIDS-110's design
text was correspondingly updated to state explicitly too — both clauses
only make explicit what the existing implementation already did; neither
changes any runtime behavior, interface, or constraint.

## Scope

- Feature: `ai-data-scientist`
- Change type: defect correction (specification/documentation defect in an
  existing Acceptance fixture; no implementation or Statement/Constraints
  behavior change)
- Worktree: `/home/nahisaho/GitHub/jupytermind-change040`
- Branch: `change-040-fix-aids110-fixtures`
- GitHub Issue: #84

Requirements: REQ-AIDS-110

## Impact analysis

`npx musubix3 trace impact REQ-AIDS-110 --json` confirms the only artifacts
reachable from REQ-AIDS-110 are: `DES-AIDS-110`, `ADR-0124`, `CODE-AIDS-165`
(`diagnose_missingness`), and `TEST-AIDS-415`/`416`/`417`/`418`. No other
requirement, design, or code artifact is affected.

Empirical verification performed before editing requirements.md (via
`scipy.stats.ttest_ind`, matching the implementation's exact
`ttest_ind(missing_group, observed_group)` argument order):

- Fixture 1 (`MCAR_inconsistent`): `target_column = [1.0, None, 2.0, None,
  3.0, None, 4.0, None, 5.0, None]`, `probe_column = [20.1, 9.1, 19.9, 8.9,
  20.0, 9.0, 20.2, 9.2, 19.8, 8.8]` → `t_statistic = -110.0000000000002`,
  `p_value = 5.2124653934461314e-14` (matches `TEST-AIDS-415`).
- Fixture 2 (`MCAR_consistent`): `target_column = [1.0, None, 2.0, 3.0,
  None, 4.0]`, `probe_column = [10.0, 9.95, 9.9, 10.05, 10.0, 9.95]` →
  `t_statistic = 0.0`, `p_value = 1.0` (matches `TEST-AIDS-416`).

## Changes

- `.musubix/features/ai-data-scientist/requirements.md`: REQ-AIDS-110's
  Statement clarified to name the `ttest_ind(missing_group, observed_group)`
  argument order explicitly (previously implicit/unstated); Acceptance
  section's two fixtures replaced with the empirically-verified values
  above, matching the already-correct tests exactly.
- `.musubix/features/ai-data-scientist/design.md`: DES-AIDS-110's
  Responsibilities clause updated to name the same explicit
  `ttest_ind(missing_group, observed_group)` argument order, matching the
  requirements.md Statement clarification above. No interface, constraint,
  or behavior changed.
- `src/ai_data_scientist/missing_data_analysis.py`: module docstring's
  "Known issue... tracked as GitHub #84" note removed (the mismatch it
  described no longer exists) and `Change:` footer updated to reference
  CHANGE-040; one clarifying word added to match the Statement's now-
  explicit argument-order phrasing. No functional code changed.
- `tests/test_missing_data_analysis.py`: `TEST-AIDS-415`'s comment updated
  (no longer describes a now-resolved discrepancy); `TEST-AIDS-416` gained
  an exact `p_value == pytest.approx(1.0, abs=1e-6)` assertion (previously
  only asserted the qualitative `>= 0.05` threshold), now asserting the
  precise Acceptance-specified value in addition to the threshold.

## Rubber-duck review

A `rubber-duck` review of the edited Acceptance text, implementation
docstring, and test file found 4 issues, all fixed:
1. Stale "Known issue... GitHub #84" docstring/test-comment text that no
   longer reflected reality — removed/updated.
2. The Statement did not specify `ttest_ind`'s argument order, yet the
   Acceptance text implied a signed `t_statistic` depends on it — Statement
   now states the order explicitly.
3. `TEST-AIDS-416` asserted only `p_value >= 0.05`, not the exact Acceptance
   value `1.0` — exact assertion added.
4. Minor Acceptance-sentence wording ambiguity (`p_value = 1.0 >= 0.05`
   read as a chained comparison) — reworded to
   "`p_value = 1.0` (and therefore `p_value >= 0.05`)".

A re-review confirmed all 4 fixed, 0 remaining issues.

## Test evidence

Full suite: 859/859 passing, 0 regressions (identical count to CHANGE-039's
final state — this change adds no new tests, since no new behavior is
introduced; `TEST-AIDS-415`/`416` are strengthened, not added).

## Residual risks

- `approval record release` is expected to hard-fail on unrelated
  pre-existing repo-wide debt (`workflow`/`tdd`/`change-history`/
  `change-completeness`/`command:test`/`model-correspondence`/`commands`/
  `constitution:RULE-002` checks each still carry pre-existing failures
  unrelated to this change), identical to the precedent at CHANGE-033
  through CHANGE-039. The user's explicit `ask_user` approval (artifact
  hash + file paths presented) is treated as the authoritative release
  approval for this change.
- `WORKFLOW_INVOCATION_UNVERIFIED`-class mid-session limitation (GitHub
  #63): documented, non-blocking, same precedent as CHANGE-013/018/
  CHANGE-033 through CHANGE-039.
- This is a documentation/specification-only correction (no behavior
  change, no new test; implementation gained one clarifying comment only).
  Recording its change phases via musubix3's fingerprint-based CLI required
  3 waivers (`CHANGE_RED_UNPROVEN`/`CHANGE_GREEN_UNPROVEN`/
  `CHANGE_COMPLETENESS_TDD` for `REQ-AIDS-110`) — see Status below —
  identical to how documentation-only edits were handled in CHANGE-039.

## Status

Requirements and design approved by nahisaho via `ask_user`+
`approval record` (requirements hash
`70ba061509ea6ed9f2dc7bf434f53cd92170c8e402a1b9d07d74205a694dc1e5`, design
hash `47b64718fd0b10be0f1164eaefdd75a9041ee98b7a9685d1121c6099455f2a92`).
`npx musubix3 change-record CHANGE-040 {impact,requirements,design,red,
implementation,green,quality} --requirement REQ-AIDS-110` all recorded
successfully (`requirements` used `--allow-unchanged`, documented by the
CLI itself as intended for "defect fixes only," which this is).
`trace build`/`trace check --strict`/`graph index`/`graph gate` all pass
with 0 diagnostics. Full suite: 859/859 passing, 0 regressions (identical
to CHANGE-039's final count; no behavior changed, so no test count
changed). 3 waivers recorded (`CHANGE_RED_UNPROVEN`/`CHANGE_GREEN_UNPROVEN`/
`CHANGE_COMPLETENESS_TDD` for `REQ-AIDS-110`), downgrading those 3
diagnostics from error to warning — the identical musubix3 fingerprint-
recording-order quirk already accepted at CHANGE-029 through CHANGE-039
(this CLI has no representation for "tests already passed before this
change's own Red/Green phases were recorded").

`gate --changed --json` after waivers: `workflow`/`tdd`/`change-history`/
`change-completeness`/`approval` still show `fail` overall, but 0 of their
diagnostics reference `CHANGE-040` at `error` severity — confirmed by
filtering the gate JSON for `CHANGE-040`-tagged error diagnostics (zero
found). These are the same unrelated, pre-existing, repo-wide failures
already disclosed and accepted at CHANGE-033 through CHANGE-039.

Residual risks (same as disclosed above): `approval record release`
hard-fails on unrelated pre-existing repo-wide debt (identical to
CHANGE-033–039's precedent); `WORKFLOW_INVOCATION_UNVERIFIED` (GitHub #63,
non-blocking, same precedent as CHANGE-013/018/033–039).

A second rubber-duck review of this CHANGE-040 document (after the
Status section above was drafted) found 3 non-blocking wording issues
(Changes section omitting the design.md edit; Summary inaccurately
calling the Statement "unchanged"; Residual risks using stale prospective
waiver language). All 3 were fixed; a follow-up rubber-duck pass
confirmed 0 remaining issues.

Release approved by nahisaho via `ask_user`. `musubix3 approval record
release` itself hard-fails on unrelated pre-existing repo-wide debt
(identical reasons/precedent as CHANGE-033 through CHANGE-039); the
explicit human `ask_user` approval is the authoritative release approval
for this change.

Change complete. Fixes #84.
