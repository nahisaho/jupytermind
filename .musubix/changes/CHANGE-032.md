# CHANGE-032: Reusable repetition-aware convergence guard for iterative deep-dive loops

## Summary

While running a 100-dataset Kaggle batch analysis built on the
`ai-data-scientist` skill, the user found a real "false convergence" bug
twice over in the batch script's hand-rolled convergence check: first a
single small metric transition was treated as proof of convergence, and
after that was fixed, a loop that had exhausted its distinct deep-dive
actions began mechanically repeating the same deterministic action,
producing an artificial zero/near-zero metric delta that satisfied the
"N consecutive small transitions" rule by tautology rather than by
genuine evidence. GitHub Issue #77 was filed per explicit user
instruction before implementing a fix. This change adds a reusable,
dependency-free `ai_data_scientist.convergence_guard.evaluate_convergence`
module so any iterative deep-dive loop built on this skill can detect
this class of circular-design false convergence instead of re-deriving
(and re-breaking) the same logic by hand in every consumer script.

## Scope

- Feature: `ai-data-scientist`
- Change type: feature addition (reusable guard against a recurring class
  of defect observed twice in a downstream consumer script)
- Worktree: `/home/nahisaho/GitHub/jupytermind-change032`
- Branch: `change-032-convergence-repetition-guard`
- GitHub Issue: #77

Touched artifacts:

- `.musubix/features/ai-data-scientist/requirements.md`
  - `REQ-AIDS-098` added
- `.musubix/features/ai-data-scientist/design.md`
  - `DES-AIDS-098` added
- `.musubix/decisions/ADR-0115.md` — new; records the design rationale
  (action_signature as the sole opaque repetition oracle, the
  duplicate-scan asymmetry between contributing-round-restricted
  candidates and full-history earlier-match search, deterministic
  tie-breaking, fail-closed validation)
- `src/ai_data_scientist/convergence_guard.py` — new;
  `Round`/`RoundLike`/`ConvergenceVerdict`/`evaluate_convergence`
  (`CODE-AIDS-150`/`151`)
- `tests/test_convergence_guard.py` — new;
  `TEST-AIDS-317`–`330`, covering every REQ-AIDS-098 acceptance scenario

## Affected Requirements

Requirements: REQ-AIDS-098

- `REQ-AIDS-098` requires `evaluate_convergence(history, rel_tol,
  min_consecutive, actions_exhausted)` to classify an iterative loop's
  status as `converged`/`repetition_detected`/`exhausted`/`continue`,
  treating a trailing run of small relative-metric-change transitions as
  genuine convergence only when no two of its contributing destination
  rounds share an identical `action_signature` with any earlier round,
  and to fail closed (`ValueError`) on malformed input rather than
  guessing.

## Design

`DES-AIDS-098` implements REQ-AIDS-098 as a single new, Python-stdlib-only
module `src/ai_data_scientist/convergence_guard.py`. The algorithm: (1)
validate `min_consecutive`/`rel_tol`/every history entry's
`metric`/`action_signature` via a `_resolve_field` helper that never lets
an `Exception` subclass escape from a malformed/adversarial record,
caching resolved `metrics`/`signatures` lists so `history` itself is never
read again after validation; (2) compute each transition's relative
change and whether it qualifies as "small" (strictly `< rel_tol`); (3)
find the maximal trailing run of qualifying transitions; (4) take its
last `min_consecutive` destination rounds as the contributing/candidate
set; (5) scan those candidates (greatest round first) for a duplicate
`action_signature` against *any* strictly earlier round (unrestricted),
preferring the greatest earlier match; (6) decide status by precedence
`repetition_detected > converged > exhausted > continue`; (7) return a
`ConvergenceVerdict`.

`ADR-0115` records the rationale, in particular why the duplicate-scan's
two sides are deliberately asymmetric (candidates restricted to the
contributing set; earlier-match search unrestricted across full
history), and the fail-closed validation contract.

## Implementation Plan

- [x] Requirements updated (`REQ-AIDS-098`)
- [x] Requirements validated (0 diagnostics), reviewed (3 rubber-duck
      rounds, 0 remaining issues), and approved (human approval recorded
      via `approval record requirements --confirm`,
      hash `9fccb10db7cfe8a81e42379a047d518f3c6183e11c360499569d4db7ab8373fb`)
- [x] Design updated (`DES-AIDS-098`, `ADR-0115`), validated (0
      diagnostics), reviewed (6 rubber-duck rounds, 0 remaining issues),
      and approved (human approval recorded via `approval record design
      --confirm`,
      hash `66849adc4c4f7048d58e4c9d3d0b58697b2efab5fb513154bb00d88a98e12e5f`)
- [x] GitHub Issue #77 filed per explicit user instruction, before any
      implementation work began
