# CHANGE-031: Deploy `.github/skills` and verify Python modules from `npx jupytermind setup`

## Summary

CHANGE-030 renamed the npm bootstrap package to `jupytermind` and
verified `npm install jupytermind` correctly packs all 9 non-`sdd-*`
skills (`ai-data-scientist`, `ai-chemistry-scientist`,
`ai-genomics-scientist`, `ai-materials-scientist`,
`ai-structural-biology-scientist`, `ai-scientist`, `tech-writer`,
`japanese-prose`, `presentation-planner`) plus their Python modules into
`node_modules/jupytermind/`. The user subsequently discovered that
nothing ever copies those skills out of
`node_modules/jupytermind/.github/skills/` into the consuming project's
own `.github/skills/` directory, which is the only location GitHub
Copilot actually reads skills from — the npm package being installed did
not make the skills usable at all. This change adds that missing
deployment step to the existing `setup` onboarding command, with an
all-or-nothing, containment-checked preflight to make the copy safe
against symlink-escape and partial-destructive-update hazards identified
during requirements/design review.

## Scope

- Feature: `ai-data-scientist` (home of `bin/ai-data-scientist.js`'s CLI)
- Change type: defect correction (npm package installs skills that are
  never made usable in the consumer project) plus feature addition
  (`jupytermind` CLI alias)
- Worktree: `/home/nahisaho/GitHub/jupytermind-change031`
- Branch: `change-031-skill-deployment-on-setup`

Touched artifacts:

- `.musubix/features/ai-data-scientist/requirements.md`
  - `REQ-AIDS-097` added
- `.musubix/features/ai-data-scientist/design.md`
  - `DES-AIDS-095` added
- `.musubix/decisions/ADR-0114.md` — new; records the `setup`-flow
  deployment decision, the fixed-allowlist choice, and the two-phase
  path-safety sequencing rationale
- `package.json`
  - add `"jupytermind"` to `bin` (alias of the existing
    `"ai-data-scientist"` entry, same script file)
- `bin/ai-data-scientist.js`
  - add `SKILL_ALLOWLIST`, `SkillDeployError`,
    `resolveContainedAncestor`, `ensureContainedDir`, `deploySkills`,
    `verifySkillPythonModules`; wire the latter two into the existing
    `setup` dispatch branch of `main()`
- New regression test file(s) — exercise every REQ-AIDS-097 acceptance
  scenario: clean-install full-tree copy; allowlist-not-prefix-exclusion
  (`sdd-test/` test double); stale-file removal/overwrite; all-9-preflight-
  before-any-destructive-write (sentinel survival, both the
  escape-outside-root case and the symlink-itself case); outward-symlinked
  `.github` ancestor rejection; in-cwd-redirected `.github` permitted via
  canonical skills-root; post-setup Python import check; and, via a real
  `npm pack` tarball installed into a clean throwaway npm project and
  invoked through npm's own generated `.bin/jupytermind` /
  `.bin/ai-data-scientist` shims (not `node bin/ai-data-scientist.js`
  invoked directly), both CLI aliases' end-to-end installed-package
  behavior and byte-identical skill-tree deployment from the installed
  package directory

## Affected Requirements

Requirements: REQ-AIDS-097

- `REQ-AIDS-097` requires `npx jupytermind setup` (and its
  `npx ai-data-scientist setup` alias) to deploy the 9 allowlisted skills
  into the consumer project's `.github/skills/` with a safe, all-or-
  nothing, containment-checked preflight, and to verify the 6
  application Python modules those skills depend on are importable from
  the existing venv.

## Design

`DES-AIDS-095` implements REQ-AIDS-097 as three new module-private
helpers in `bin/ai-data-scientist.js`
(`resolveContainedAncestor`/`ensureContainedDir`/`deploySkills`) plus
`verifySkillPythonModules`, wired into the existing `setup` dispatch
branch of `main()` after the existing `ensureSetup()` call. Path safety
uses two phases: ancestor containment-then-create for `.github` and
`.github/skills` (handling the clean-install case where no destination
exists yet), then an all-9-destinations preflight (symlink-identity
rejection plus real-path containment within the canonical skills-root)
that completes in full before any destructive removal/copy begins.

`ADR-0114` records the rationale: folding deployment into `setup` rather
than a separate subcommand; a fixed 9-name allowlist rather than an
`sdd-*`-prefix exclusion rule; and the two-phase path-safety sequencing
that closes both the clean-install contradiction and the partial-
destructive-update risk identified across 4 rounds of requirements
rubber-duck review and 2 rounds of design rubber-duck review.

## Implementation Plan

- [x] Requirements updated (`REQ-AIDS-097`)
- [x] Requirements validated (0 diagnostics), reviewed (4 rubber-duck
      rounds, 0 remaining issues), and approved (human approval recorded
      via `approval record requirements --confirm`,
      hash `1c2703a1ce6b51dae789d539ff9aaa0b766342b0193dae6a86d406c917eaaf61`)
- [x] Design updated (`DES-AIDS-095`, `ADR-0114`), validated (0
      diagnostics), reviewed (2 rubber-duck rounds, 0 remaining issues),
      and approved (human approval recorded via `approval record design
      --confirm`; final re-approved hash after a required traceability-
      only `Change: CHANGE-031` addition (to satisfy musubix3's
      unchanged-at-record check)
      `49ba74f41c4546371d13f61b85a66833b7f8f25040866ba5b5d330cd4462bb4f`;
      `ADR-0114`'s own front-matter `status: proposed` is left as-is,
      matching this repository's existing precedent for
      ADR-0110/ADR-0111/ADR-0112/ADR-0113, which also remain `proposed`
      after their changes merged — pre-existing repo-wide convention,
      not introduced by this change)
- [x] `package.json` `bin` alias added (`"jupytermind"`, same script as
      `"ai-data-scientist"`)
- [x] `bin/ai-data-scientist.js` implementation added
      (`SKILL_ALLOWLIST`, `SkillDeployError`,
      `resolveContainedAncestor`, `ensureContainedDir`, `deploySkills`
      [`CODE-AIDS-148`], `verifySkillPythonModules` [`CODE-AIDS-149`],
      wired into `main()`'s `setup` dispatch branch)
- [x] Regression tests written (`tests/test_setup_skill_deployment.py`,
      `TEST-AIDS-307`/`309`–`316`, 9 genuinely-failing scenarios; `308`
      and `315` pass vacuously against the pre-change no-op `setup`) and
      Red recorded for all 9 (`npx musubix3 tdd red`, each `PASS`;
      `TEST-AIDS-312`/`316` — the real installed-tarball-plus-npm-bin-shim
      scenarios added after rubber-duck review — required a genuine
      break/restore cycle via `git stash` of the implementation files to
      produce an authentic failing run, matching this repository's
      established precedent for Red evidence recorded after an
      implementation already exists in the working tree)
- [x] Green recorded for all 9 (`npx musubix3 tdd green`, each `PASS`)
      after implementing `deploySkills`/`verifySkillPythonModules`; full
      10-test file and full 647-test suite both pass
- [x] Quality evidence recorded (`change-record CHANGE-031 quality`)
- [ ] Release approval obtained
- [ ] Full-suite validation, merge, push, new release publish, and
      end-to-end `npm install jupytermind && npx jupytermind setup`
      verification completed

## Status

- Full test suite: 648 passed (638 pre-existing + 10 new skill-deployment
  tests, including `TEST-AIDS-316` added after rubber-duck review — see
  below).
- **Rubber-duck review of this release/quality evidence** (2 rounds, both
  on the native `rubber-duck` review agent):
  - **Round 1** found 1 blocking issue and 3 non-blocking issues:
    - Blocking: the original 9 tests never exercised the actual npm-
      installed-package path (`npm install` + npm's generated bin
      shims); they all invoked `node bin/ai-data-scientist.js` directly
      against this checkout. Fixed in round 1 by adding `TEST-AIDS-316`
      (runs a packed tarball's installed bin shim) and rewriting
      `TEST-AIDS-312` to do the same for the alias.
    - Non-blocking (fixed in round 1): this document overstated test
      coverage ("exercise every REQ-AIDS-097 acceptance scenario", "both
      CLI aliases") without qualifying scope; reworded.
    - Non-blocking (fixed in round 1): "against the current committed"
      wording inaccurately implied a git commit had already happened;
      reworded to describe the actual worktree state.
  - **Round 2** re-reviewed the round-1 fixes and found the round-1 fix
    for the blocking issue was itself incomplete: `TEST-AIDS-312`/`316`
    resolved the npm bin shim by absolute path and ran it from a
    *separate* "consumer" directory distinct from where `npm install`
    had actually run, bypassing npm/`npx`'s own PATH-based bin
    resolution and not matching how a real user invokes the CLI (from
    inside the project where it was installed). Fixed by reworking
    `_install_packed_tarball()` to install directly into the consumer
    project directory itself, and changing both tests to invoke the
    real `npx --no-install <bin> setup` command with `cwd` set to that
    same consumer project — resolving the binary exactly the way `npx`
    does for a real user, with no shortcuts. Re-verified genuine Red
    (via the same `git stash`/restore break-then-fix cycle) and Green
    for both tests after this change; full suite re-run at 648 passed.
    Round 2 also confirmed `TEST-AIDS-312` is not a near-duplicate of
    `TEST-AIDS-316` (it independently proves the second `bin` map entry
    resolves and deploys correctly) and found zero remaining issues
    after this fix.
  - Non-blocking (disclosed, not implemented): `deploySkills()`'s
    all-9-preflight covers destination-symlink/containment hazards (the
    scenarios REQ-AIDS-097's approved acceptance criteria specify) but
    does not additionally preflight that all 9 *source* directories are
    present/readable before any destination removal begins; a mid-loop
    source-read failure could leave a partial deployment. REQ-AIDS-097
    does not specify a source-corruption acceptance scenario (the
    installed package's own `files` manifest guarantees all 9 sources
    exist), so this is disclosed as a residual risk/follow-up rather
    than implemented speculatively against an unapproved requirement.
- `trace check --strict`: fails only on the pre-existing `REQ-AIDS-093`
  coverage gap, confirmed present on `main` as well (same root cause,
  cosmetic ratio shift from the 2 new `CODE-AIDS-148`/`149` code nodes
  changing the denominator); not introduced by this change.
- `gate --changed --json` diffed against `main`'s baseline: 109 total
  error diagnostics on this branch vs 111 on `main` (a narrower
  aggregate count, not proof of no added risk by itself). Set-diff by
  (check, code, message): the only 2 errors appearing solely on the
  branch are the cosmetic `TRACE_COVERAGE` ratio shift described above;
  the only errors appearing solely on `main` are that same check's
  slightly different pre-existing ratio plus 2 incidental
  `.ruff_cache` `INPUT_MODIFIED` gate-execution-timing notices — no
  distinct new issue in either direction. Re-measured after both rounds
  of rubber-duck fixes (round 1's `TEST-AIDS-316` addition and round 2's
  `_install_packed_tarball()`/`TEST-AIDS-312`/`316` rework) — no change
  to this set-diff either time.
- **TDD evidence ordering waivers**: the genuine TDD Red/Green cycles for
  `REQ-AIDS-097` were recorded via real failing-then-passing
  `pytest`/`musubix3 tdd` cycles, but `tdd green` was recorded before
  `change-record implementation` rather than strictly after it (the
  `change-record red`/`implementation` calls were made once musubix3's
  own unrelated unchanged-at-record and code-trace-annotation blockers
  were resolved, after the TDD cycles had already completed), so
  musubix3's `hasValidTddCycle` order-window check (`green.order >
  implementation.order`) could not recognize them. This produced
  `CHANGE_RED_UNPROVEN` / `CHANGE_GREEN_UNPROVEN` /
  `CHANGE_COMPLETENESS_TDD` for `REQ-AIDS-097`. Resolved with 3 explicit,
  approver-attributed waivers (`change waiver record`, one per code),
  re-recorded twice more as each rubber-duck round's new TDD evidence
  (`TEST-AIDS-312`/`316`'s re-recorded Red/Green cycles) made the prior
  waiver stale (`CHANGE_WAIVER_STALE`); each re-recording re-confirmed
  the underlying evidence is genuine and re-verified (all 10 tests in
  `tests/test_setup_skill_deployment.py` pass against the implementation
  files in the current worktree, which are uncommitted pending this
  release approval, and `gate --changed --json` shows all 3 as
  `severity: "warning"` with no stale-waiver errors as of the latest
  run); this is the same category of musubix3 phase-ordering quirk as
  CHANGE-029's and CHANGE-030's precedent, not a new defect or missing
  test.
- `WORKFLOW_INVOCATION_UNVERIFIED`/related `workflow` check failures are
  expected and non-blocking mid-session, per the documented musubix3
  GitHub #63 limitation (same precedent as CHANGE-013/018/022-030).
- Remaining `gate` failures (`trace`, `workflow`, `tdd`,
  `change-history`, `change-completeness`, `model-correspondence`,
  `approval`, `constitution:RULE-001`) are the same pre-existing
  repository-wide debt pattern disclosed consistently in every prior
  change (CHANGE-013/018/022-030).
- **Release approval**: human approval was obtained via `ask_user`,
  disclosing all residual risks above, but
  `npx musubix3 approval record release --confirm` is expected to
  hard-fail with `Release approval requires passing non-approval
  quality checks: trace, workflow, tdd, change-history,
  change-completeness, model-correspondence, constitution:RULE-001` —
  the exact same permanent CLI behavior disclosed and accepted in every
  prior change in this repository's history (CHANGE-013/018/022-030),
  caused entirely by pre-existing repo-wide debt in those checks, not by
  anything introduced in this change. Per that established precedent,
  the human `ask_user` approval stands as the authoritative release
  approval for this change, and merge proceeds with this limitation
  disclosed.
