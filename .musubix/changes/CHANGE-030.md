# CHANGE-030: Rename npm package to `jupytermind` and complete ai-genomics/ai-materials/ai-structural-biology-scientist npm packaging

## Summary

The repository's npm bootstrap package currently publishes as
`ai-data-scientist-skill`; `npm install jupytermind` (the repository's own
name) does not resolve to any package. This change renames the npm
package to `jupytermind`, matching the repository name and its now much
broader skill suite.

While investigating the rename, `npm pack --dry-run` revealed that 3 of
the 5 `ai-*`-prefixed scientist skills — `ai-genomics-scientist`,
`ai-materials-scientist`, and `ai-structural-biology-scientist` — are
entirely absent from `package.json`'s `files` array, so neither their
skill payload nor their `src/` Python modules ship in the packed npm
artifact, unlike `ai-chemistry-scientist` and `ai-scientist` (fixed by
CHANGE-023/ADR-0109). This change adds the missing `files` entries and a
dedicated npm packaging-completeness requirement/design/test for each of
the 3 affected features, reusing CHANGE-023's generic
`src/ai_scientist/npm_packaging.py` helpers.

## Scope

- Features: `ai-genomics-scientist`, `ai-materials-scientist`,
  `ai-structural-biology-scientist`
- Change type: feature/defect correction (npm package rename + packaging
  completeness)
- Worktree: `/home/nahisaho/GitHub/jupytermind-change030`
- Branch: `change-030-npm-rename-and-missing-modules`

Touched artifacts:

- `.musubix/features/ai-genomics-scientist/requirements.md`
  - `REQ-AGENOM-080` added
- `.musubix/features/ai-genomics-scientist/design.md`
  - `DES-AGENOM-080` added
- `.musubix/features/ai-materials-scientist/requirements.md`
  - `REQ-AIMS-080` added
- `.musubix/features/ai-materials-scientist/design.md`
  - `DES-AIMS-080` added
- `.musubix/features/ai-structural-biology-scientist/requirements.md`
  - `REQ-ASTRUCT-060` added
- `.musubix/features/ai-structural-biology-scientist/design.md`
  - `DES-ASTRUCT-060` added
- `.musubix/decisions/ADR-0113.md` — new; records both the npm rename
  decision and the packaging-completeness-guard extension to the 3
  affected features
- `package.json`
  - `name`: `ai-data-scientist-skill` -> `jupytermind`
  - version bump
  - add `.github/skills/ai-genomics-scientist`,
    `.github/skills/ai-materials-scientist`,
    `.github/skills/ai-structural-biology-scientist` and their matching
    `src/ai_genomics_scientist/**/*.py`,
    `src/ai_materials_scientist/**/*.py`,
    `src/ai_structural_biology_scientist/**/*.py` globs to `files`
- `README.md` / `README-ja.md`
  - `npm install ai-data-scientist-skill` -> `npm install jupytermind`
- `tests/test_ai_scientist_skill_packaging.py` (or dedicated new test
  files) — new regression tests for `REQ-AGENOM-080`/`REQ-AIMS-080`/
  `REQ-ASTRUCT-060`, reusing
  `src/ai_scientist/npm_packaging.py`'s existing generic helpers

No code-behavior change to any of the 3 features' Python modules
themselves; this is purely an npm distribution/packaging fix plus the
package rename.

## Affected Requirements

Requirements: REQ-AGENOM-080, REQ-AIMS-080, REQ-ASTRUCT-060

- `REQ-AGENOM-080` requires the npm bootstrap package to ship the
  `ai-genomics-scientist` skill payload together with its
  `src/ai_genomics_scientist/**/*.py` sources.
- `REQ-AIMS-080` requires the same for `ai-materials-scientist` /
  `src/ai_materials_scientist/**/*.py`.
- `REQ-ASTRUCT-060` requires the same for
  `ai-structural-biology-scientist` /
  `src/ai_structural_biology_scientist/**/*.py`.

The npm package rename itself (`ai-data-scientist-skill` -> `jupytermind`)
is a non-functional packaging-identity change with no new `REQ-*`
acceptance criteria of its own; it is documented in ADR-0113 and verified
by existing/updated tests that do not hardcode the old package name
(confirmed by repository-wide search before starting this change).

## Design

