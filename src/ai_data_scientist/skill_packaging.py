"""Skill packaging metadata.

Implements DES-AIDS-001 (REQ-AIDS-012): parses the GitHub Copilot Agent
Skill manifest (YAML frontmatter + Markdown sections) so packaging can be
verified the same way other `sdd-*` skills in this repository are
discovered and loaded.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SKILL_PATH = _REPO_ROOT / ".github" / "skills" / "ai-data-scientist" / "SKILL.md"

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)
_FIELD_RE = re.compile(r'^(\w+):\s*"?(.*?)"?\s*$', re.MULTILINE)
_SECTION_RE = re.compile(r"^#+\s+(.+)$", re.MULTILINE)


# @id CODE-AIDS-012
# @implements REQ-AIDS-012
# @design DES-AIDS-001
def load_skill_manifest(path: Path = DEFAULT_SKILL_PATH) -> dict:
    """Parse a SKILL.md file's frontmatter and section headings."""
    text = Path(path).read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"'{path}' is missing the required YAML frontmatter block.")

    frontmatter_block, body = match.groups()
    fields = dict(_FIELD_RE.findall(frontmatter_block))
    sections = _SECTION_RE.findall(body)

    return {
        "name": fields.get("name", ""),
        "description": fields.get("description", ""),
        "sections": sections,
    }
