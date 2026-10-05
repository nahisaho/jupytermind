# CHANGE-018: Add explicit target-claim identity to sensitivity plans (#59)

## Summary

GitHub issue #59 identified a pre-existing compliance gap in
`ai_data_scientist.sensitivity`: `REQ-AIDS-056` describes
`SensitivityPlan` as carrying a target claim, but the actual public shape
only exposed `parameter_grid` and `max_runs`. As a result, a
`SensitivityReport` could not independently state which claim its
specification grid was evaluating.

This change is classified as a defect/gap-closure. The requirement is kept
as written; the implementation/design will be brought into conformance by
making the target claim explicit in the sensitivity plan/report API.

## Scope

- Existing feature: `ai-data-scientist`
- In scope:
  - DES-AIDS-044 wording for the sensitivity module's public shape
  - `src/ai_data_scientist/sensitivity.py`
  - `tests/test_sensitivity.py`
  - `.github/skills/ai-data-scientist/SKILL.md` example text that currently
    shows the old constructor shape
- Out of scope:
  - Rewording REQ-AIDS-056 to remove the target-claim obligation
  - Unrelated sensitivity-classification behavior already fixed in CHANGE-014

## Affected Requirements

Requirements: REQ-AIDS-056.

## Design

Design: DES-AIDS-044. ADRs: ADR-0057 — the `target_claim` field is a
breaking, required addition to the public `SensitivityPlan`/
`SensitivityResult`/`SensitivityReport` dataclass shape, so the decision
and its rejected alternatives (default value, plan-only storage,
out-of-band mapping) are recorded as ADR-0057 to satisfy the repository's
ADR-completeness gate and to document why the field is required rather
than defaulted.

## Impact

- `trace impact REQ-AIDS-056 --json` currently resolves to `DES-AIDS-044`,
  `CODE-AIDS-079`, `CODE-AIDS-080`, `CODE-AIDS-127`, and the existing
  REQ-AIDS-056 test set (`TEST-AIDS-096`, `097`, `098`, `099`, `205`,
  `206`, `207`, `208`, `209`, `213`, `214`, `291`).
- `graph impact src/ai_data_scientist/sensitivity.py --json` currently
  resolves to the sensitivity module itself plus
  `tests/test_sensitivity.py`; no broader code fan-out is currently indexed.
- Repository-wide search found no in-repo production callers of
  `SensitivityPlan`/`run_sensitivity` beyond documentation/examples, so the
  implementation impact is localized to this module, its tests, and
  directly related docs.

## Rationale

REQ-AIDS-056 is not stale: its current statement and acceptance text both
assume a concrete target claim whose conclusion can be reversed,
attenuated, or stable across specifications. The existing design already
records per-specification parameter choices and outcome values, so the
minimal conforming fix is to add explicit claim identity to that same data
model rather than weaken the requirement.

Planned public-shape direction, pending human requirements/design approval:

- add `target_claim: str` to `SensitivityPlan`;
- preserve that claim on `SensitivityReport`;
- preserve that claim on each `SensitivityResult`, so detached per-spec
  results also remain self-describing;
- reject blank/whitespace-only claims before any evaluation runs;
- keep existing `parameter_grid`, `max_runs`, stability classification
  fields, and evaluator contract unchanged.

Backward-compatibility note: this preserves the legacy positional binding of
existing constructor arguments (`parameter_grid`, `specification`, `results`,
etc.) while requiring a `target_claim` to be supplied either by keyword or
via the new first positional slot. No existing fields are removed or
renamed. Because these are public frozen dataclasses, any shape-based
consumer (`dataclasses.asdict`, tuple conversion, snapshot or schema
assertions, or JSON serialized from those derived structures) will observe
the added field and must be updated accordingly.

## Implementation Plan

- [x] Update `DES-AIDS-044` to replace the old GitHub #59 known-gap note with
  the approved target-claim plan shape and migration notes.
- [x] Add a genuine Red test (`TEST-AIDS-293`) proving the current code does
  not accept/preserve `target_claim`.
- [x] Implement `target_claim: str` on `SensitivityPlan`,
  `SensitivityReport`, and `SensitivityResult`, rejecting blank or
  whitespace-only claims before evaluation starts.
- [x] Thread `plan.target_claim` through every `run_sensitivity(...)` return
  path, including failed/all-failed/empty-grid branches.
- [x] Update the skill example in `.github/skills/ai-data-scientist/SKILL.md`
  to show the new constructor shape.
- [x] Refresh the existing REQ-AIDS-056 sensitivity tests to use explicit
  target claims and record fresh TDD evidence for the tests whose
  fingerprints changed.
