# CHANGE-003: Add ai-materials-scientist skill with 7 simplified simulation modules

## Summary

Introduce a new, domain-specific Copilot Agent Skill, `ai-materials-scientist`,
hosting 7 MECE-categorized materials-science simulation modules: phase-field
microstructure evolution, molecular dynamics, classical Monte Carlo lattice
sampling, kinetic Monte Carlo event-driven evolution, single-point crystal
plasticity, a simplified finite-element field solver, and a simplified binary
CALPHAD phase-diagram calculator. All modules are implemented with
numpy/scipy/pandas/scikit-learn only, per the repository's existing dependency
constraint (no heavy external solvers). The skill shares bilingual
instruction handling, module routing, parameter validation, reproducible-run
evidence recording, and a common SI unit/dimension convention across all 7
modules.

## Scope

- New feature/skill: `ai-materials-scientist`.
- New skill boundary alongside existing `ai-scientist` (orchestration) and
  `ai-data-scientist` (generic analysis/ML, including Bayesian optimization,
  which remains domain-agnostic there).
- Touches: new `.github/skills/ai-materials-scientist/` directory (manifest,
  SKILL.md, Python package), to be created during implementation.

## Affected Requirements

Requirements: REQ-AIMS-001, REQ-AIMS-002, REQ-AIMS-003, REQ-AIMS-004, REQ-AIMS-005, REQ-AIMS-010, REQ-AIMS-020, REQ-AIMS-030, REQ-AIMS-040, REQ-AIMS-050, REQ-AIMS-060, REQ-AIMS-070.

## Design

Design: DES-AIMS-001 (bilingual instruction handling), DES-AIMS-002 (module
routing), DES-AIMS-003 (parameter validation + evidence schema), DES-AIMS-010
(phase-field), DES-AIMS-020 (molecular dynamics), DES-AIMS-030 (classical
Monte Carlo / Ising), DES-AIMS-040 (kinetic Monte Carlo), DES-AIMS-050
(crystal plasticity), DES-AIMS-060 (finite-element solver), DES-AIMS-070
(CALPHAD). Backed by ADR-0015 through ADR-0024 (one per component).

Both requirements.md and design.md passed `musubix3` structural validation
and multiple rounds of native `rubber-duck` review (6 rounds for
requirements, 7 rounds for design) before explicit human approval of each
stage.

## Implementation Plan

Per-module interleaved Red-Implementation-Green TDD batches, one module per
batch, in this order: phase-field, molecular dynamics, classical Monte Carlo,
kinetic Monte Carlo, crystal plasticity, finite-element solver, CALPHAD.
Shared infrastructure (bilingual handling, routing, validation, evidence
schema — DES-AIMS-001/002/003) is implemented first as its own batch.

## Status

- [x] Impact analysis
- [x] Requirements drafted, reviewed (6 rounds), validated (PASS), approved
  (requirements.md was authored and approved before this CHANGE document was
  created, so its fingerprint did not change between the `impact` and
  `requirements` phase recordings; `--allow-unchanged` was used to capture
  this already-completed, already-approved phase retroactively — not a
  defect-fix exemption.)
- [x] Design drafted, reviewed (7 rounds), validated (PASS), approved
- [x] Red/Implementation/Green per module, all 7 simulation modules plus
  shared dispatch/evidence/validation infrastructure (REQ-AIMS-001/002/003/
  004/005/010/020/030/040/050/060/070). Full suite: 140/140 tests passing.
- [x] `trace build`/`trace check --strict`: PASS, 0 diagnostics.
- [x] `graph index`/`graph gate`: PASS.
- [ ] Quality gate: **BLOCKED, deferred to a follow-up change.**
  `gate --changed --json` reports `status: fail` due to a `musubix3` TDD
  evidence-tooling limitation discovered during this change's own
  ID-deduplication cleanup (see "Known gate blocker" below), not a defect in
  any of the 7 delivered modules or the dispatch/evidence/validation
  infrastructure. Release approval was intentionally **not** requested for
  this reason; see the follow-up GitHub issue for the dedicated repair work.
- [ ] Release approval (not requested; blocked, see above)

## Known gate blocker (deferred, tracked separately)

While correcting a project-wide `@id` global-uniqueness violation (every
`TEST-AIMS-*`/`CODE-AIMS-*` annotation had to become globally unique, with
each test function's embedded number matching its own `@id`), several test
functions were renamed more than once within this session to resolve ID
collisions. Once `musubix3 tdd green`/`tdd red` evidence had been recorded
against an intermediate test name, renaming that same test again left the
earlier evidence cycle permanently "stale"/"legacy" — and `musubix3` provides
no supported partial-repair path for this: `tdd void` refuses any cycle with
a valid Green phase (even a stale one), `tdd migrate` refuses any cycle whose
drift is real source change rather than an algorithm-only change, and direct
edits to `.musubix/evidence/tdd.json` are detected and rejected by its chain
integrity check. The tool's only offered remedy is to move the *entire*
project's `tdd.json` aside and re-record Red/Green for **all 96 requirements
project-wide**, including the 85 already-released requirements from
CHANGE-001 (`ai-scientist`) and CHANGE-002 (`ai-data-scientist`) — judged
disproportionate risk/scope for this change, and explicitly declined by the
user (`nahisaho`) in favor of deferring a dedicated fix.

Affected IDs: `TEST-AIMS-002`, `TEST-AIMS-949`, `TEST-AIMS-950`,
`TEST-AIMS-980`, `TEST-AIMS-981` (all in
`tests/test_ai_materials_scientist_dispatch.py`; the live, current test
functions in that file are `TEST-AIMS-002/947/948/990/991` and all 18 of its
tests pass) and `TEST-AIMS-040` (`tests/test_ai_materials_scientist_kinetic_monte_carlo.py`;
an earlier Green recording failed validation solely due to a transient
pytest-report ID-annotation format issue, not a test or implementation
defect; all 15 of its tests pass).

Tracked for follow-up: #39.
