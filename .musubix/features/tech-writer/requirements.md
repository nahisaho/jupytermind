---
schemaVersion: 1
feature: tech-writer
---
# Requirements / 要求

Feature: Packaging constraints for the bundled `tech-writer` GitHub Copilot
Agent Skill, which structures and polishes technical documents. This feature
tracks the skill's `SKILL.md` metadata packaging requirements so the skill
remains discoverable and loadable by GitHub Copilot CLI's skill loader.

## REQ-TECHWRITER-001: SKILL.md description stays within the Copilot CLI skill-loader limit / SKILL.md説明文はCopilot CLIのスキルローダー上限内に収める
Priority: must
Type: non-functional
Pattern: ubiquitous
Statement: The tech-writer skill's SKILL.md description frontmatter field shall not exceed 1024 Unicode code points, counted as the exact `description` string value returned by a standard YAML parser's folded-scalar resolution with no additional normalization, so that GitHub Copilot CLI's skill loader does not silently drop the skill.
Acceptance: An automated test loads `.github/skills/tech-writer/SKILL.md`'s YAML frontmatter using Python's `yaml.safe_load` and asserts `len(description) <= 1024` (Python's `len()` on a `str` counts Unicode code points). The same test enumerates every `.github/skills/*/SKILL.md` file in this repository, asserts each has parseable YAML frontmatter containing a non-empty string `description` field, and asserts `len(description) <= 1024` for each, to guard against regressions in any bundled skill, including removal of the field itself.
Constraints: The tech-writer description value shall satisfy `"technical documents" in description.lower()` and `("ドキュメント" in description) or ("文書" in description)`; the same automated test asserts both conditions. Exhaustive doctype lists and trigger-phrase enumerations beyond these required substrings may be moved into the SKILL.md body instead of the frontmatter description.
