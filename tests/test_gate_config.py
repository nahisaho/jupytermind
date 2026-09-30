"""Tests for the TDD verification gate configuration (REQ-AIDS-013)."""

from ai_data_scientist.gate_config import get_required_test_command


# @id TEST-AIDS-PYTEST-001
# @verifies REQ-AIDS-013
def test_TEST_AIDS_PYTEST_001():
    command = get_required_test_command()
    assert command["name"] == "test"
    assert command["required"] is True
    assert command["adapter"] == "pytest"