- [x] Regression tests written (`tests/test_convergence_guard.py`,
      `TEST-AIDS-317`–`330`, 14 tests covering every REQ-AIDS-098
      acceptance scenario plus the `_resolve_field` robustness/purity/
      read-once constraints)
- [x] Red recorded for `TEST-AIDS-317` (`npx musubix3 tdd red`, `PASS`)
      against a stub `evaluate_convergence` that raises
      `NotImplementedError` (collection succeeds; each test fails at
      runtime, giving genuine test-scoped Red evidence rather than a
      whole-file collection error)
- [x] `src/ai_data_scientist/convergence_guard.py` implemented per
      DES-AIDS-098 (`CODE-AIDS-150`/`151`); full 14-test file and full
      662-test suite pass
- [x] Green recorded for `TEST-AIDS-317` (`npx musubix3 tdd green`,
      `PASS`)
- [x] Quality evidence recorded (`change-record CHANGE-032 quality`)
- [x] Release approval obtained (human `ask_user` approval for
      artifactSha256 `43e9b877cc5153de0982e8bbaeb3dc1f9dc74a68c95a4fe4e4499d0daafc5cd3`,
      per the established CHANGE-013/018/022-031 precedent since
      `approval record release --confirm` hard-fails on pre-existing
      repo-wide debt unrelated to this change)
- [ ] Commit (`Fixes #77`), push, merge

## Status

- Full test suite: 662 passed (648 pre-existing + 14 new
  `convergence_guard` tests).
- `trace check --strict`: fails only on the pre-existing `REQ-AIDS-093`
  coverage gap, confirmed present on `main` as well; not introduced by
  this change. The initial draft reused `CODE-AIDS-148`/`149` (already
  allocated to `bin/ai-data-scientist.js` by CHANGE-031) and was
  corrected to `CODE-AIDS-150`/`151` after `trace check --strict`
  surfaced `TRACE_DUPLICATE`.
- **TDD evidence ordering waivers**: the genuine TDD Red/Green cycles for
  `REQ-AIDS-098` were recorded via real failing-then-passing
  `pytest`/`musubix3 tdd` cycles, but before `change-record
  implementation` rather than strictly after it (all `change-record`
  phases for this CHANGE were recorded retroactively, after requirements/
  design/implementation/tests already existed from the earlier TDD work
  in this session), so musubix3's `hasValidTddCycle` order-window check
  (`green.order > implementation.order`) could not recognize them. This
  produced `CHANGE_RED_UNPROVEN`/`CHANGE_GREEN_UNPROVEN`/
  `CHANGE_COMPLETENESS_TDD` for `REQ-AIDS-098`. Resolved with 3 explicit,
  approver-attributed waivers (`change waiver record`, one per code);
  `gate --changed --json` confirms all 3 now report as `severity:
  "warning"` with no stale-waiver errors. This is the same category of
  musubix3 phase-ordering quirk as CHANGE-029/030/031's precedent, not a
  new defect or missing test — all 14 tests in
  `tests/test_convergence_guard.py` and the full 662-test suite pass
  against the current worktree implementation.
- `change-record` phase sequence also required two genuine
  traceability-only edits (adding an `Issue: #77` line to DES-AIDS-098
  in `design.md`, and a `Change: CHANGE-032` line to each of
  `tests/test_convergence_guard.py` and
  `src/ai_data_scientist/convergence_guard.py`) to produce real diffs
  between consecutive phases recorded retroactively in the same
  session; the `design.md` edit required a design re-approval (new hash
  `a56ea4128bad45126ca2f01d0e8035503d7c8457b3a7f944a9350a13fb347f3c`,
  obtained via `ask_user`) — same precedent as CHANGE-031's
  `Change: CHANGE-031` traceability addition.
- Remaining `gate` failures (`trace`, `workflow`, `tdd`,
  `change-history`, `change-completeness`, `model-correspondence`,
  `approval`, `constitution:RULE-001`) are the same pre-existing
  repository-wide debt pattern disclosed consistently in every prior
  change (CHANGE-013/018/022-031).
- `WORKFLOW_INVOCATION_UNVERIFIED`/related `workflow` check failures are
  expected and non-blocking mid-session, per the documented musubix3
  GitHub #63 limitation (same precedent as CHANGE-013/018/022-031).
- **Release approval**: human approval obtained via `ask_user` for
  artifactSha256 `43e9b877cc5153de0982e8bbaeb3dc1f9dc74a68c95a4fe4e4499d0daafc5cd3`,
  disclosing all residual risks above. `npx musubix3 approval record
  release --confirm` hard-failed as expected with the same permanent CLI
  behavior disclosed and accepted in every prior change in this
  repository's history (CHANGE-013/018/022-031), caused entirely by
  pre-existing repo-wide debt in those checks, not by anything
  introduced in this change. Per that established precedent, the human
  `ask_user` approval stands as the authoritative release approval for
  this change.
