"""Tests for the molecular dynamics module (DES-AIMS-020 / REQ-AIMS-020)."""

from __future__ import annotations

import math

import numpy as np
import pytest


def _reference_fixture(dt: float) -> dict:
    side = 1.5
    positions0 = np.array(
        [
            [0.0, 0.0],
            [side, 0.0],
            [side, side],
            [0.0, side],
        ]
    )
    velocities0 = np.zeros_like(positions0)
    return {
        "positions0": positions0,
        "velocities0": velocities0,
        "lj_params": {"epsilon": 1.0, "sigma": 1.0, "mass": 1.0},
        "box_length": 6.0,
        "cutoff": 2.5,
        "dt": dt,
        "steps": 1000,
        "output_every": 10,
    }


# @id TEST-AIMS-020
# @verifies REQ-AIMS-020
def test_TEST_AIMS_020_reports_correct_stability_bound():
    from ai_materials_scientist.molecular_dynamics import compute_dt_bound

    assert compute_dt_bound(epsilon=1.0, sigma=1.0, mass=1.0) == pytest.approx(0.005)


# @id TEST-AIMS-969
# @verifies REQ-AIMS-020
def test_TEST_AIMS_969_conserves_energy_within_one_percent():
    from ai_materials_scientist.molecular_dynamics import run_molecular_dynamics

    params = _reference_fixture(dt=0.005)
    result = run_molecular_dynamics(**params)

    assert result["dt_bound"] == pytest.approx(0.005)
    energies = np.array(result["energies"])
    e0 = energies[0]
    max_rel_drift = np.max(np.abs(energies - e0) / abs(e0))
    assert max_rel_drift <= 0.01
    assert len(result["snapshots"]) == 101
    assert len(energies) == 101
    assert np.array_equal(result["snapshots"][0]["positions"], params["positions0"])


# @id TEST-AIMS-970
# @verifies REQ-AIMS-020
def test_TEST_AIMS_970_dispatches_through_manifest():
    from ai_materials_scientist.dispatch import load_manifest

    manifest = load_manifest()
    assert (
        manifest["molecular-dynamics"]["modulePath"] == "ai_materials_scientist.molecular_dynamics"
    )
    assert manifest["molecular-dynamics"]["functionName"] == "run_molecular_dynamics"


# @id TEST-AIMS-971
# @verifies REQ-AIMS-003
def test_TEST_AIMS_971_rejects_cutoff_greater_than_half_box():
    from ai_materials_scientist.molecular_dynamics import run_molecular_dynamics

    params = _reference_fixture(dt=0.005)
    params["cutoff"] = 3.1  # box_length / 2 == 3.0

    with pytest.raises(ValueError, match="cutoff"):
        run_molecular_dynamics(**params)


@pytest.mark.parametrize(
    ("overrides", "bad_parameter"),
    [
        ({"box_length": 0.0}, "box_length"),
        ({"box_length": -1.0}, "box_length"),
        ({"dt": 0.0}, "dt"),
        ({"dt": -0.1}, "dt"),
        ({"steps": 0}, "steps"),
        ({"steps": -1}, "steps"),
    ],
)
# @id TEST-AIMS-972
# @verifies REQ-AIMS-003
def test_TEST_AIMS_972_rejects_invalid_scalar_parameters(overrides, bad_parameter):
    from ai_materials_scientist.molecular_dynamics import run_molecular_dynamics

    params = _reference_fixture(dt=0.005)
    params.update(overrides)

    with pytest.raises(ValueError, match=bad_parameter):
        run_molecular_dynamics(**params)


@pytest.mark.parametrize(
    ("overrides", "bad_parameter"),
    [
        ({"mass": 0.0}, "mass"),
        ({"mass": -1.0}, "mass"),
        ({"epsilon": 0.0}, "epsilon"),
        ({"epsilon": -1.0}, "epsilon"),
        ({"sigma": 0.0}, "sigma"),
        ({"sigma": -1.0}, "sigma"),
    ],
)
# @id TEST-AIMS-973
# @verifies REQ-AIMS-003
def test_TEST_AIMS_973_rejects_invalid_lj_params(overrides, bad_parameter):
    from ai_materials_scientist.molecular_dynamics import run_molecular_dynamics

    params = _reference_fixture(dt=0.005)
    params["lj_params"] = {**params["lj_params"], **overrides}

    with pytest.raises(ValueError, match=bad_parameter):
        run_molecular_dynamics(**params)


# @id TEST-AIMS-974
# @verifies REQ-AIMS-003
def test_TEST_AIMS_974_rejects_non_positive_cutoff():
    from ai_materials_scientist.molecular_dynamics import run_molecular_dynamics

    params = _reference_fixture(dt=0.005)
    params["cutoff"] = 0.0

    with pytest.raises(ValueError, match="cutoff"):
        run_molecular_dynamics(**params)


# @id TEST-AIMS-975
# @verifies REQ-AIMS-003
def test_TEST_AIMS_975_rejects_particles_too_close():
    from ai_materials_scientist.molecular_dynamics import run_molecular_dynamics

    params = _reference_fixture(dt=0.005)
    params["positions0"] = np.array([[0.0, 0.0], [0.1, 0.0], [1.5, 0.0], [0.0, 1.5]])

    with pytest.raises(ValueError, match="separation"):
        run_molecular_dynamics(**params)


# @id TEST-AIMS-976
# @verifies REQ-AIMS-003
def test_TEST_AIMS_976_rejects_non_finite_positions_or_velocities():
    from ai_materials_scientist.molecular_dynamics import run_molecular_dynamics

    params = _reference_fixture(dt=0.005)
    params["positions0"] = params["positions0"].copy()
    params["positions0"][0, 0] = math.nan

    with pytest.raises(ValueError, match="positions0"):
        run_molecular_dynamics(**params)
