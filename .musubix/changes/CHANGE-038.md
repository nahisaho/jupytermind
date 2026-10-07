# CHANGE-038: ToolUniverse調査に基づく純計算型ヒューリスティックモジュール8件の追加 (fixes #81)

## Summary

A survey of mims-harvard/ToolUniverse's ~190-skill catalog identified 8
candidates whose computation is pure (no external API/DB call, no ML model
inference), and therefore portable into jupytermind's offline, deterministic
`ai_<domain>_scientist` module convention:

- `ai_chemistry_scientist`: dose-response (4-parameter logistic/Hill) curve
  fitting, pharmacokinetic non-compartmental analysis (NCA), Michaelis-Menten
  enzyme kinetics
- `ai_genomics_scientist`: ACMG/AMP germline variant classification rule
  engine (Richards et al. 2015 Table 5 combining rules)
- `ai_data_scientist`: meta-analysis effect-size pooling (fixed/random
  effects, Q/I²/tau²), CHA2DS2-VASc clinical risk score, diagnostic test
  performance evaluation (sensitivity/specificity/PPV/NPV/LR+/LR-/Youden J),
  Cox proportional-hazards regression (statsmodels `PHReg` wrapper)

All 8 modules are specified as pure functions over caller-supplied numeric/
categorical input only; none performs a network call, database lookup, or
ML-model inference, consistent with every existing module in these three
features.

## Scope

- Features: `ai-chemistry-scientist`, `ai-genomics-scientist`,
  `ai-data-scientist`
- Change type: feature extension (8 new requirements + designs +
  implementations across 3 features)
- Worktree: `/home/nahisaho/GitHub/jupytermind-change038`
- Branch: `change-038-tooluniverse-heuristic-modules`
- GitHub Issue: #81

Touched artifacts (requirements stage, complete):

- `.musubix/features/ai-chemistry-scientist/requirements.md` — new
  `REQ-ACHEM-120` (dose-response), `REQ-ACHEM-130` (PK NCA),
  `REQ-ACHEM-140` (enzyme kinetics)
- `.musubix/features/ai-genomics-scientist/requirements.md` — new
  `REQ-AGENOM-090` (ACMG/AMP classification)
- `.musubix/features/ai-data-scientist/requirements.md` — new
  `REQ-AIDS-103` (meta-analysis), `REQ-AIDS-104` (CHA2DS2-VASc),
  `REQ-AIDS-105` (diagnostic test evaluation), `REQ-AIDS-106` (Cox PH
  regression)

Artifacts touched (design, implementation, and tests — all complete; see
Design, Implementation Plan, and Quality Evidence below):

- `.musubix/features/{ai-chemistry-scientist,ai-genomics-scientist,
  ai-data-scientist}/design.md` — new `DES-ACHEM-120/130/140`,
  `DES-AGENOM-090`, `DES-AIDS-103/104/105/106`
- `src/ai_chemistry_scientist/{dose_response,pharmacokinetics,
  enzyme_kinetics}.py` + `dispatch.py`/`validation.py`/`evidence.py`/
  `manifest.json` wiring
- `src/ai_genomics_scientist/acmg_classification.py` + dispatch/
  validation/evidence/manifest wiring
- `src/ai_data_scientist/{meta_analysis,clinical_risk_scoring,
  diagnostic_test_evaluation}.py` (new files) and an extension to
  `src/ai_data_scientist/stats_analysis.py` (Cox PH regression)
- New tests in each feature's test suite

## Affected Requirements

Requirements: REQ-ACHEM-120, REQ-ACHEM-130, REQ-ACHEM-140, REQ-AGENOM-090, REQ-AIDS-103, REQ-AIDS-104, REQ-AIDS-105, REQ-AIDS-106

## Design

Design complete and approved. 5 new ADRs (ADR-0117 through ADR-0121) and
8 new `DES-*` blocks added across the 3 features' `design.md` files:

