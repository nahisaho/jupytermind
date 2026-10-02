"""Tests for the crystal plasticity module (DES-AIMS-050 / REQ-AIMS-050)."""

from __future__ import annotations

import math

import numpy as np
import pytest


def _reference_fixture() -> dict:
    sigma_hat = 2.0
    return {
        "orientation_q": np.eye(3),
        "stress_tensor": sigma_hat * np.diag([1.0, 0.0, 0.0]),
        "crss": 0.3 * sigma_hat,
        "gamma_dot_0": 0.001,
        "n": 20,
    }


# @id TEST-AIMS-050
# @verifies REQ-AIMS-050
def test_TEST_AIMS_050_identity_orientation_uniaxial_tension_schmid_factors():
    from ai_materials_scientist.crystal_plasticity import run_crystal_plasticity

    result = run_crystal_plasticity(**_reference_fixture())

    inactive_systems = (1, 4, 7, 10)
    positive_systems = (2, 3, 5, 6, 8, 9)
    negative_systems = (11, 12)

    for idx in inactive_systems:
        i = idx - 1
        assert abs(result["schmid_factors"][i]) < 1e-9
        assert result["active_systems"][i] is False
        assert result["shear_strain_rates"][i] == 0.0

    for idx in positive_systems:
        i = idx - 1
        assert result["schmid_factors"][i] == pytest.approx(1 / math.sqrt(6), rel=0.01)
        assert result["active_systems"][i] is True
        expected_rate = 0.001 * (0.408248 / 0.3) ** 20
        assert result["shear_strain_rates"][i] == pytest.approx(expected_rate, rel=0.01)
        assert result["shear_strain_rates"][i] > 0

    for idx in negative_systems:
        i = idx - 1
        assert result["schmid_factors"][i] == pytest.approx(-1 / math.sqrt(6), rel=0.01)
        assert result["active_systems"][i] is True
        expected_rate = -0.001 * (0.408248 / 0.3) ** 20
        assert result["shear_strain_rates"][i] == pytest.approx(expected_rate, rel=0.01)
        assert result["shear_strain_rates"][i] < 0

    assert len(result["schmid_factors"]) == 12


# @id TEST-AIMS-939
# @verifies REQ-AIMS-050
def test_TEST_AIMS_939_dispatches_through_manifest():
    from ai_materials_scientist.dispatch import load_manifest

    manifest = load_manifest()
    assert (
        manifest["crystal-plasticity"]["modulePath"] == "ai_materials_scientist.crystal_plasticity"
    )
    assert manifest["crystal-plasticity"]["functionName"] == "run_crystal_plasticity"


# @id TEST-AIMS-940
# @verifies REQ-AIMS-003
def test_TEST_AIMS_940_rejects_non_orthogonal_orientation():
    from ai_materials_scientist.crystal_plasticity import run_crystal_plasticity

    params = _reference_fixture()
    params["orientation_q"] = np.array([[1.0, 0.1, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])

    with pytest.raises(ValueError, match="orientation_q"):
        run_crystal_plasticity(**params)


# @id TEST-AIMS-941
# @verifies REQ-AIMS-003
def test_TEST_AIMS_941_rejects_improper_rotation_negative_determinant():
    from ai_materials_scientist.crystal_plasticity import run_crystal_plasticity

    params = _reference_fixture()
    params["orientation_q"] = np.diag([1.0, 1.0, -1.0])  # orthogonal, det = -1

    with pytest.raises(ValueError, match="orientation_q"):
        run_crystal_plasticity(**params)


# @id TEST-AIMS-942
# @verifies REQ-AIMS-003
def test_TEST_AIMS_942_rejects_non_symmetric_stress_tensor():
    from ai_materials_scientist.crystal_plasticity import run_crystal_plasticity

    params = _reference_fixture()
    params["stress_tensor"] = np.array([[1.0, 0.5, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])

    with pytest.raises(ValueError, match="stress_tensor"):
        run_crystal_plasticity(**params)


# @id TEST-AIMS-943
# @verifies REQ-AIMS-003
def test_TEST_AIMS_943_rejects_zero_norm_stress_tensor():
    from ai_materials_scientist.crystal_plasticity import run_crystal_plasticity

    params = _reference_fixture()
    params["stress_tensor"] = np.zeros((3, 3))

    with pytest.raises(ValueError, match="stress_tensor"):
        run_crystal_plasticity(**params)


@pytest.mark.parametrize(
    ("overrides", "bad_parameter"),
    [
        ({"crss": 0.0}, "crss"),
        ({"crss": -1.0}, "crss"),
        ({"gamma_dot_0": 0.0}, "gamma_dot_0"),
        ({"gamma_dot_0": -1.0}, "gamma_dot_0"),
        ({"n": 0}, "n"),
        ({"n": -1}, "n"),
    ],
)
# @id TEST-AIMS-944
# @verifies REQ-AIMS-003
def test_TEST_AIMS_944_rejects_invalid_scalar_parameters(overrides, bad_parameter):
    from ai_materials_scientist.crystal_plasticity import run_crystal_plasticity

    params = _reference_fixture()
    params.update(overrides)

    with pytest.raises(ValueError, match=bad_parameter):
        run_crystal_plasticity(**params)


# @id TEST-AIMS-945
# @verifies REQ-AIMS-003
def test_TEST_AIMS_945_rejects_non_finite_scalar_parameters():
    from ai_materials_scientist.crystal_plasticity import run_crystal_plasticity

    for param in ("crss", "gamma_dot_0", "n"):
        params = _reference_fixture()
        params[param] = math.nan
        with pytest.raises(ValueError, match=param):
            run_crystal_plasticity(**params)


# @id TEST-AIMS-946
# @verifies REQ-AIMS-003
def test_TEST_AIMS_946_rejects_non_finite_orientation():
    from ai_materials_scientist.crystal_plasticity import run_crystal_plasticity

    params = _reference_fixture()
    bad_q = np.eye(3)
    bad_q[0, 0] = math.nan
    params["orientation_q"] = bad_q

    with pytest.raises(ValueError, match="orientation_q"):
        run_crystal_plasticity(**params)
