"""npm packaging-completeness regression for the ai-materials-scientist skill."""

from __future__ import annotations

from pathlib import Path

from ai_scientist.npm_packaging import (
    iter_skill_python_globs,
    load_npm_pack_dry_run_paths,
    load_package_files,
)

SKILL_ENTRY = ".github/skills/ai-materials-scientist"
SOURCE_GLOB = "src/ai_materials_scientist/**/*.py"


# @id TEST-AIMS-992
# @verifies REQ-AIMS-080
def test_TEST_AIMS_992_npm_package_ships_skill_payload_with_matching_python_sources():
    package_files = load_package_files()

    assert SKILL_ENTRY in package_files
    assert SOURCE_GLOB in package_files
    assert iter_skill_python_globs(package_files)[SKILL_ENTRY] == SOURCE_GLOB

    packed_paths = load_npm_pack_dry_run_paths()
    assert f"{SKILL_ENTRY}/SKILL.md" in packed_paths
    assert f"{SKILL_ENTRY}/manifest.json" in packed_paths

    source_paths = {path.as_posix() for path in Path("src/ai_materials_scientist").rglob("*.py")}
    assert source_paths.issubset(packed_paths)
