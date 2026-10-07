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

Planned artifacts (design/implementation stages, not yet started):

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

Requirements: REQ-ACHEM-120, REQ-ACHEM-130, REQ-ACHEM-140, REQ-AGENOM-090,
REQ-AIDS-103, REQ-AIDS-104, REQ-AIDS-105, REQ-AIDS-106

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
- [ ] Red (new `TEST-*` ids per requirement)
- [ ] Implementation (new module files + dispatch/validation/evidence/
      manifest wiring)
- [ ] Green
- [ ] Quality evidence (tests, lint, trace, graph, gate)
- [ ] Release approval
- [ ] Commit (`Fixes #81`), push, merge

## Quality Evidence

Not yet available (implementation not started).

## Residual risk

To be documented at release-approval time.

## Status

Requirements and design stages complete and approved. TDD red/green phase
not yet started.
