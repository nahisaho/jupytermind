"""Tests for the simplified binary CALPHAD module (DES-AIMS-070 / REQ-AIMS-070)."""

from __future__ import annotations

import numpy as np
import pytest

_R = 8.314


def _reference_fixture() -> dict:
    return {
        "omega": 10000.0,
        "temperature": 400.0,
        "composition_grid": np.linspace(0.01, 0.99, 99),
    }


# @id TEST-AIMS-070
# @verifies REQ-AIMS-070
def test_TEST_AIMS_070_reference_binodal_compositions():
    from ai_materials_scientist.calphad import run_calphad

    result = run_calphad(**_reference_fixture())

    assert result["x_alpha"] == pytest.approx(0.0701, abs=1e-4)
    assert result["x_beta"] == pytest.approx(0.9299, abs=1e-4)
    assert 0.0 < result["x_alpha"] < 0.5
    assert 0.5 < result["x_beta"] < 1.0


# @id TEST-AIMS-922
# @verifies REQ-AIMS-070
def test_TEST_AIMS_922_binodal_compositions_are_mirror_symmetric_about_half():
    from ai_materials_scientist.calphad import run_calphad

    result = run_calphad(**_reference_fixture())

    assert result["x_alpha"] + result["x_beta"] == pytest.approx(1.0, abs=1e-8)


# @id TEST-AIMS-923
# @verifies REQ-AIMS-070
def test_TEST_AIMS_923_free_energy_curve_matches_regular_solution_formula():
    from ai_materials_scientist.calphad import run_calphad

    params = _reference_fixture()
    result = run_calphad(**params)

    x = params["composition_grid"]
    expected = _R * params["temperature"] * (x * np.log(x) + (1 - x) * np.log(1 - x)) + params[
        "omega"
    ] * x * (1 - x)
    np.testing.assert_allclose(result["free_energy_curve"], expected, atol=1e-8)
    assert len(result["free_energy_curve"]) == len(x)


# @id TEST-AIMS-924
# @verifies REQ-AIMS-070
def test_TEST_AIMS_924_free_energy_curve_is_symmetric_about_half():
    from ai_materials_scientist.calphad import run_calphad

    result = run_calphad(
        omega=10000.0, temperature=400.0, composition_grid=np.array([0.2, 0.3, 0.7, 0.8])
    )

    curve = result["free_energy_curve"]
    assert curve[0] == pytest.approx(curve[3], abs=1e-8)
    assert curve[1] == pytest.approx(curve[2], abs=1e-8)


# @id TEST-AIMS-925
# @verifies REQ-AIMS-070
def test_TEST_AIMS_925_is_deterministic():
    from ai_materials_scientist.calphad import run_calphad

    result_a = run_calphad(**_reference_fixture())
    result_b = run_calphad(**_reference_fixture())

    assert result_a["x_alpha"] == result_b["x_alpha"]
    assert result_a["x_beta"] == result_b["x_beta"]


# @id TEST-AIMS-926
# @verifies REQ-AIMS-070
def test_TEST_AIMS_926_dispatches_through_manifest():
    from ai_materials_scientist.dispatch import load_manifest

    manifest = load_manifest()
    assert manifest["calphad"]["modulePath"] == "ai_materials_scientist.calphad"
    assert manifest["calphad"]["functionName"] == "run_calphad"


# @id TEST-AIMS-927
# @verifies REQ-AIMS-070
def test_TEST_AIMS_927_with_evidence_wraps_run_record():
    from ai_materials_scientist.calphad import run_calphad_with_evidence

    record = run_calphad_with_evidence(**_reference_fixture())

    assert set(record.keys()) == {"metadata", "parameters", "arrays"}
    assert record["metadata"]["module"] == "calphad"
    assert record["arrays"]["x_alpha"][0] == pytest.approx(0.0701, abs=1e-4)
    assert record["arrays"]["x_beta"][0] == pytest.approx(0.9299, abs=1e-4)
    assert len(record["arrays"]["free_energy_curve"]) == len(
        _reference_fixture()["composition_grid"]
    )


# @id TEST-AIMS-928
# @verifies REQ-AIMS-003
def test_TEST_AIMS_928_rejects_non_positive_omega():
    from ai_materials_scientist.calphad import run_calphad

    params = _reference_fixture()
    params["omega"] = 0.0

    with pytest.raises(ValueError, match="omega"):
        run_calphad(**params)


# @id TEST-AIMS-929
# @verifies REQ-AIMS-003
def test_TEST_AIMS_929_rejects_non_positive_temperature():
    from ai_materials_scientist.calphad import run_calphad

    params = _reference_fixture()
    params["temperature"] = 0.0

    with pytest.raises(ValueError, match="temperature"):
        run_calphad(**params)


# @id TEST-AIMS-930
# @verifies REQ-AIMS-003
def test_TEST_AIMS_930_rejects_temperature_at_or_above_consolute_temperature():
    from ai_materials_scientist.calphad import run_calphad

    params = _reference_fixture()
    t_c = params["omega"] / (2 * _R)
    params["temperature"] = t_c

    with pytest.raises(ValueError, match="temperature"):
        run_calphad(**params)

    params["temperature"] = t_c + 50.0
    with pytest.raises(ValueError, match="temperature"):
        run_calphad(**params)


# @id TEST-AIMS-931
# @verifies REQ-AIMS-003
def test_TEST_AIMS_931_rejects_composition_grid_values_at_singular_endpoints():
    from ai_materials_scientist.calphad import run_calphad

    params = _reference_fixture()
    params["composition_grid"] = np.array([0.0, 0.5, 1.0])

    with pytest.raises(ValueError, match="composition_grid"):
        run_calphad(**params)
