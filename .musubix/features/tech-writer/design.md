---
schemaVersion: 1
feature: tech-writer
---
# Design / 設計

## DES-TECHWRITER-001: SKILL.md description-length guard / SKILL.md説明文字数ガード
Responsibilities: Provide a Python test utility that loads a `SKILL.md`
file's YAML frontmatter with `yaml.safe_load`, exposes the parsed
`description` string, and is reused by an automated test to (1) assert
`tech-writer`'s description is at most 1024 Unicode code points and
contains the required English/Japanese substrings, and (2) iterate every
`.github/skills/*/SKILL.md` in the repository asserting each has a
non-empty `description` of at most 1024 Unicode code points, as a
regression guard against any bundled skill silently becoming undiscoverable
in GitHub Copilot CLI.
Interfaces: `load_skill_frontmatter(path: Path) -> dict` parses the
`---`-delimited YAML frontmatter block of a `SKILL.md` file, raising
`ValueError` (identifying the file and the problem) if the block is
missing, is not parseable YAML, or parses to a non-mapping top-level value
(e.g. `None`, a scalar, or a list); on success it returns the parsed
mapping, including `description` as the exact folded-scalar string
produced by the YAML parser (no additional normalization).
`discover_skill_md_paths(skills_root: Path) -> list[Path]` returns every
`.github/skills/*/SKILL.md` file path in the repository, sorted
deterministically.
Constraints: Must not duplicate the existing but narrower
`ai_data_scientist.skill_packaging.load_skill_manifest` parser (which only
captures the first physical line of a folded field and is unsuitable for
measuring true description length); this new utility is a standalone,
dependency-light YAML-based parser usable by any skill's packaging tests.
Must not modify any skill's functional document-writing behavior — this
design is packaging/metadata-only. Depends on `pyyaml` (declared in the
`dev` optional-dependency group in `pyproject.toml`, since this utility is
used only by test tooling, not by any skill's runtime code).
Requirements: REQ-TECHWRITER-001
ADRs: ADR-0109
Depends-On: none
