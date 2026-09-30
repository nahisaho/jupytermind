"""Tests for skill packaging as SKILL.md (REQ-AIDS-012)."""

from ai_data_scientist.skill_packaging import DEFAULT_SKILL_PATH, load_skill_manifest


# @id TEST-AIDS-012
# @verifies REQ-AIDS-012
def test_TEST_AIDS_012():
    assert DEFAULT_SKILL_PATH.exists()

    manifest = load_skill_manifest()

    assert manifest["name"] == "ai-data-scientist"
    assert "description" in manifest
    assert len(manifest["description"]) > 0
    assert "sections" in manifest
    assert any("Workflow" in title for title in manifest["sections"])
