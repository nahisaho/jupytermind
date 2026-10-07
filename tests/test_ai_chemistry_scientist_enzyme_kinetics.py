"""Tests for ai_chemistry_scientist.enzyme_kinetics (DES-ACHEM-140)."""

from __future__ import annotations

import pytest

_SUBSTRATE_CONCENTRATIONS = [0.5, 1.0, 2.0, 5.0, 10.0, 20.0]
_VELOCITIES = [
    2.0,
    3.3333333333333335,
    5.0,
    7.142857142857143,
    8.333333333333334,
    9.090909090909092,
]


# @id TEST-ACHEM-140
# @verifies REQ-ACHEM-140
def test_TEST_ACHEM_140_fits_known_michaelis_menten_model_exactly():
    from ai_chemistry_scientist.enzyme_kinetics import run_enzyme_kinetics

    result = run_enzyme_kinetics(_SUBSTRATE_CONCENTRATIONS, _VELOCITIES)

    assert result["vmax"] == pytest.approx(10.0, abs=1e-3)
    assert result["km"] == pytest.approx(2.0, abs=1e-3)
    assert result["r_squared"] >= 0.999999


# @id TEST-ACHEM-141
# @verifies REQ-ACHEM-140
def test_TEST_ACHEM_141_result_fields_are_plain_python_floats():
    from ai_chemistry_scientist.enzyme_kinetics import run_enzyme_kinetics

    result = run_enzyme_kinetics(_SUBSTRATE_CONCENTRATIONS, _VELOCITIES)

    for key in ("vmax", "km", "r_squared"):
        assert isinstance(result[key], float)


# @id TEST-ACHEM-142
# @verifies REQ-ACHEM-003 REQ-ACHEM-140
def test_TEST_ACHEM_142_fewer_than_three_points_is_rejected():
    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters(
        "enzyme-kinetics",
        {"substrate_concentrations": [0.5, 1.0], "velocities": [2.0, 3.0]},
    )

    assert result["ok"] is False
    assert result["parameter"] == "substrate_concentrations"


# @id TEST-ACHEM-143
# @verifies REQ-ACHEM-003 REQ-ACHEM-140
def test_TEST_ACHEM_143_non_positive_substrate_concentration_is_rejected():
    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters(
        "enzyme-kinetics",
        {"substrate_concentrations": [-0.5, 1.0, 2.0], "velocities": [2.0, 3.0, 5.0]},
    )

    assert result["ok"] is False
    assert result["parameter"] == "substrate_concentrations"


# @id TEST-ACHEM-144
# @verifies REQ-ACHEM-003 REQ-ACHEM-140
def test_TEST_ACHEM_144_constant_velocities_is_rejected():
    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters(
        "enzyme-kinetics",
        {"substrate_concentrations": [0.5, 1.0, 2.0], "velocities": [5.0, 5.0, 5.0]},
    )

    assert result["ok"] is False
    assert result["parameter"] == "velocities"
    assert result["constraint"] == "must contain at least 2 distinct values"


# @id TEST-ACHEM-145
# @verifies REQ-ACHEM-140
def test_TEST_ACHEM_145_nonconvergent_fit_raises_value_error(monkeypatch):
    import ai_chemistry_scientist.enzyme_kinetics as enzyme_kinetics

    def _raise_runtime_error(*_args, **_kwargs):
        raise RuntimeError("Optimal parameters not found")

    monkeypatch.setattr(enzyme_kinetics, "curve_fit", _raise_runtime_error)

    with pytest.raises(ValueError, match="fit did not converge"):
        enzyme_kinetics.run_enzyme_kinetics(_SUBSTRATE_CONCENTRATIONS, _VELOCITIES)


# @id TEST-ACHEM-146
# @verifies REQ-ACHEM-140
def test_TEST_ACHEM_146_nonphysical_fit_raises_value_error(monkeypatch):
    import ai_chemistry_scientist.enzyme_kinetics as enzyme_kinetics

    def _fake_curve_fit(*_args, **_kwargs):
        return [-10.0, 2.0], None

    monkeypatch.setattr(enzyme_kinetics, "curve_fit", _fake_curve_fit)

    with pytest.raises(
        ValueError, match="fitted parameters must be finite with vmax > 0 and km > 0"
    ):
        enzyme_kinetics.run_enzyme_kinetics(_SUBSTRATE_CONCENTRATIONS, _VELOCITIES)
