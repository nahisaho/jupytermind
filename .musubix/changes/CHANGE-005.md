# CHANGE-005: Add ai-chemistry-scientist skill with 5 cheminformatics modules

## Summary

Introduce a new, domain-specific Copilot Agent Skill, `ai-chemistry-scientist`,
hosting 5 MECE-categorized cheminformatics/drug-discovery modules: molecular
descriptor calculation, ADMET heuristic screening (Lipinski's Rule of Five +
Veber's rule), QSAR linear-regression modeling, molecular similarity search
(Morgan-fingerprint Tanimoto) against a bundled sample dataset, and a
simplified pharmacophore-complementarity docking-score heuristic. All modules
are implemented with RDKit (required dependency, local computation only, no
network calls, no external solver binaries) plus numpy/scikit-learn already
present in this repository. The skill shares bilingual instruction handling,
module routing, parameter validation, and reproducible-run evidence recording
with the same contract shape as `ai-materials-scientist`.

This is inspired by a survey of the external ToolUniverse project's domain
taxonomy (mims-harvard/ToolUniverse), used only to identify candidate
scientific domains; no code, data, or API wrapping from that project is
reused — every module here is a first-party, local-only implementation
consistent with this repository's existing no-network-call convention.

## Scope

- New feature/skill: `ai-chemistry-scientist`.
- New skill boundary alongside existing `ai-scientist` (orchestration),
  `ai-data-scientist` (generic analysis/ML, including Bayesian optimization,
  which remains domain-agnostic there), and `ai-materials-scientist`
  (materials-science simulation).
- New required dependency: `rdkit` (added to `pyproject.toml`).
- Touches: new `.github/skills/ai-chemistry-scientist/` directory (manifest,
  SKILL.md, Python package under `src/ai_chemistry_scientist/`), to be
  created during implementation.

## Affected Requirements

Requirements: REQ-ACHEM-001, REQ-ACHEM-002, REQ-ACHEM-003, REQ-ACHEM-004, REQ-ACHEM-010, REQ-ACHEM-020, REQ-ACHEM-030, REQ-ACHEM-040, REQ-ACHEM-050.

## Change-Record Phase Notes

`impact` and `requirements` phases were both recorded (`change-record CHANGE-005
impact|requirements`) after `requirements.md` was already drafted, validated,
and rubber-duck reviewed to completion in this session — so no further textual
change occurred between the `impact` fingerprint snapshot and the
`requirements` phase snapshot. The `requirements` phase was therefore recorded
with `--allow-unchanged`; this flag is a pure fingerprint-diff bypass in the
CLI (no change-type restriction is enforced in code), and is used here because
the requirements content was already final and human-approved at record time,
not because of unchanged/stale content.

## Design

Design drafted in `.musubix/features/ai-chemistry-scientist/design.md` (8
design components, DES-ACHEM-001/002/003/010/020/030/040/050) plus 8 new
ADRs (`ADR-0025` through `ADR-0032`), mirroring `ai-materials-scientist`'s
dispatch/validation/evidence contract shape. Rubber-duck reviewed across 3
rounds: round 1 found 5 blocking + 2 non-blocking issues (incomplete
dispatcher handler-invocation contract; evidence recorder disconnected
from module interfaces; QSAR validation not covering `query_smiles_list`
plus a validate-before-compute sequencing conflict with the rank-check;
ADR-0028 overclaiming RDKit was already added to `pyproject.toml` and
over-asserting an exact installed version; stale trace evidence;
undesigned SKILL.md limitation-label deliverable; a malformed manifest
path typo in ADR-0025) — all fixed. Round 2 found 2 new blocking issues
introduced by the round-1 fixes (missing params-passing definition
between `dispatch` and handler wrappers; a double-validation contradiction
between the new wrapper-owns-validation contract and each module's own
Responsibilities text; no localization mechanism for
`limitation_label`/no exact bilingual text specified; QSAR's "reuses
validated descriptors" claim unsupported by `validate_parameters`'s
actual interface) — all fixed (dispatch now passes `request_text`
through; DES-ACHEM-020/030/040/050 now explicitly receive
already-validated input with DES-ACHEM-010 called out as the sole
interleaved-validation exception; `limitation_label_key` + exact bilingual
text + a wrapper-side localization step were added; QSAR's "reuse" claim
was replaced with an explicit, ADR-0030-documented intentional-recomputation
rationale). Round 3 found one remaining non-blocking wording
inconsistency (DES-ACHEM-002's `validate_batch_item` Interfaces line
still attributing the per-item call to "REQ-ACHEM-010's handler" instead
of `run_molecular_descriptors` itself) — fixed. `design validate` and
`trace check --strict` (post `trace build`) both ran clean after all
fixes.

## Status

- [x] Requirements drafted
- [x] Requirements rubber-duck reviewed (2 passes; all blocking issues resolved)
- [x] Requirements approved (approver: nahisaho, artifactSha256: c9f93da6906b9006496b3a6202b2048cfe51728008309311afe5b7a95b1c4b69)
- [x] Design drafted
- [x] Design rubber-duck reviewed (3 passes; all blocking issues resolved)
- [x] Design approved (approver: nahisaho, artifactSha256: 0da4bf67c7fcbcd56f60cb5967d29c3ea6af7de3564c02cfb3a7c1f959f8e692)
- [ ] TDD Red/Green per requirement
- [ ] trace/graph gates pass
- [ ] Release approval
