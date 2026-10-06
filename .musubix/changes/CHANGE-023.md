# CHANGE-023: ai-scientist npm packaging completeness fix

## Summary

Fix GitHub issue #70: the published npm bootstrap package currently ships
`.github/skills/ai-scientist` but omits the Python implementation package
under `src/ai_scientist/**/*.py`, making the packaged `ai-scientist`
skill non-functional after `npm install`.

This change adds an explicit packaging-completeness requirement and design
guard, extends the ai-scientist test-coverage requirement to include the
new regression, updates `package.json` so npm pack/publish includes the
`src/ai_scientist` sources, and adds an automated regression test that
checks both the manifest entries and the effective `npm pack --dry-run`
artifact contents. Because the broken artifact was already published as
`ai-data-scientist-skill@0.2.4`, this fix also bumps the npm bootstrap
package version to `0.2.5` so the corrected payload can be released.

## Scope

- Feature: `ai-scientist`
- Change type: defect correction (npm/bootstrap packaging completeness)
- Worktree: `/home/nahisaho/GitHub/jupytermind-change023`
- Branch: `change-023-npm-packaging-ai-scientist`
- Issue: `#70`

Touched artifacts:

- `.musubix/features/ai-scientist/requirements.md`
  - `REQ-AISCI-024` acceptance updated
  - `REQ-AISCI-025` added
- `.musubix/features/ai-scientist/design.md`
  - `DES-AISCI-019` updated
  - `DES-AISCI-020` added
- `package.json`
  - bump npm bootstrap version `0.2.4` → `0.2.5`
  - add `src/ai_scientist/**/*.py` to `files`
- `src/ai_scientist/npm_packaging.py`
  - new packaging-audit helper linked to `REQ-AISCI-025`
- `src/ai_scientist/tdd_gate.py`
  - updated gate documentation tied to `REQ-AISCI-024`
- `tests/test_ai_scientist_skill_packaging.py`
  - update `TEST-AISCI-024`
  - add `TEST-AISCI-048`

No `pyproject.toml` package-list change was required: setuptools package
discovery already uses `[tool.setuptools.packages.find] where = ["src"]`,
so `ai_scientist` remains auto-discovered once the npm package includes
its source tree.

## Affected Requirements

Requirements: REQ-AISCI-024, REQ-AISCI-025

- `REQ-AISCI-024` now explicitly requires the ai-scientist automated test
  corpus to include packaging coverage for the new packaging-completeness
  requirement.
- `REQ-AISCI-025` adds the missing shipped-artifact contract for the npm
  bootstrap package: the ai-scientist skill payload
  (`SKILL.md` + `manifest.json`) must ship together with a `package.json`
  `files` entry whose effect is that every `src/ai_scientist/**/*.py`
  file is included in the packed artifact.

## Design

Design work updates `DES-AISCI-019` so the configured TDD gate explicitly
requires requirement-level `@verifies` coverage for every `REQ-AISCI`
requirement, including the new packaging regression, and adds
`DES-AISCI-020` as an npm skill-package completeness guard.

`DES-AISCI-020` specifies two proofs:

1. static manifest proof: `package.json.files` contains both
   `.github/skills/ai-scientist` and `src/ai_scientist/**/*.py`
2. effective artifact proof: `npm pack --dry-run --json` includes
   `.github/skills/ai-scientist/SKILL.md`,
   `.github/skills/ai-scientist/manifest.json`, and every current
   repository file matching `src/ai_scientist/**/*.py`

Requirements were rubber-duck reviewed to zero remaining issues and
approved by `nahisaho` (`artifact-sha256:
6ee8aaf4b36cd315661efa8b6fdb27b3de98d0fd27a4ecd45c1956bdd9154293`).
Design was rubber-duck reviewed to zero remaining issues and approved by
`nahisaho` (`artifact-sha256:
954cd36b61d9631acec7e5b6f029c0f0dc08c063b3c33362760cdb3ced4c6aa0`).

## Implementation

- Added `src/ai_scientist/**/*.py` to `package.json.files`
- Bumped npm bootstrap package version from `0.2.4` to `0.2.5`
- Added `src/ai_scientist/npm_packaging.py` with:
  - `load_package_files`
  - `load_npm_pack_dry_run_paths`
  - `iter_skill_python_globs`
- Updated `src/ai_scientist/tdd_gate.py` documentation so the existing
  TDD gate's responsibility text now explicitly covers the CHANGE-023
  packaging regression
- Updated `TEST-AISCI-024` so the requirement-coverage audit expects
  `REQ-AISCI-025`
- Added `TEST-AISCI-048` (`@verifies REQ-AISCI-025`) to assert:
  - `.github/skills/ai-scientist` and `src/ai_scientist/**/*.py` are in
    `package.json.files`
  - every exact shipped skill entry whose mapped `src/<package>/__init__.py`
    exists also has a matching `src/<package>/**/*.py` manifest entry
  - `npm pack --dry-run --json` includes the ai-scientist skill payload
    and every current `src/ai_scientist/**/*.py` source file

## TDD evidence

- `TEST-AISCI-024` / `REQ-AISCI-024`
  - Red recorded after updating the requirement-coverage audit to expect
    `REQ-AISCI-025`
  - Green recorded after the new packaging regression test existed and the
    suite passed
- `TEST-AISCI-048` / `REQ-AISCI-025`
  - Red recorded against the broken `package.json` missing
    `src/ai_scientist/**/*.py`
  - Green recorded after the `package.json` fix and packaged-artifact
    regression checks passed

## Verification

Focused verification completed:

- `pytest tests/test_ai_scientist_skill_packaging.py -k 'TEST_AISCI_024 or TEST_AISCI_048'`
  → passing
- `npm pack --dry-run --json`
  → verified by `TEST-AISCI-048`
- `musubix3 trace build`
  → PASS
- `musubix3 trace check --strict`
  → PASS
- `musubix3 graph index`
  → PASS
- `musubix3 graph gate`
  → PASS

## Implementation Plan

- [x] Requirements updated, validated, reviewed, and approved
- [x] Design updated, validated, reviewed, and approved
- [x] Regression tests written and Red recorded
- [x] Packaging fix implemented
- [x] Regression tests Green recorded
- [x] Quality evidence recorded
- [ ] Release approval obtained
- [ ] Full-suite validation, merge, push, and issue close completed

## Accepted residual risk

Current release remains blocked on one in-scope item plus repo-wide
pre-existing evidence debt:

- `approval`: release approval for CHANGE-023 is still pending and must be
  obtained against the current `approval prepare release --json` hash
- `workflow`: declaration reconciliation remains blocked in this live
  session by the known musubix3 limitation (`WORKFLOW_INVOCATION_UNVERIFIED`)
  and, in this session, by the current transcript-byte ceiling that caused
  `workflow-verify` on `events.jsonl` to abort before reconciliation

Repo-wide pre-existing evidence debt outside CHANGE-023's scope still
keeps the aggregate status in `fail`:

- `tdd`, `change-history`, `change-completeness`, `test-identities`,
  `performance`, `mutation`, and `attestation`: pre-existing repository
  diagnostics from older changes and unsigned local evidence still keep the
  repo-wide gate/status summary in `fail`

These are release-approval disclosures, not regressions introduced by
CHANGE-023 itself.
