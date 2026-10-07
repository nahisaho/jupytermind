# CHANGE-039: aira co-scientistスキルカタログ調査に基づく純計算型モジュール追加 (fixes #83)

## Summary

A survey of nahisaho/aira's `skills/co-scientist/skills` catalog (202
sub-skills) identified functionality gaps in jupytermind's existing
`ai_<domain>_scientist` modules. 15 requirement blocks across 4 pure-
computation modules were selected as portable into jupytermind's offline,
deterministic module convention (no external API/DB call, no ML-model
inference beyond scikit-learn's own bundled estimators used exactly as
published):

- `ai_data_scientist` (general/stats file): parametric/non-parametric
  hypothesis-testing dispatcher with FDR correction, bootstrap confidence
  intervals + power analysis, missing-data mechanism heuristic diagnosis,
  single-covariate propensity-score matching, PSI/KS distribution-drift
  detection, AST-whitelist-sandboxed symbolic math (solve/differentiate/
  integrate/simplify via `sympy`)
- `ai_data_scientist` (ML file): t-SNE dimensionality reduction, Isolation
  Forest / Local Outlier Factor anomaly detection
- `ai_genomics_scientist`: CRISPR PAM-site scanning, sequence feature
  extraction, UPGMA phylogenetic tree construction from a distance matrix,
  miRNA seed-match target-site prediction
- `ai_materials_scientist`: XRD peak detection and d-spacing calculation

All modules are specified as pure functions over caller-supplied numeric/
sequence input only; none performs a network call, database lookup, or
ML-model training beyond directly invoking an existing dependency
(`scipy`, `statsmodels`, `scikit-learn`, or the newly introduced `sympy`)
exactly as that library documents, consistent with every existing module
in these features. Several requirements (CRISPR PAM scanning, propensity-
score matching, missing-data diagnosis) carry explicit disclaimer fields
in their output documenting that they are heuristic aids, not validated
causal/clinical tools.

## Scope

- Features: `ai-data-scientist`, `ai-data-scientist-ml` (ML-specific
  requirements file within the `ai-data-scientist` feature directory),
  `ai-genomics-scientist`, `ai-materials-scientist`
- Change type: feature extension (15 new requirements + designs +
  implementations across 4 requirements files / 3 feature source trees)
- Worktree: `/home/nahisaho/GitHub/jupytermind-change039`
- Branch: `change-039-aira-coscientist-modules`
- GitHub Issue: #83
- New dependency: `sympy` (added to root `pyproject.toml`, documented via
  a dedicated ADR during the design phase)

Touched artifacts (requirements stage, complete):

- `.musubix/features/ai-data-scientist/requirements.md` — new
  `REQ-AIDS-107` (ANOVA/t-test power groundwork shared with 108/109),
  `REQ-AIDS-108` (hypothesis-testing dispatcher + FDR), `REQ-AIDS-109`
  (bootstrap CI + power analysis), `REQ-AIDS-110` (missing-data mechanism
  heuristic), `REQ-AIDS-113` (propensity-score matching), `REQ-AIDS-114`
  (PSI/KS drift detection), `REQ-AIDS-115` (AST-whitelist-sandboxed
  symbolic math), `REQ-AIDS-116` (supporting/closing requirement for this
  batch)
- `.musubix/features/ai-data-scientist-ml/requirements.md` — new
  `REQ-AIDS-111` (t-SNE), `REQ-AIDS-112` (Isolation Forest / LOF anomaly
  detection)
- `.musubix/features/ai-genomics-scientist/requirements.md` — new
  `REQ-AGENOM-100` (CRISPR PAM scanning), `REQ-AGENOM-101` (sequence
  feature extraction), `REQ-AGENOM-110` (UPGMA phylogenetics),
  `REQ-AGENOM-120` (miRNA seed-match prediction)
- `.musubix/features/ai-materials-scientist/requirements.md` — new
  `REQ-AIMS-090` (XRD peak detection and d-spacing calculation)

Requirements-stage review history: two full `rubber-duck` review rounds
found and fixed 3 blocking + ~14 non-blocking issues (including a
confirmed-exploitable sandbox-bypass RCE in the original `REQ-AIDS-115`
sympy-only design, replaced with an AST-whitelist validator applied before
any `sympy` evaluation); a third `rubber-duck` round found zero blocking
and one minor non-blocking wording issue (softened in
`REQ-AGENOM-110`'s tie-break attribution to the pinned `scipy` version
rather than an implied cross-version library guarantee), which has also
been fixed. All 4 requirements files pass `npx musubix3 requirements
validate`.

## Affected Requirements

Requirements: REQ-AIDS-107, REQ-AIDS-108, REQ-AIDS-109, REQ-AIDS-110, REQ-AIDS-111, REQ-AIDS-112, REQ-AIDS-113, REQ-AIDS-114, REQ-AIDS-115, REQ-AIDS-116, REQ-AGENOM-100, REQ-AGENOM-101, REQ-AGENOM-110, REQ-AGENOM-120, REQ-AIMS-090

## Status

Requirements stage: approved by nahisaho (artifact sha256
`0ecadec69921b9dfc41e755f665aa8573a424b15aa28c30a5f5455e5dfee5a02`).
Design stage: not started.
