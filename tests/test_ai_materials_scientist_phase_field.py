"""Tests for the phase-field module (DES-AIMS-010 / REQ-AIMS-010)."""

from __future__ import annotations

import math
from itertools import pairwise

import numpy as np
import pytest


def _reference_initial_field(n: int = 64) -> np.ndarray:
    i, j = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    return 0.5 + 0.01 * np.cos(2 * math.pi * i / n) * np.cos(2 * math.pi * j / n)


def _reference_params(model: str, dt: float) -> dict:
    return {
        "field0": _reference_initial_field(),
        "model": model,
        "dx": 1.0,
        "M": 1.0,
        "kappa": 1.0,
        "dt": dt,
        "steps": 200,
        "output_every": 20,
    }


# @id TEST-AIMS-010
# @verifies REQ-AIMS-010
def test_TEST_AIMS_010_reports_correct_stability_bounds():
    from ai_materials_scientist.phase_field import compute_dt_bound

    assert compute_dt_bound("allen-cahn", M=1.0, kappa=1.0, dx=1.0) == pytest.approx(0.2)
    assert compute_dt_bound("cahn-hilliard", M=1.0, kappa=1.0, dx=1.0) == pytest.approx(0.025)


# @id TEST-AIMS-977
# @verifies REQ-AIMS-010
def test_TEST_AIMS_977_cahn_hilliard_conserves_mass():
    from ai_materials_scientist.phase_field import run_phase_field

    params = _reference_params("cahn-hilliard", dt=0.025)
    result = run_phase_field(**params)

    dx2 = params["dx"] ** 2
    mass_initial = result["snapshots"][0].sum() * dx2
    mass_final = result["snapshots"][-1].sum() * dx2

    assert abs(mass_final - mass_initial) <= 1e-10 * max(1.0, abs(mass_initial))
    assert result["dt_bound"] == pytest.approx(0.025)
    # Step-zero snapshot included, plus one every 20 steps through 200.
    assert len(result["snapshots"]) == 11
    assert np.array_equal(result["snapshots"][0], params["field0"])


def _discrete_free_energy(c: np.ndarray, dx: float, kappa: float) -> float:
    f_bulk = (c**2) * (1 - c) ** 2
    grad_i = (np.roll(c, -1, axis=0) - c) / dx
    grad_j = (np.roll(c, -1, axis=1) - c) / dx
    return float(dx**2 * np.sum(f_bulk + (kappa / 2) * (grad_i**2 + grad_j**2)))


# @id TEST-AIMS-978
# @verifies REQ-AIMS-010
def test_TEST_AIMS_978_allen_cahn_free_energy_is_non_increasing():
    from ai_materials_scientist.phase_field import run_phase_field

    params = _reference_params("allen-cahn", dt=0.2)
    result = run_phase_field(**params)

    energies = [
        _discrete_free_energy(snapshot, params["dx"], params["kappa"])
        for snapshot in result["snapshots"]
    ]
    for earlier, later in pairwise(energies):
        assert later <= earlier + 1e-10
    assert result["dt_bound"] == pytest.approx(0.2)


# @id TEST-AIMS-979
# @verifies REQ-AIMS-003
@pytest.mark.parametrize(
    ("overrides", "bad_parameter"),
    [
        ({"M": 0.0}, "M"),
        ({"M": -1.0}, "M"),
        ({"kappa": -1.0}, "kappa"),
        ({"dx": 0.0}, "dx"),
        ({"dx": -1.0}, "dx"),
        ({"dt": 0.0}, "dt"),
        ({"dt": -0.1}, "dt"),
        ({"steps": 0}, "steps"),
        ({"steps": -5}, "steps"),
    ],
)
def test_TEST_AIMS_979_rejects_invalid_parameters_before_any_step(overrides, bad_parameter):
    from ai_materials_scientist.phase_field import run_phase_field

    params = _reference_params("allen-cahn", dt=0.2)
    params.update(overrides)
    field_before = params["field0"].copy()

    with pytest.raises(ValueError, match=bad_parameter):
        run_phase_field(**params)

    assert np.array_equal(params["field0"], field_before)


# @id TEST-AIMS-980
# @verifies REQ-AIMS-010
def test_TEST_AIMS_980_dispatches_through_manifest():
    from ai_materials_scientist.dispatch import load_manifest

    manifest = load_manifest()
    assert manifest["phase-field"]["modulePath"] == "ai_materials_scientist.phase_field"
    assert manifest["phase-field"]["functionName"] == "run_phase_field"