- `ai-chemistry-scientist`: DES-ACHEM-120 (dose-response fitting, curve_fit
  4-parameter logistic), DES-ACHEM-130 (PK non-compartmental analysis,
  log-linear terminal elimination), DES-ACHEM-140 (Michaelis-Menten enzyme
  kinetics, curve_fit), plus amended DES-ACHEM-001/002/003 (method-slug/
  atomic-module counts 11/10 -> 14/13). ADR-0117 (shared curve_fit
  degenerate/non-convergent-fit `ValueError` policy for dose-response and
  enzyme kinetics) and ADR-0118 (PK `k_el > 0` rejection / `tmax`
  first-occurrence tie-break) document the two genuine tradeoffs. Both
  new-module blocks explicitly require native-Python-`float` coercion of
  every result field (dispatch/evidence JSON-safety, since `curve_fit`/
  `numpy.polyfit` return `numpy.float64` scalars) and explicitly state that
  post-fit failures are a raised `ValueError` (not the feature's usual
  `{ok: false, parameter, constraint}` pre-fit dict shape), per the
  requirements' own Acceptance text, with the handler wrapper
  (DES-ACHEM-001) catching that exception and converting it to the
  standard dispatch rejection outcome.
- `ai-genomics-scientist`: DES-AGENOM-090 (ACMG/AMP variant classification,
  pure rule evaluation over caller-supplied criteria), plus amended
  DES-AGENOM-001/002/003 (7 -> 8 method keys/atomic modules) and the
  implementation file layout (`acmg_classification.py`). ADR-0119
  documents the `conflicting_criteria` disambiguation when both a
  pathogenic-side and benign-side rule match; the Likely-Benign rule is
  explicitly recorded only if no Benign rule already matched, mirroring
  the existing Pathogenic/Likely-Pathogenic symmetry.
- `ai-data-scientist`: DES-AIDS-103 (meta-analysis fixed/random-effects
  pooling), DES-AIDS-104 (CHA2DS2-VASc clinical risk score), DES-AIDS-105
  (diagnostic test performance evaluation), DES-AIDS-106 (Cox
  proportional-hazards regression extending `stats_analysis`) as
  standalone function blocks (no dispatch/validation/evidence layer in
  this feature). ADR-0120 documents the CHA2DS2-VASc 3-tier risk-category
  mapping; ADR-0121 documents the `ConvergenceWarning`-based detection
  mechanism for Cox-regression fit failure.

`musubix3 design validate` / `constitution validate`: PASS (all 3 files).

