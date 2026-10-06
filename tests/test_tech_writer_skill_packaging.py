"""Tests for the SKILL.md description-length packaging guard (REQ-TECHWRITER-001)."""

from __future__ import annotations

from pathlib import Path

import pytest

from skill_packaging_guard import discover_skill_md_paths, load_skill_frontmatter

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TECH_WRITER_SKILL_MD = _REPO_ROOT / ".github" / "skills" / "tech-writer" / "SKILL.md"
_MAX_DESCRIPTION_LENGTH = 1024


# @id TEST-TECHWRITER-001
# @verifies REQ-TECHWRITER-001
def test_TEST_TECHWRITER_001_tech_writer_description_fits_copilot_cli_limit():
    frontmatter = load_skill_frontmatter(_TECH_WRITER_SKILL_MD)
    description = frontmatter["description"]

    assert len(description) <= _MAX_DESCRIPTION_LENGTH
    assert "technical documents" in description.lower()
    assert ("ドキュメント" in description) or ("文書" in description)


# @id TEST-TECHWRITER-002
# @verifies REQ-TECHWRITER-001
def test_TEST_TECHWRITER_002_every_bundled_skill_description_fits_copilot_cli_limit():
    skill_md_paths = discover_skill_md_paths()
    assert skill_md_paths, "expected at least one .github/skills/*/SKILL.md file"

    for path in skill_md_paths:
        frontmatter = load_skill_frontmatter(path)
        description = frontmatter.get("description")

        assert isinstance(description, str) and description, (
            f"{path} must declare a non-empty string 'description'"
        )
        assert len(description) <= _MAX_DESCRIPTION_LENGTH, (
            f"{path} description is {len(description)} chars, "
            f"exceeding the {_MAX_DESCRIPTION_LENGTH}-char Copilot CLI limit"
        )


# @id TEST-TECHWRITER-003
# @verifies REQ-TECHWRITER-001
def test_TEST_TECHWRITER_003_load_skill_frontmatter_rejects_missing_frontmatter(tmp_path):
    bad_path = tmp_path / "SKILL.md"
    bad_path.write_text("# no frontmatter here\n", encoding="utf-8")

    with pytest.raises(ValueError):
        load_skill_frontmatter(bad_path)


# @id TEST-TECHWRITER-004
# @verifies REQ-TECHWRITER-001
def test_TEST_TECHWRITER_004_load_skill_frontmatter_rejects_non_mapping_frontmatter(tmp_path):
    bad_path = tmp_path / "SKILL.md"
    bad_path.write_text("---\n- a\n- b\n---\nbody\n", encoding="utf-8")

    with pytest.raises(ValueError):
        load_skill_frontmatter(bad_path)


# @id TEST-TECHWRITER-005
# @verifies REQ-TECHWRITER-001
def test_TEST_TECHWRITER_005_load_skill_frontmatter_preserves_clip_chomping_newline(tmp_path):
    path = tmp_path / "SKILL.md"
    path.write_text(
        "---\nname: sample\ndescription: >\n  hello\n---\nbody\n",
        encoding="utf-8",
    )

    frontmatter = load_skill_frontmatter(path)

    # YAML's clip chomping indicator (">") keeps exactly one trailing
    # newline; a parser that drops the newline before the closing "---"
    # would silently undercount every clip-chomped description.
    assert frontmatter["description"] == "hello\n"


# @id TEST-TECHWRITER-006
# @verifies REQ-TECHWRITER-001
def test_TEST_TECHWRITER_006_load_skill_frontmatter_strip_chomping_has_no_trailing_newline(
    tmp_path,
):
    path = tmp_path / "SKILL.md"
    path.write_text(
        "---\nname: sample\ndescription: >-\n  hello\n---\nbody\n",
        encoding="utf-8",
    )

    frontmatter = load_skill_frontmatter(path)

    assert frontmatter["description"] == "hello"
