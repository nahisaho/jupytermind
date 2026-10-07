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

Not yet started.

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
- [ ] Design (DES-ACHEM-120/130/140, DES-AGENOM-090, DES-AIDS-103/104/105/106)
- [ ] Design rubber-duck review + human approval
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

Requirements stage complete and approved. Design stage not yet started.