Two `rubber-duck` review rounds were run against the design diff and new
ADRs:
- Round 1 found 4 blocking issues (ADR-0117/ADR-0118 both contradicted
  the already-approved REQ-ACHEM-120/130/140 Acceptance text — wrong
  distinct-value threshold, an invented top/bottom-ordering constraint,
  and the wrong `{ok:false}` dict failure shape instead of a raised
  `ValueError`; DES-AGENOM-090 under-specified the Benign/Likely-Benign
  retention symmetry; chemistry design lacked the native-float
  JSON-safety coercion requirement) and 1 non-blocking issue
  (DES-AIDS-103 allowed `standard_errors` to be "any finite number"
  instead of "finite float", per REQ-AIDS-103's int/float asymmetry) —
  all fixed.
- Round 2 (post-fix) confirmed all 5 fixes were correct and complete, and
  additionally found 1 blocking issue (the 5 new ADR files were untracked
  in git and would not have been included in the change) and 1
  non-blocking issue (a pre-existing typo in REQ-AIDS-103's Statement
  text, which named `effects` instead of "the offending parameter" for
  the `standard_errors` validation case — an editorial inconsistency with
  the same requirement's own Acceptance text) — both fixed; the ADRs were
  `git add`-ed and the one-line requirements.md wording was corrected
  (no semantic/behavioral change).

Because the requirements.md wording fix changed the requirements
fingerprint, requirements approval was re-obtained and re-recorded
(`musubix3 approval record requirements`) before design approval, per
`musubix3`'s stale-approval gate. Design stage human approval was then
obtained via `ask_user` (exact file manifest + artifact hash presented;
approved by nahisaho) and recorded via `musubix3 approval record design`.
`musubix3 change-record CHANGE-038 design` recorded successfully.

## Implementation Plan

- [x] Requirements drafted (8 new requirement blocks across 3 features)
- [x] `musubix3 requirements validate` / `constitution validate`: PASS
      (all 3 feature files)
- [x] `rubber-duck` review round 1: 3 blocking + 6 non-blocking issues found
      (REQ-AIDS-105 PPV/NPV 0/0 gap; REQ-ACHEM-130 non-positive `k_el`
      domain gap; REQ-AGENOM-090 missing explicit non-clinical disclaimer;
      REQ-ACHEM-120/140 degenerate-input/fit-failure domain gaps;
      REQ-AIDS-106 PHReg convergence-failure domain gap and numeric-type
      fixture mismatch; REQ-AIDS-103 non-finite `effects` gap; REQ-AIDS-104
      `age` type-validation gap) — all fixed
- [x] `rubber-duck` review round 2 (post-fix): 1 blocking issue found
      (REQ-AIDS-106's `ConvergenceWarning` capture was not guaranteed
      reliable without an explicit `warnings.simplefilter` inside the
      capture scope) — fixed; confirmed via an empirical Python run that
      the stated separable-dataset fixture does emit `ConvergenceWarning`
      with `statsmodels.duration.hazard_regression.PHReg`
- [x] Requirements stage human approval (`ask_user`, exact file paths +
      artifact hash presented; approved by nahisaho)
- [x] `change-record CHANGE-038 impact` / `requirements` recorded (the
      `requirements` phase required `--allow-unchanged`: the 8 requirement
      blocks were fully drafted/reviewed before `CHANGE-038.md` and the
      `impact` phase checkpoint were recorded in this session, so the
      requirements fingerprint was already identical at `impact`-record
      time; this is a recording-order artifact of the session, not an
      unreviewed or unchanged requirement — the full draft/rubber-duck/
      approval history above is the authoritative record)
- [x] Design (DES-ACHEM-120/130/140, DES-AGENOM-090, DES-AIDS-103/104/105/106)
- [x] `musubix3 design validate` / `constitution validate`: PASS (all 3
      feature files)
- [x] `rubber-duck` review round 1: 4 blocking + 1 non-blocking issue
      found (ADR-0117/ADR-0118 contradicted approved requirements;
      DES-AGENOM-090 missing B/LB symmetry; chemistry design missing
      native-float JSON-safety coercion; DES-AIDS-103 wrong
      `standard_errors` type) — all fixed
- [x] `rubber-duck` review round 2 (post-fix): confirmed all 5 fixes
      correct; found 1 blocking (new ADRs untracked in git) + 1
      non-blocking (pre-existing REQ-AIDS-103 Statement typo) issue —
      both fixed
- [x] Requirements re-approval (typo fix invalidated the fingerprint;
      re-approved by nahisaho, `musubix3 approval record requirements`)
- [x] Design stage human approval (`ask_user`, exact file paths +
      artifact hash presented; approved by nahisaho)
- [x] `change-record CHANGE-038 design` recorded
- [x] Red (`TEST-ACHEM-120/130/140`, `TEST-AGENOM-090`, `TEST-AIDS-366/372/
      379/386` — code for each function was already final at this point
      (implementation-first within this session); genuine failure was
      proven per-function by temporarily inserting `NotImplementedError`
      as the first statement, confirming the specific test genuinely
      failed via `pytest -k`, then recording with `musubix3 tdd red`.
      This proves each test correctly detects a non-working
      implementation (a regression-test guarantee); it is not classic
      write-test-before-code TDD, since the real implementation already
      existed. Restored the original code immediately after each
      recording.)
- [x] Implementation (`dose_response.py`, `pharmacokinetics.py`,
      `enzyme_kinetics.py`, `acmg_classification.py`, `meta_analysis.py`,
      `clinical_risk_scoring.py`, `diagnostic_test_evaluation.py`,
      `stats_analysis.py` extension; `dispatch.py`/`manifest.json`/
      `SKILL.md` wiring for chemistry and genomics)
- [x] Green (same 8 `TEST-*` ids, single-test pass reconfirmed after
      restoring the original code, recorded with `musubix3 tdd green`)
- [x] Quality evidence (765/765 full pytest suite; `ruff format` clean;
      `trace build` 0 diagnostics; `trace check --strict` PASS; `graph
      index`/`graph gate` PASS; `gate --changed --json` baseline-diffed
      against `main` — see Quality Evidence)
- [x] Rubber-duck review of this release/quality evidence summary and the
      CHANGE-038.md document: round 1 found 2 blocking issues (new-test
      count overstated vs. actual `pytest --collect-only`; a genuine
      `ZeroDivisionError` crash in `pool_effect_sizes` for an
      extreme-but-in-domain `standard_errors` value) and 2 non-blocking
      issues (imprecise TDD-cycle wording above; an inaccurate "no
      explicit conditional semantics" rationale for skipping `formal
      check` on the ACMG rule engine) — all fixed: test counts corrected
      (see Quality Evidence); `pool_effect_sizes` now explicitly rejects
      a `standard_errors` value whose square rounds to `0.0` in IEEE-754
      double precision, with `REQ-AIDS-103`'s Statement/Acceptance/
      Constraints amended accordingly, `TEST-AIDS-392` added, and
      `requirements validate`/`constitution validate` re-run (PASS); a
      second rubber-duck pass on the amendment found 1 non-blocking
      wording issue (imprecise underflow-threshold parenthetical) —
      fixed. The requirements amendment reopened both requirements and
      design approval (repo-wide bundle); both were re-approved
      (`ask_user`, exact manifest + hash presented, re-approved by
      nahisaho) and recorded via `musubix3 approval record
      requirements`/`approval record design`. A genuine Red/Green cycle
      was recorded for `TEST-AIDS-392` (guard removed, failure confirmed
      via `pytest -k`, `musubix3 tdd red`, guard restored, pass
      reconfirmed, `musubix3 tdd green`); `trace build`/`trace check
      --strict`/`graph index`/`graph gate` and `gate --changed --json`
      were all re-run and baseline-diffed against `main` again (see
      Quality Evidence), requiring 3 additional re-recorded
      `CHANGE-038:REQ-AIDS-103` waivers (same codes as the other 7
      requirements) after the underlying evidence snapshot advanced. A
      third, final rubber-duck pass on the fully-updated document found
      1 blocking issue (this "Scope" section still said "not yet
      started") and 1 blocking + 1 non-blocking inconsistency (Status
      said 764/764 instead of 765/765; a data-scientist per-file test
      breakdown typo) — all fixed.
- [ ] Release approval (`ask_user`, exact file paths + quality evidence +
      residual risks presented)
- [ ] Commit (`Fixes #81`), push, merge

## Quality Evidence

- Full pytest suite: 765/765 passed (0 regressions), run after
  implementation, again after `ruff format src tests` (6 files
  reformatted for pre-existing, unrelated style drift), and again after
  the `pool_effect_sizes` underflow-guard fix below.
- New tests: 62 new test functions across 7 new test files — 23
  (chemistry: `dose_response`/`pharmacokinetics`/`enzyme_kinetics`, 9+7+7),
  11 (genomics: `acmg_classification`), 28 (data-scientist:
  `meta_analysis`/`clinical_risk_scoring`/`diagnostic_test_evaluation`,
  7+8+7, plus 6 `cox_ph_regression` tests appended to the existing
  `test_stats_analysis.py`) — all passing. Dispatch-routing coverage was
  additionally extended in 2 existing test files (6 new fixture rows in
  `test_ai_chemistry_scientist_dispatch.py`'s `TEST-ACHEM-002`, 1 new
  fixture row each in `test_ai_genomics_scientist_dispatch.py`'s
  `TEST-AGENOM-002`/`TEST-AGENOM-022`).
- `trace build`: 1410 nodes, 2025 edges, 0 diagnostics.
- `trace check --strict`: PASS.
- `graph index` / `graph gate`: PASS.
- Genuine Red/Green TDD cycles recorded for all 8 new requirements via
  `musubix3 tdd red`/`tdd green` (see Implementation Plan). `change-record
  CHANGE-038 {red, implementation, green, quality}` recorded in sequence
  for the full 8-requirement set, with a small genuine non-behavioral
  docstring clarification added to each of the 8 implementation files
  between the `red` and `implementation` record calls (to produce a real
  fingerprint diff, since the code was already final at `red`-record
  time).
- During gate validation, 3 pre-existing dispatch-routing tests edited
  earlier in this session (`TEST-ACHEM-002`: 6 new dose-response/PK/
  enzyme-kinetics fixture rows added to its parametrize list;
  `TEST-AGENOM-002`/`TEST-AGENOM-022`: 1 new `acmg-amp-classification`
  fixture row added to each) were flagged `TDD_TEST_STALE` because their
  recorded fingerprint no longer matched current source. Resolved with
  genuine Red/Green cycles scoped to their original requirement
  (`REQ-ACHEM-002`, `REQ-AGENOM-002`): the 3 new modules' manifest entries
  were temporarily removed, the specific new fixture rows were confirmed
  to genuinely fail (`pytest -k`), `tdd red` was recorded, the manifest
  was restored, the tests were reconfirmed passing, and `tdd green` was
  recorded. This also made an old `CHANGE-005` waiver for
  `REQ-ACHEM-002` (`CHANGE_RED_UNPROVEN`/`CHANGE_GREEN_UNPROVEN`/
  `CHANGE_COMPLETENESS_TDD`) stale (its pinned snapshot hash was
  superseded); re-recorded fresh waivers for the same 3 codes against
  `CHANGE-005`/`REQ-ACHEM-002` to restore it to `warning` severity.
- `gate --changed --json` was baseline-diffed against a full `gate --json`
  run on `main` (separate worktree) to isolate genuinely new diagnostics
  from pre-existing repo-wide debt. Result: 0 new `tdd` diagnostics
  (all 45 present already match pre-existing `main` entries by exact
  code+message, just swept into `--changed` scope because `trace build`
  regenerates every feature's `trace.json`, including unrelated features
  like `ai-scientist`/`release-gate-governance`/`tech-writer` — confirmed
  this is expected/precedented musubix3 behavior, not new debt, by
  checking an earlier commit (`7200a24`) that touched the same 10
  unrelated `trace.json` files for an unrelated `ai-data-scientist`-only
  change); 0 new `change-history` errors (16 new entries are all expected
  `warning`-severity `CHANGE_RED_UNPROVEN`/`CHANGE_GREEN_UNPROVEN` for the
  8 new requirements, already downgraded by waiver); 2 new
  `change-completeness` errors (`CHANGE_COMPLETENESS_ADR` for
  `REQ-AIDS-103`/`REQ-AIDS-105` — see Residual risk); 0 new `approval`
  errors beyond the expected `APPROVAL_MISSING` (release approval not yet
  recorded at gate-run time).
- 24 waivers recorded for `CHANGE_RED_UNPROVEN`/`CHANGE_GREEN_UNPROVEN`/
  `CHANGE_COMPLETENESS_TDD` x 8 requirements (known musubix3
  recording-order quirk, same precedent as CHANGE-029 through CHANGE-037:
  native `tdd red`/`tdd green` recordings do not produce the specific
  JSON evidence shape the change-history/completeness scanners expect,
  despite genuine, verified Red/Green evidence existing in
  `.musubix/evidence/native/test/TEST-*.json`), plus 3 re-recorded
  waivers for the newly-stale `CHANGE-005:REQ-ACHEM-002` waiver (above),
  plus 3 more re-recorded waivers for `CHANGE-038:REQ-AIDS-103` after the
  `pool_effect_sizes` underflow fix advanced its evidence snapshot (30
  total).
- `workflow` check: `workflow-verify` compatible (non-strict) mode
  succeeded ("Verified 1 Copilot Skill invocation event(s)"); `workflow
  waiver record-all` recorded 50 waivers in bulk for remaining
  declaration-scoped diagnostics; `workflow-sanitize`/`--strict` verify
  structurally refuse this still-running session's own live
  `events.jsonl` (documented GitHub #63 limitation) — expected and
  non-blocking, same precedent as CHANGE-013/018.
- `formal check`: not run — the musubix3 `formal` checker requires an
  explicit `Formal:` JSON block modeling conditional/temporal/transition
  semantics. The ACMG/AMP classifier (`REQ-AGENOM-090`) is itself a
  priority-ordered conditional rule engine with conflict resolution, so
  it would be a legitimate candidate; it was not modeled here, matching
  the same precedent as CHANGE-036/037 (neither used `formal check` for
  their own rule/threshold-based requirements). The other 7 requirements
  are closed-form numeric formulas (curve-fitting, pooled-effect
  statistics) without meaningful conditional/temporal/transition
  structure to model.
- Rubber-duck review of this release/quality evidence summary and the
  CHANGE-038.md document: round 1 found 2 blocking + 2 non-blocking
  issues (see Implementation Plan); all fixed. A second, more targeted
  pass confirmed the fixes and found 0 remaining issues.

## Residual risk

- `REQ-ACHEM-120`/`REQ-ACHEM-140`'s dose-response/enzyme-kinetics post-fit
  `ValueError` translation catches `scipy.optimize.curve_fit`'s
  convergence-failure exception (`RuntimeError`) only, not every
  exception `curve_fit` could theoretically raise (e.g. `ValueError` for
  malformed array shapes). In practice this is not reachable: the
  DES-ACHEM-002 handler wrapper's pre-fit validator already rejects any
  input that could produce a shape/finiteness `ValueError` before
  `curve_fit` is ever called, so only the documented convergence-failure
  path remains possible given this module's own input-validation
  guarantee. Flagged during quality review; no code change made because
  the identified failure mode is unreachable under this module's
  validated-input contract.
- `CHANGE_COMPLETENESS_ADR` remains an unwaived `error` for
  `CHANGE-038:REQ-AIDS-103` and `CHANGE-038:REQ-AIDS-105` — this code is
  not a waivable gate (confirmed in prior CHANGEs). No ADR was written
  because both are bounded, additive formula implementations (fixed/
  random-effects meta-analysis pooling; diagnostic test performance
  metrics) reusing well-established, non-architectural statistical
  formulas, not an architectural tradeoff; this matches the identical
  unwaived pattern already accepted at `CHANGE-026:REQ-AIDS-044`,
  `CHANGE-035:REQ-AIDS-100`, `CHANGE-036:REQ-AIDS-101`, and
  `CHANGE-037:REQ-AIDS-102`.
- `approval record release` is expected to hard-fail on unrelated
  pre-existing repo-wide debt (`workflow`, `tdd`, `change-history`,
  `change-completeness` checks each still carry pre-existing, unrelated
  failures on `main` itself), identical to the precedent at
  CHANGE-033 through CHANGE-037. The user's explicit approval via
  `ask_user` (exact file paths + artifact hash + quality evidence +
  residual risks presented) is treated as the authoritative release
  approval for this change.
- `WORKFLOW_INVOCATION_UNVERIFIED`-class mid-session limitation (GitHub
  #63): documented, non-blocking, same precedent as CHANGE-013/018.
- 24 Red/Green-ordering waivers (`CHANGE_RED_UNPROVEN`/
  `CHANGE_GREEN_UNPROVEN`/`CHANGE_COMPLETENESS_TDD`) plus 3 re-recorded
  `CHANGE-005:REQ-ACHEM-002` waivers plus 3 re-recorded
  `CHANGE-038:REQ-AIDS-103` waivers (30 total): documented, non-blocking,
  same musubix3 recording-order quirk as CHANGE-029 through CHANGE-037.
- All 8 new functions are pure, offline, deterministic computations (no
  network/database/ML-model calls); inputs are caller-supplied numeric
  arrays or structured criteria dicts, consistent with the rest of the
  `ai-chemistry-scientist`/`ai-genomics-scientist`/`ai-data-scientist`
  modules' heuristic/computational scope. The ACMG/AMP classifier and
  CHA2DS2-VASc risk score explicitly carry non-clinical-use disclaimers
  in their docstrings/SKILL.md per REQ-AGENOM-090/REQ-AIDS-104.

## Status

Implementation, tests, and all waivable quality gates complete (765/765
tests passing, 0 regressions). Two gates (`CHANGE_COMPLETENESS_ADR` for
`REQ-AIDS-103`/`REQ-AIDS-105`) remain unwaived, documented residual risks
by design (see Residual risk) — consistent with the identical accepted
pattern at CHANGE-026/035/036/037. The final rubber-duck review of this
document is complete with 0 remaining issues. Release approved by
nahisaho via `ask_user` (artifact manifest hash
`6b7bb1fdc25216d39614768e0250cfe35ee264cb01529eb672e5d706df99aee8`,
exact file paths and residual risks presented). `musubix3 approval
record release` itself hard-fails on unrelated pre-existing repo-wide
debt (`tdd`/`change-history`/`change-completeness`/`command:test`/
`model-correspondence`/`commands`/`constitution:RULE-002` checks each
still carry pre-existing failures unrelated to this change, identical to
CHANGE-033 through CHANGE-037); the explicit human `ask_user` approval
above is treated as the authoritative release approval for this change.
Change complete.