`DES-AGENOM-080`, `DES-AIMS-080`, and `DES-ASTRUCT-060` each directly
instantiate `DES-AISCI-020`'s existing npm skill-package completeness
guard pattern for their respective feature, reusing
`src/ai_scientist/npm_packaging.py`'s generic
`load_package_files`/`load_npm_pack_dry_run_paths`/
`iter_skill_python_globs` helpers rather than duplicating them.

ADR-0113 records the rationale for both the npm rename and the packaging
extension, and the alternatives considered and rejected (dual-publish
under both names; leaving the name unchanged; a single combined
cross-feature test instead of 3 feature-scoped ones).

## Implementation Plan

- [x] Requirements updated (`REQ-AGENOM-080`, `REQ-AIMS-080`,
      `REQ-ASTRUCT-060`)
- [x] Requirements validated, reviewed, and approved
- [x] Design updated (`DES-AGENOM-080`, `DES-AIMS-080`,
      `DES-ASTRUCT-060`, `ADR-0113`), validated, reviewed, and approved
      (human design-approval recorded via `approval record design
      --confirm`; `ADR-0113`'s own front-matter `status: proposed` is
      left as-is, matching this repository's existing precedent for
      ADR-0110/ADR-0111/ADR-0112, which also remain `proposed` after
      their changes merged — pre-existing repo-wide convention, not
      introduced by this change)
- [x] `package.json` renamed and missing `files` entries added
- [x] README.md / README-ja.md install instructions updated
- [x] Regression tests written and Red recorded
- [x] Green recorded
- [x] Quality evidence recorded
- [ ] Release approval obtained
- [ ] Full-suite validation, merge, push, new release publish, and
      verification (`npm view jupytermind version`) completed

## Status

- Full test suite: 638 passed (635 pre-existing + 3 new packaging tests).
- `trace check --strict`: fails only on the pre-existing `REQ-AIDS-093`
  coverage gap, confirmed present on `main` as well (same root cause,
  cosmetic ratio shift from the 3 new requirements changing the
  denominator); not introduced by this change.
- `gate --changed --json` diffed against `main`'s baseline: 105 total
  errors on this branch vs 107 on `main` (a narrower aggregate count,
  not proof of no added risk by itself). Category-by-category, the
  exact set-diff breakdown: 2 errors appear only on the branch (the
  cosmetic `TRACE_COVERAGE` ratio shift, see above); 4 errors appear
  only on `main` (2 incidental `.ruff_cache` `INPUT_MODIFIED` notices
  from gate-execution timing, plus the same `TRACE_COVERAGE` check at
  `main`'s slightly different pre-existing ratio — not a distinct
  issue). The 9 `CHANGE_RED_UNPROVEN` / `CHANGE_GREEN_UNPROVEN` /
  `CHANGE_COMPLETENESS_TDD` diagnostics described below do **not**
  appear in this branch error count at all, because they were
  explicitly downgraded to warnings via recorded waivers (not because
  they were silently absent/unevaluated).
- **TDD evidence ordering waivers**: the genuine TDD Red/Green cycles for
  `REQ-AGENOM-080`/`REQ-AIMS-080`/`REQ-ASTRUCT-060` were recorded via real
  break/pytest/restore cycles, but were sequenced before
  `change-record implementation` rather than strictly after it, so
  musubix3's `hasValidTddCycle` order-window check (`green.order >
  implementation.order`) cannot recognize them. This produced
  `CHANGE_RED_UNPROVEN` / `CHANGE_GREEN_UNPROVEN` /
  `CHANGE_COMPLETENESS_TDD` for all 3 requirements. Resolved with 9
  explicit, approver-attributed waivers (`change waiver record`,
  one per requirement per code) documenting that the underlying evidence
  is genuine and re-verified (all 3 new tests pass against the current
  committed `package.json`); this is the same category of musubix3
  phase-ordering quirk as CHANGE-029's precedent, not a new defect or
  missing test.
- `WORKFLOW_INVOCATION_UNVERIFIED`/related `workflow` check failures are
  expected and non-blocking mid-session, per the documented musubix3
  GitHub #63 limitation (same precedent as CHANGE-013/018/022-029).
- Remaining `gate` failures (`trace`, `workflow`, `tdd`,
  `change-history`, `change-completeness`, `model-correspondence`,
  `approval`, `constitution:RULE-001`) are the same pre-existing
  repository-wide debt pattern disclosed consistently in every prior
  change (CHANGE-013/018/022-029); `approval` fails only because release
  approval has not yet been recorded.
