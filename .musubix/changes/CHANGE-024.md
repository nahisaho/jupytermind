# CHANGE-024: tech-writer SKILL.md description-length fix (Issue #71)

## Summary

Fixes GitHub issue #71: the bundled `tech-writer` GitHub Copilot Agent
Skill's `SKILL.md` YAML frontmatter `description` field is 1,817 Unicode
code points (measured via `yaml.safe_load` + Python `len()` -- the metric
this change's regression test enforces), exceeding GitHub Copilot CLI's
documented 1,024-character skill-description limit (see
github/copilot-cli#3494). When exceeded, Copilot CLI silently drops the
skill from discovery with no warning, and any attempt to invoke it via
`skill(tech-writer)` fails with `Skill not found: tech-writer`.

This change adds a new requirement (REQ-TECHWRITER-001) that bounds the
`tech-writer` `description` field to 1,024 Unicode code points (measured via
Python's `yaml.safe_load` + `len()`), requires the shortened description to
still contain required English/Japanese purpose/routing substrings, and adds
an automated regression test that checks every bundled skill's `SKILL.md`
(not just `tech-writer`) to guard against this class of defect recurring.

The `tech-writer` `SKILL.md` description is shortened accordingly to 948
code points: the exhaustive bilingual trigger-phrase enumeration is moved
out of the frontmatter `description` into a new "## Trigger phrases / 起動
フレーズ" section in the skill body (the exhaustive doctype list was
already present in the body and is unchanged), leaving the frontmatter
description as a concise purpose summary plus a representative (not
exhaustive) subset of trigger phrases.

## Scope

- New feature `tech-writer` (`.musubix/features/tech-writer/requirements.md`,
  `design.md`) — packaging-only concern for this bundled skill.
- `.github/skills/tech-writer/SKILL.md` — shortened `description`
  frontmatter field; exhaustive doctype/trigger-phrase detail moved into the
  skill body.
- New test module asserting the length/content constraints for `tech-writer`
  and, as a regression guard, for every other bundled skill's `SKILL.md`.

## Out of scope

- No change to `tech-writer`'s document-writing behavior, intake flow, or
  any other skill's functional behavior.
- No change to the `japanese-prose` skill it invokes for Japanese documents.

Requirements: REQ-TECHWRITER-001
