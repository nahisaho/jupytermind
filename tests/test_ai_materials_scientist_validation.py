"""Tests for shared parameter validation helpers (DES-AIMS-002 / REQ-AIMS-003)."""

from __future__ import annotations

import numpy as np


# @id TEST-AIMS-003
# @verifies REQ-AIMS-003
def test_TEST_AIMS_003_non_finite_array_is_rejected_naming_parameter():
    from ai_materials_scientist.validation import check_finite_array

    result = check_finite_array("field0", np.array([1.0, float("nan"), 3.0]))

    assert result["ok"] is False
    assert result["parameter"] == "field0"
    assert "finite" in result["constraint"]


# @id TEST-AIMS-981
# @verifies REQ-AIMS-003
def test_TEST_AIMS_981_finite_array_passes():
    from ai_materials_scientist.validation import check_finite_array

    result = check_finite_array("field0", np.array([1.0, 2.0, 3.0]))

    assert result["ok"] is True


# @id TEST-AIMS-982
# @verifies REQ-AIMS-003
def test_TEST_AIMS_982_non_positive_step_count_is_rejected():
    from ai_materials_scientist.validation import check_positive_step_count

    for bad_steps in (0, -1):
        result = check_positive_step_count(bad_steps)
        assert result["ok"] is False
        assert result["parameter"] == "steps"

    assert check_positive_step_count(1)["ok"] is True


# @id TEST-AIMS-983
# @verifies REQ-AIMS-003
def test_TEST_AIMS_983_non_positive_output_interval_is_rejected():
    from ai_materials_scientist.validation import check_positive_output_interval

    for bad_interval in (0, -5):
        result = check_positive_output_interval(bad_interval)
        assert result["ok"] is False
        assert result["parameter"] == "output_every"

    assert check_positive_output_interval(10)["ok"] is True


# @id TEST-AIMS-984
# @verifies REQ-AIMS-003
def test_TEST_AIMS_984_validate_parameters_dispatches_to_registered_module_validator():
    from ai_materials_scientist.validation import register_validator, validate_parameters

    def _fake_validator(params):
        if params.get("x", 0) < 0:
            return {"ok": False, "parameter": "x", "constraint": "x >= 0"}
        return {"ok": True}

    register_validator("fake-module", _fake_validator)

    assert validate_parameters("fake-module", {"x": 1})["ok"] is True
    failure = validate_parameters("fake-module", {"x": -1})
    assert failure["ok"] is False
    assert failure["parameter"] == "x"


# @id TEST-AIMS-985
# @verifies REQ-AIMS-003
def test_TEST_AIMS_985_validate_parameters_unknown_module_is_rejected():
    from ai_materials_scientist.validation import validate_parameters

    result = validate_parameters("no-such-module", {})

    assert result["ok"] is False
