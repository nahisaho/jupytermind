# CHANGE-037: convergence_guard surfaces secondary-metric regression at declared convergence (fixes #80)

## Summary

GitHub Issue #80 reports that `ai_data_scientist.convergence_guard.evaluate_convergence()`
evaluates convergence against a single scalar primary metric per round (e.g.
`accuracy`). For imbalanced-classification tasks, a round-over-round pipeline
can report `"converged"` on `accuracy` while a secondary metric that matters
more for the task (e.g. `recall` on the minority class) has meaningfully
regressed between rounds, with nothing in the guard's verdict surfacing this.

Reproduced on a real Kaggle run (`arashnic/imbalanced-data-practice`,
~17% positive rate): accuracy stabilized within `rel_tol=0.02` across rounds
4-5, so the guard declared `"converged"`, while recall fell from its round-2
peak of `0.7844` (achieved with `class_weight='balanced'`) to `0.6232` at the
final round 5 — a ~20% relative regression — with no signal in the verdict.

This change adds `REQ-AIDS-102`/`DES-AIDS-102`: an additive, opt-in
`secondary_metrics`/`secondary_rel_tol` parameter pair on
`evaluate_convergence()`. When the base classification would be `"converged"`
and at least one requested secondary metric's peak-to-final value has
regressed by more than `secondary_rel_tol` on a relative basis, the status is
upgraded to `"converged_with_secondary_regression"` and the regressed metric
names are listed in a new `ConvergenceVerdict.secondary_regressions` field.
Existing callers that do not pass `secondary_metrics` see zero behavior
change.

## Scope

- Feature: `ai-data-scientist`
- Change type: feature extension (new requirement + design + implementation)
- Worktree: `/home/nahisaho/GitHub/jupytermind-change037`
- Branch: `change-037-convergence-guard-secondary-metric`
- GitHub Issue: #80

Touched artifacts:

- `.musubix/features/ai-data-scientist/requirements.md` — new `REQ-AIDS-102`;
  one non-behavioral clarification to `REQ-AIDS-098`'s Acceptance text (the
  "exactly 3 fields" phrasing updated to explicitly permit REQ-AIDS-102's
  additive field; no behavior change, no fresh TDD required for REQ-AIDS-098)
- `.musubix/features/ai-data-scientist/design.md` — new `DES-AIDS-102`
- `src/ai_data_scientist/convergence_guard.py` — `Round` gains
  `secondary_metrics`; `ConvergenceVerdict` gains `secondary_regressions`;
  `evaluate_convergence` gains `secondary_metrics`/`secondary_rel_tol`
  parameters and the peak-vs-final regression check
- `tests/test_convergence_guard.py` — new regression tests covering
  `REQ-AIDS-102`'s scenarios

## Affected Requirements

Requirements: REQ-AIDS-102

(REQ-AIDS-098's text was clarified but its statement/acceptance obligations
are unchanged in substance — documented above, no fresh Red/Green required
for it.)

## Design

DES-AIDS-102 (see design.md).

## Implementation Plan

- [x] Requirements approved (`REQ-AIDS-102`)
- [x] Design approved (`DES-AIDS-102`)
- [x] Regression tests written (`TEST-AIDS-361`-`365`)
- [x] Red recorded (`musubix3 tdd red`, all 5 tests)
- [x] Implementation (`CODE-AIDS-156`, plus `CODE-AIDS-151` annotation
      extended to cover `REQ-AIDS-102`/`DES-AIDS-102`)
- [x] Green recorded (`musubix3 tdd green`, all 5 tests)
- [x] Quality evidence recorded
- [x] Release approval obtained (human approval via `ask_user`; automated
      `approval record release` hard-fails on unrelated pre-existing
      repo-wide debt, see Residual risk)
- [ ] Commit (`Fixes #80`), push, merge

## Quality Evidence

- Tests: 5 new regression tests added to `tests/test_convergence_guard.py`:
  - `TEST-AIDS-361` — Issue #80 reproduction (recall peaks round 2, regresses
    by round 5 while accuracy has converged) upgrades status to
    `"converged_with_secondary_regression"` and lists `"recall"`.
  - `TEST-AIDS-362` — omitting `secondary_metrics` is fully behavior-identical
    to pre-change `REQ-AIDS-098` semantics.
  - `TEST-AIDS-363` — a secondary metric with no meaningful regression stays
    `"converged"` with empty `secondary_regressions`.
  - `TEST-AIDS-364` — 3 sub-checks confirming the regression check never
    upgrades `"repetition_detected"`, `"exhausted"`, or `"continue"` statuses.
  - `TEST-AIDS-365` — key-only lookup correctly resolves a metric name that
    collides with a dict method (`"items"`), excludes a `NaN` round value
    from peak/final consideration, and treats a custom `Mapping` whose
    `__getitem__` raises as absent rather than propagating.
  - Full suite: 697 passed, 0 failed (692 pre-existing + 5 new).
