"""Tests for ai_chemistry_scientist.dose_response (DES-ACHEM-120)."""

from __future__ import annotations

import pytest

_CONCENTRATIONS = [0.001, 0.01, 0.1, 1.0, 10.0, 100.0]
_RESPONSES = [
    99.90009990009992,
    99.00990099009901,
    90.9090909090909,
    50.0,
    9.090909090909092,
    0.9900990099009901,
]


# @id TEST-ACHEM-120
# @verifies REQ-ACHEM-120
def test_TEST_ACHEM_120_fits_known_four_parameter_logistic_exactly():
    from ai_chemistry_scientist.dose_response import run_dose_response_fit

    result = run_dose_response_fit(_CONCENTRATIONS, _RESPONSES)

    assert result["top"] == pytest.approx(100.0, abs=1e-3)
    assert result["bottom"] == pytest.approx(0.0, abs=1e-3)
    assert result["ic50"] == pytest.approx(1.0, abs=1e-3)
    assert result["hill_slope"] == pytest.approx(1.0, abs=1e-3)
    assert result["r_squared"] >= 0.999999


# @id TEST-ACHEM-121
# @verifies REQ-ACHEM-120
def test_TEST_ACHEM_121_result_fields_are_plain_python_floats():
    from ai_chemistry_scientist.dose_response import run_dose_response_fit

    result = run_dose_response_fit(_CONCENTRATIONS, _RESPONSES)

    for key in ("top", "bottom", "ic50", "hill_slope", "r_squared"):
        assert isinstance(result[key], float)


# @id TEST-ACHEM-122
# @verifies REQ-ACHEM-003 REQ-ACHEM-120
def test_TEST_ACHEM_122_fewer_than_four_points_is_rejected():
    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters(
        "dose-response-fitting",
        {"concentrations": [0.1, 1.0, 10.0], "responses": [90.0, 50.0, 10.0]},
    )

    assert result["ok"] is False
    assert result["parameter"] == "concentrations"


# @id TEST-ACHEM-123
# @verifies REQ-ACHEM-003 REQ-ACHEM-120
def test_TEST_ACHEM_123_non_positive_concentration_is_rejected():
    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters(
        "dose-response-fitting",
        {"concentrations": [-0.1, 0.1, 1.0, 10.0], "responses": [99.0, 90.0, 50.0, 10.0]},
    )

    assert result["ok"] is False
    assert result["parameter"] == "concentrations"


# @id TEST-ACHEM-124
# @verifies REQ-ACHEM-003 REQ-ACHEM-120
def test_TEST_ACHEM_124_mismatched_lengths_is_rejected():
    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters(
        "dose-response-fitting",
        {"concentrations": [0.1, 1.0, 10.0, 100.0], "responses": [90.0, 50.0, 10.0]},
    )

    assert result["ok"] is False
    assert result["parameter"] == "responses"


# @id TEST-ACHEM-125
# @verifies REQ-ACHEM-003 REQ-ACHEM-120
def test_TEST_ACHEM_125_constant_responses_is_rejected():
    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters(
        "dose-response-fitting",
        {"concentrations": [0.1, 1.0, 10.0, 100.0], "responses": [50.0, 50.0, 50.0, 50.0]},
    )

    assert result["ok"] is False
    assert result["parameter"] == "responses"
    assert result["constraint"] == "must contain at least 2 distinct values"


# @id TEST-ACHEM-126
# @verifies REQ-ACHEM-003 REQ-ACHEM-120
def test_TEST_ACHEM_126_constant_concentrations_is_rejected():
    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters(
        "dose-response-fitting",
        {"concentrations": [1.0, 1.0, 1.0, 1.0], "responses": [10.0, 20.0, 30.0, 40.0]},
    )

    assert result["ok"] is False
    assert result["parameter"] == "concentrations"
    assert result["constraint"] == "must contain at least 2 distinct values"


# @id TEST-ACHEM-127
# @verifies REQ-ACHEM-120
def test_TEST_ACHEM_127_nonconvergent_fit_raises_value_error(monkeypatch):
    import ai_chemistry_scientist.dose_response as dose_response

    def _raise_runtime_error(*_args, **_kwargs):
        raise RuntimeError("Optimal parameters not found")

    monkeypatch.setattr(dose_response, "curve_fit", _raise_runtime_error)

    with pytest.raises(ValueError, match="fit did not converge"):
        dose_response.run_dose_response_fit(_CONCENTRATIONS, _RESPONSES)


# @id TEST-ACHEM-128
# @verifies REQ-ACHEM-120
def test_TEST_ACHEM_128_nonphysical_fit_raises_value_error(monkeypatch):
    import ai_chemistry_scientist.dose_response as dose_response

    def _fake_curve_fit(*_args, **_kwargs):
        return [100.0, 0.0, -1.0, 1.0], None

    monkeypatch.setattr(dose_response, "curve_fit", _fake_curve_fit)

    with pytest.raises(ValueError, match="fitted parameters must be finite with ic50 > 0"):
        dose_response.run_dose_response_fit(_CONCENTRATIONS, _RESPONSES)
