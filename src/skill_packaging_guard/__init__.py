"""Shared GitHub Copilot Agent Skill `SKILL.md` packaging guard utilities.

Implements DES-TECHWRITER-001 (REQ-TECHWRITER-001): a standalone,
dependency-light YAML frontmatter parser used to measure the true parsed
`description` field length GitHub Copilot CLI's skill loader would see,
across every bundled `.github/skills/*/SKILL.md` file in this repository.

This intentionally does not reuse or modify
`ai_data_scientist.skill_packaging.load_skill_manifest`, which is scoped to
`ai-data-scientist`'s own manifest (REQ-AIDS-012) and only captures the
first physical line of a folded YAML scalar -- unsuitable for measuring
true multi-line description length (see ADR-0109).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SKILLS_ROOT = _REPO_ROOT / ".github" / "skills"

_FRONTMATTER_RE = re.compile(r"^---\n(.*?\n)---\n", re.DOTALL)

__all__ = ["load_skill_frontmatter", "discover_skill_md_paths"]


# @id CODE-TECHWRITER-001
# @implements REQ-TECHWRITER-001
# @design DES-TECHWRITER-001
def load_skill_frontmatter(path: Path) -> dict:
    """Parse a `SKILL.md` file's YAML frontmatter block with a real YAML parser.

    Raises ValueError if the frontmatter block is missing, is not parseable
    YAML, or parses to a non-mapping top-level value.
    """
    text = Path(path).read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"'{path}' is missing the required YAML frontmatter block.")

    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise ValueError(f"'{path}' has unparseable YAML frontmatter: {exc}") from exc

    if not isinstance(frontmatter, dict):
        raise ValueError(
            f"'{path}' frontmatter must parse to a YAML mapping, got "
            f"{type(frontmatter).__name__!r}."
        )

    return frontmatter


# @id CODE-TECHWRITER-002
# @implements REQ-TECHWRITER-001
# @design DES-TECHWRITER-001
def discover_skill_md_paths(skills_root: Path = _SKILLS_ROOT) -> list[Path]:
    """Return every `.github/skills/*/SKILL.md` file path, sorted deterministically."""
    return sorted(Path(skills_root).glob("*/SKILL.md"))