- Lint: `ruff format --check` and `ruff check` on the two touched files show
  only 2 pre-existing, unrelated findings (`BLE001` on `_resolve_field`'s
  outer exception guard at line 91, `SIM102` on the existing duplicate-scan
  loop at line 238) — both already present before this change, confirmed via
  `git show HEAD:... | ruff check`. New code (`_resolve_secondary_value`,
  `_is_present_numeric`, the regression-check block) is fully clean; its one
  intentional blind-exception catch carries a `# noqa: BLE001` justification
  matching repo convention.
- Trace-scanner bug discovered and fixed: a pre-existing stray apostrophe at
  line 105 of `tests/test_convergence_guard.py` ("round 2's duplicate-looking
  name") was silently masking musubix3's `maskGenericStrings()` quote-balance
  scanner from that point to EOF, hiding `TEST-AIDS-322` through `330` (9
  pre-existing tests, unrelated to this change) and all 5 new
  `TEST-AIDS-361`-`365` annotations from `trace build`/`tdd red` with zero
  diagnostics emitted. Root-caused by direct Node.js inspection of musubix3's
  compiled `trace.js`. Fixed by removing the apostrophe (and two similar ones
  introduced in this change's own new test comments). `trace build` now
  reports `1317 nodes, 1892 edges, 0 diagnostics`; `trace check --strict`:
  PASS. This is a musubix3 parser limitation, not a defect in this repo's own
  code; stored as a repository-scoped memory to prevent recurrence.
- `graph index`/`graph gate`: PASS (224 files, 1343 imports, 1433 symbols).
- `gate --changed --json`: after waivers (below), only the pre-existing,
  unrelated repo-wide `workflow`/`tdd`/`change-history`/`change-completeness`
  checks remain `fail` (same CHANGE-001/005/019/020/026 debt seen in every
  prior CHANGE in this series); no new unwaived error-severity diagnostic
  is attributable to CHANGE-037 except `CHANGE_COMPLETENESS_ADR` (expected,
  see Residual risk).
- Waivers recorded (scoped to `REQ-AIDS-102`, approver `nahisaho`):
  `CHANGE_RED_UNPROVEN`, `CHANGE_GREEN_UNPROVEN`, `CHANGE_COMPLETENESS_TDD` —
  all three downgraded from `error` to `warning` after recording; the
  change-history/completeness scanners require a specific JSON evidence
  shape that the native `tdd red`/`tdd green` recordings (used here, as in
  CHANGE-033/034/035/036) do not produce, which is why these diagnostics
  fire despite genuine, verified Red/Green evidence existing in
  `.musubix/evidence/native/test/TEST-AIDS-36{1..5}.json`.

## Residual risk

- `CHANGE_COMPLETENESS_ADR` remains an unwaived `error` for
  `CHANGE-037:REQ-AIDS-102` — this code is not a waivable gate (confirmed in
  prior CHANGEs). No ADR was written because DES-AIDS-102 is a bounded,
  additive extension reusing an existing documented algorithm
  (`_relative_change`), not an architectural tradeoff; this matches the
  identical unwaived pattern already accepted at `CHANGE-026:REQ-AIDS-044`,
  `CHANGE-035:REQ-AIDS-100`, and `CHANGE-036:REQ-AIDS-101`.
- `secondary_metrics`/`secondary_rel_tol` is a heuristic peak-vs-final
  comparison, scoped only to the base `"converged"` status, as specified in
  REQ-AIDS-102; it does not attempt to detect secondary-metric regressions
  within `"repetition_detected"`/`"exhausted"`/`"continue"` verdicts (by
  design, matching REQ-AIDS-102's explicit scoping and verified by
  `TEST-AIDS-364`).
- `approval record release` hard-fails on unrelated pre-existing repo-wide
  debt (`workflow`, `tdd`, `change-history`, `change-completeness`,
  `input-stability` checks), identical to the precedent at
  CHANGE-033/034/035/036. The user's explicit approval via `ask_user`
  (exact file paths + quality evidence + residual risks presented) is
  treated as the authoritative release approval for this change.

## Status

Implementation, tests, and waivable quality gates complete. One gate
(`CHANGE_COMPLETENESS_ADR`) remains an unwaived, documented residual risk by
design (see Residual risk) — consistent with the identical accepted pattern
at CHANGE-026/035/036. Release approved via explicit human `ask_user`
approval (see Residual risk); automated `approval record release` is
expected to hard-fail on unrelated pre-existing repo-wide debt per the same
precedent. Ready for commit/merge on that basis.
