# CHANGE-013: ToolUniverse-inspired offline domain-skill expansion (genomics, structural biology, chemistry)

## Summary

Add two brand-new Copilot Agent Skills, `ai-genomics-scientist` and
`ai-structural-biology-scientist`, and extend the existing
`ai-chemistry-scientist` skill with 4 additional modules, following the same
architecture already established by `ai-chemistry-scientist` /
`ai-materials-scientist`: every module is implemented purely offline
(numpy/scipy/rdkit only, no network calls, no external bioinformatics or
structural-biology libraries), with modules selected by MECE survey of the
external ToolUniverse project's domain taxonomy (used only to identify
candidate domains, not to reuse any of its code, data, or external API
calls).

- **`ai-genomics-scientist` (new skill, REQ-AGENOM-001..050)**: sequence
  feature analysis (GC content/ORF/codon usage), variant-effect heuristic
  annotation (standard genetic code), a fixed illustrative splice-site PWM
  heuristic, gene-set enrichment (hypergeometric test over a bundled toy
  50-gene/5-pathway universe), and Needleman-Wunsch pairwise alignment.
- **`ai-structural-biology-scientist` (new skill, REQ-ASTRUCT-001..050)**:
  a fixed illustrative secondary-structure propensity heuristic, Kyte-Doolittle
  hydrophobicity/burial per-residue analysis, a fixed-formula
  protein-protein docking-score heuristic, Kabsch-algorithm RMSD/structural
  similarity, and a Cα distance/sequence-separation contact-map heuristic.
- **`ai-chemistry-scientist` (extension, REQ-ACHEM-060/070/080/090)**: Ghose
  and Egan drug-likeness filters (beyond the existing Lipinski/Veber in
  REQ-ACHEM-020), a small fixed PAINS-like SMARTS structural-alert screen,
  molecular formula/exact mass, and a fixed-rule heuristic target-class
  (CNS-like / kinase-inhibitor-like / other) activity classifier.

All heuristic modules carry an explicit, fixed, bilingual limitation label
stating they are illustrative heuristics, not validated scientific
predictors, matching the existing ADMET/docking-score disclosure pattern.

## Scope

- New features: `ai-genomics-scientist`, `ai-structural-biology-scientist`.
- Extended feature: `ai-chemistry-scientist` (second increment, 4 new
  modules on top of the existing 5).
- Touches (planned): new `.github/skills/ai-genomics-scientist/`,
  `.github/skills/ai-structural-biology-scientist/` skill directories with
  `SKILL.md`/`manifest.json`; new `src/ai_genomics_scientist/`,
  `src/ai_structural_biology_scientist/` packages (`dispatch.py`,
  `evidence.py`, `validation.py`, one module file per algorithm, bundled
  `data/` CSVs); extension of `src/ai_chemistry_scientist/` with 4 new
  module files plus `dispatch.py`/manifest updates; new test suites per
  skill.
- Developed in the separate git worktree
  `/home/nahisaho/GitHub/jupytermind-change013` (branch
  `change-013-tooluniverse-domain-skills`) to avoid colliding with a
  concurrent bug-fix session working in the main checkout.

## Affected Requirements

Requirements: REQ-ACHEM-060, REQ-ACHEM-070, REQ-ACHEM-080, REQ-ACHEM-090, REQ-AGENOM-001, REQ-AGENOM-002, REQ-AGENOM-003, REQ-AGENOM-004, REQ-AGENOM-010, REQ-AGENOM-020, REQ-AGENOM-030, REQ-AGENOM-040, REQ-AGENOM-050, REQ-ASTRUCT-001, REQ-ASTRUCT-002, REQ-ASTRUCT-003, REQ-ASTRUCT-004, REQ-ASTRUCT-010, REQ-ASTRUCT-020, REQ-ASTRUCT-030, REQ-ASTRUCT-040, REQ-ASTRUCT-050

## Design

Design complete and approved: `DES-AGENOM-001..050`,
`DES-ASTRUCT-001..050`, and `DES-ACHEM-060/070/080/090` (plus an amendment
to `DES-ACHEM-001` and ADR-0025/0026/0027 updates for the 9-method
dispatcher). Drafted by 3 parallel background agents mirroring the
existing `ai-chemistry-scientist` architecture pattern (static manifest
dispatcher, shared validator registry, shared `record_run` evidence
envelope). Rubber-duck reviewed (2 blocking issues fixed in genomics —
required `scipy_version` and missing exact diagnostic constraint strings;
2 non-blocking issues fixed in structural-biology — sequence alphabet
validation and coordinate list/tuple domain; 1 non-blocking issue fixed in
chemistry — stale ADR module-count wording), re-reviewed clean, approved
by nahisaho (`artifact-sha256:
8aabaa014bf7fa109a4491646a496a134cdf9100fcfb50d049f37afff9c3c546`).

## Implementation Plan

- [x] Requirements (22 new REQ IDs across 3 features): drafted, validated
  (`musubix3 requirements validate`, `constitution validate`), rubber-duck
  reviewed (2 rounds on structural-biology and chemistry-extension; 1 round
  clean on genomics), approved by nahisaho.
- [x] Design (component/interface/constraint specs + manifests for all 3
  features): drafted, validated, rubber-duck reviewed, approved by
  nahisaho.
- [x] TDD Red/Green per requirement, per feature: implemented via 3
  parallel agents working on `src/ai_genomics_scientist/`,
  `src/ai_structural_biology_scientist/`, and the `ai-chemistry-scientist`
  second increment, each running real `tdd red`/`tdd green` cycles per
  REQ ID against the configured `test` (`.venv/bin/pytest`) command.
  Genomics: 10 Green test IDs across REQ-AGENOM-001..050 (9 requirements).
  Structural biology: 9 Green test IDs across REQ-ASTRUCT-001..050 (9
  requirements). Chemistry extension: 20 new tests recorded against
  REQ-ACHEM-060/070/080/090 (plus incidental REQ-ACHEM-001/002 dispatch
  coverage), with the 5 pre-existing chemistry modules' tests left
  untouched and still green. Full worktree suite: 454 passed
  (`.venv/bin/pytest tests/ -q`); `ruff format --check src tests`: 194
  files already formatted.
- [ ] `trace build`/`trace check --strict`, `graph index`/`graph gate`.
- [ ] Quality gate (`gate --changed --json`, `status --json`).
- [ ] Release approval (human sign-off via `ask_user`, presenting exact
  files/hash/residual risks).
- [ ] Commit, push.

## Status

In progress — requirements and design approved, starting TDD
implementation phase.
