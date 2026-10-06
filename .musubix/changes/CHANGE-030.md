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
- [ ] Requirements validated, reviewed, and approved
- [ ] Design updated (`DES-AGENOM-080`, `DES-AIMS-080`,
      `DES-ASTRUCT-060`, `ADR-0113`), validated, reviewed, and approved
- [ ] `package.json` renamed and missing `files` entries added
- [ ] README.md / README-ja.md install instructions updated
- [ ] Regression tests written and Red recorded
- [ ] Green recorded
- [ ] Quality evidence recorded
- [ ] Release approval obtained
- [ ] Full-suite validation, merge, push, new release publish, and
      verification (`npm view jupytermind version`) completed