- [x] Re-run requirements/design validation plus trace/graph/gate checks and
  capture the remaining blockers before release approval.

## Validation / Evidence

- `npx musubix3 requirements validate .musubix/features/ai-data-scientist/requirements.md`
  → PASS
- `npx musubix3 design validate .musubix/features/ai-data-scientist/design.md`
  → PASS
- `npx musubix3 trace impact REQ-AIDS-056 --json` and
  `npx musubix3 graph impact src/ai_data_scientist/sensitivity.py --json`
  confirmed the change is localized to the sensitivity module/test surface.
- Focused verification:
  - `.venv/bin/pytest tests/test_sensitivity.py -q` → `13 passed`
  - Genuine Red/Green evidence recorded for `TEST-AIDS-293`.
  - Because changing `tests/test_sensitivity.py` invalidated prior
    authoritative TDD fingerprints for existing REQ-AIDS-056 tests,
    genuine Red/Green cycles were also refreshed for `TEST-AIDS-096`,
    `097`, `098`, `099`, `205`, `206`, `207`, `208`, `209`, `213`, `214`,
    and `291` by temporarily restoring `src/ai_data_scientist/sensitivity.py`
    to its pre-change HEAD content for the Red step, then restoring the
    implemented file for Green.
- `npx musubix3 trace build` → PASS (`885 nodes`, `1270 edges`)
- `npx musubix3 trace check --strict` → FAIL only on pre-existing,
  repo-wide `ai-genomics-scientist` uncovered-trace coverage debt
  (`TRACE_COVERAGE` / `TRACE_UNCOVERED`), unrelated to CHANGE-018.
- `npx musubix3 graph index` / `graph gate` → PASS
- The missing third-party dev dependencies (`pandas`, `nbformat`,
  `matplotlib`, `rdkit`, `spacy`, `httpx`, `vaderSentiment`, etc.) blocker
  was resolved by re-running `uv pip install -e ".[dev]" --python
  .venv/bin/python` in this worktree's own `.venv`; the full project suite
  now collects and runs (`483 passed`).
- `CHANGE_DESIGN_UNCHANGED_AT_RECORD` was resolved by adding ADR-0057 and
  the corresponding `ADRs: ADR-0057` reference on DES-AIDS-044, which gave
  `design.md` a genuine further change beyond what `requirements` had
  already captured; a fresh design re-approval was then recorded and
  `change-record ... design` succeeded.
- `change-completeness` no longer reports `CHANGE-018:REQ-AIDS-056` as
  lacking ADR evidence, now that ADR-0057 decides DES-AIDS-044.
- `red` / `implementation` / `green` / `quality` are now all recorded for
  REQ-AIDS-056, in the required order (all `tdd red` before `change-record
  red`; `change-record implementation` before the corresponding `tdd
  green`; all `tdd green` before `change-record green`), verified directly
  against `.musubix/evidence/order.json` sequence numbers.
- `npx musubix3 gate --changed --json` reports **0 CHANGE-018-owned
  diagnostics**. Remaining gate/status failures are pre-existing repo-wide
  debt shared with other changes (workflow reconciliation, stale historical
  waivers/change records, model-correspondence debt, constitution fallout,
  and release-approval policy) and are not specific to CHANGE-018.

## Status

Implementation is complete and the approved public-shape change is in place:
`SensitivityPlan`, `SensitivityReport`, and `SensitivityResult` now carry
`target_claim`, blank/whitespace-only claims (including the empty string,
covered by an added assertion in `TEST-AIDS-293`) are rejected, and the
documented SKILL example is updated. All REQ-AIDS-056 tests pass (`13
passed` in `tests/test_sensitivity.py`), the full project suite passes
(`483 passed`), and fresh Red-Implementation-Green TDD evidence exists in
the required chronological order for every changed/added test.

CHANGE-018's own change-history, change-completeness, trace, and graph
gates are all clean (0 CHANGE-018-owned diagnostics). The change is
release-ready from CHANGE-018's perspective; remaining gate failures are
pre-existing repository-wide debt unrelated to this change (see #61/#62).

## Release Approval (post-fix re-record)

Human release approval was obtained via a direct approve/reject
confirmation (the `npx musubix3 approval record release` CLI command is
unconditionally blocked whenever any `.musubix/changes/*.md` file exists,
due to permanent repository-wide debt unrelated to this change), using the
`npx musubix3 approval prepare release --json` artifact hash:

`artifactSha256: ec96546524f5db3584acfc11f7a30b8a1757d6392acc222a2736b1d99092c816`

Approved by: nahisaho.
