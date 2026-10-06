# CHANGE-022: ai-genomics-scientist second increment — differential expression and variant pathogenicity heuristics

## Summary

Extend the existing `ai-genomics-scientist` skill (second increment) with
two new numpy/scipy-based heuristic modules, bringing the skill's module
count from 5 to 7:

- **Differential expression heuristic (REQ-AGENOM-060)**: DESeq2-style
  median-of-ratios normalization followed by Welch's two-sample t-test
  (`scipy.stats.ttest_ind(..., equal_var=False)`) on
  `log2(normalized_count + 1)` values, with Benjamini-Hochberg `padj`
  correction implemented in pure numpy. A documented exception defines
  `p_value = 1.0` (not `NaN`) for the degenerate case where both groups
  have zero variance for a gene (ADR-0107). This is explicitly a
  simplified heuristic, not a full negative-binomial GLM/Wald test and
  not a pyDESeq2 reimplementation.
- **Variant pathogenicity prediction heuristic (REQ-AGENOM-070)**: a
  fixed, embedded BLOSUM62 substitution matrix combined with a linear
  weighted-sum score (`0.5 * dissimilarity + 0.35 * conservation_score +
  0.15 if in_functional_domain`), classified into 5 fixed,
  lower-inclusive-boundary tiers (`benign` through `pathogenic`)
  (ADR-0108). Explicitly not a trained/externally calibrated classifier
  (not PolyPhen-2, SIFT, or AlphaMissense).

Both modules reuse the skill's existing shared architecture
(DES-AGENOM-001/002/003: manifest-based dispatch, atomic whole-run
validation, `RunRecord` evidence), and the existing bilingual
heuristic-limitation disclosure pattern.

## Scope

- Extended feature: `ai-genomics-scientist` (second increment, 2 new
  modules on top of the existing 5: 7 total).
- Touches: `.musubix/features/ai-genomics-scientist/requirements.md`
  (REQ-AGENOM-060, REQ-AGENOM-070 new; REQ-AGENOM-001/002/003/004
  updated for 7 modules), `.musubix/features/ai-genomics-scientist/design.md`
  (DES-AGENOM-060, DES-AGENOM-070 new; manifest/validator/traceability
  sections amended for 7 modules), new `.musubix/decisions/ADR-0107.md`
  and `ADR-0108.md`, `src/ai_genomics_scientist/differential_expression.py`
  and `variant_pathogenicity.py` (new), `src/ai_genomics_scientist/
  validation.py` and `dispatch.py` (wiring), `.github/skills/
  ai-genomics-scientist/manifest.json` and `SKILL.md`, and
  `tests/test_ai_genomics_scientist_differential_expression.py` /
  `test_ai_genomics_scientist_variant_pathogenicity.py`
  (`TEST-AGENOM-073` through `078`).
- Out of scope: any other skill; the repo-wide release-gate evidence
  debt tracked separately by CHANGE-025.

## Affected Requirements

Requirements: REQ-AGENOM-060, REQ-AGENOM-070 (plus consistency edits to
REQ-AGENOM-001/002/003/004 for the new module count)

## Status

Requirements approved (`approver: nahisaho`, artifact-sha256
`1d6811630ff35b8e645d61a15a1652a9b2edd26b1c429733878dd1eee7a61eca`,
commit `150cc0c`). Design approved (`approver: nahisaho`,
artifact-sha256
`36b7714098c87ddd0328ae1e525ab5f6ba485c7496cdd910a90e41c204ed37de`,
commit `766bed0`). Two rounds of rubber-duck review were run on
`requirements.md` (3 non-blocking gaps found and closed) and two rounds
on `design.md` (1 blocking + 2 non-blocking issues found and closed)
before each stage's approval.

Implementation complete: both modules implemented, wired into
`validation.py`/`dispatch.py`/`manifest.json`/`SKILL.md`. A rubber-duck
review of the implementation found 2 blocking issues (missing
string-type validation for `differential-expression`'s gene-ID/group
labels, risking an unhandled `TypeError`; missing float-type
enforcement for `variant-pathogenicity`'s `conservation_score`,
incorrectly accepting plain integers) and 2 non-blocking test-coverage
gaps (missing exact size-factor fixture assertions; partial rather than
full-key `GENE_C` result assertion); all 4 were fixed and verified by a
follow-up rubber-duck pass. `TEST-AGENOM-073` through `078` each have a
genuine break→red→revert→green TDD cycle recorded for
REQ-AGENOM-060/070. Full test suite (608 tests) passes; `trace check`,
`graph gate`, and `design validate` all report zero diagnostics for
this change.

### Disclosed residual risk: release approval blocked by pre-existing repo-wide debt

`npx musubix3 approval record release` is blocked, but **not by
anything introduced in this change**: `npx musubix3 gate --json` on
this branch reports zero CHANGE-022/REQ-AGENOM-060/070-related
diagnostics in every failing check (`workflow`, `tdd`, `change-history`,
`change-completeness`, `performance`). The same five checks fail
identically on clean `main` (`6662b7c`) and on every other open change
worktree (CHANGE-023, CHANGE-024), as independently diagnosed and
documented by CHANGE-025 ("Remediate the repairable share of repo-wide
release-gate debt, and disclose the one upstream-blocked residual
risk"). CHANGE-025 found that most of this debt is repairable but one
component — `CHANGE-003`'s permanent `CHANGE_PHASE_ORDER` diagnostic
(`nahisaho/musubix3#56`) — is neither re-recordable nor waivable in the
installed musubix3 CLI and therefore blocks `approval record release`
repository-wide, for every change including CHANGE-025 itself, until
musubix3 ships a fix upstream.

Per explicit user decision (2026-10-06), CHANGE-022 is merged to `main`
without a formal `approval record release` call, since that call cannot
succeed for any change until the upstream blocker is fixed. This is the
same disposition already applied to CHANGE-025. No waiver was recorded
claiming the release gate passes; this section is the disclosure of
that fact. `artifactSha256` for the release-stage manifest as computed
by `approval prepare release` at merge time:
`558b2327a5896eca8d550e2d9da03aa4aa09d31c5016a208dc84cd6ab4e760f1`.
