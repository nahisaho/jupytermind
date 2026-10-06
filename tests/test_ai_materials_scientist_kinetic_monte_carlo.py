"""Tests for the kinetic Monte Carlo module (DES-AIMS-040 / REQ-AIMS-040)."""

from __future__ import annotations

import numpy as np
import pytest


def _reference_fixture() -> dict:
    return {
        "gamma": 1.0,
        "a": 1.0,
        "total_time": 100.0,
        "output_times": [100.0],
        "base_seed": 7,
    }


# @id TEST-AIMS-040
# @verifies REQ-AIMS-040
def test_TEST_AIMS_040_derives_realization_seeds():
    from ai_materials_scientist.kinetic_monte_carlo import run_kinetic_monte_carlo

    result = run_kinetic_monte_carlo(**_reference_fixture())

    assert result["realization_seeds"] == [7 + i for i in range(200)]


# @id TEST-AIMS-963
# @verifies REQ-AIMS-040
def test_TEST_AIMS_963_mean_squared_displacement_matches_diffusion_theory():
    from ai_materials_scientist.kinetic_monte_carlo import run_kinetic_monte_carlo

    params = _reference_fixture()
    result = run_kinetic_monte_carlo(**params)

    gamma, a, t = params["gamma"], params["a"], params["output_times"][0]
    displacements_at_t = result["displacements"][0]  # shape (200, 2)
    squared_magnitudes = np.sum(displacements_at_t**2, axis=-1)
    mean_squared_displacement = np.mean(squared_magnitudes)
    ratio = mean_squared_displacement / (4 * gamma * a**2 * t)

    assert 0.9 <= ratio <= 1.1


# @id TEST-AIMS-964
# @verifies REQ-AIMS-040
def test_TEST_AIMS_964_never_advances_past_total_time():
    from ai_materials_scientist.kinetic_monte_carlo import run_kmc_single_realization

    events = run_kmc_single_realization(gamma=1.0, a=1.0, total_time=10.0, seed=7)

    assert all(t <= 10.0 for t, _ in events)
    assert events == sorted(events, key=lambda e: e[0])


# @id TEST-AIMS-965
# @verifies REQ-AIMS-040
def test_TEST_AIMS_965_dispatches_through_manifest():
    from ai_materials_scientist.dispatch import load_manifest

    manifest = load_manifest()
    assert (
        manifest["kinetic-monte-carlo"]["modulePath"]
        == "ai_materials_scientist.kinetic_monte_carlo"
    )
    assert manifest["kinetic-monte-carlo"]["functionName"] == "run_kinetic_monte_carlo"


# @id TEST-AIMS-966
# @verifies REQ-AIMS-003
def test_TEST_AIMS_966_rejects_empty_output_times():
    from ai_materials_scientist.kinetic_monte_carlo import run_kinetic_monte_carlo

    params = _reference_fixture()
    params["output_times"] = []

    with pytest.raises(ValueError, match="output_times"):
        run_kinetic_monte_carlo(**params)


# @id TEST-AIMS-967
# @verifies REQ-AIMS-003
def test_TEST_AIMS_967_rejects_non_finite_output_times():
    from ai_materials_scientist.kinetic_monte_carlo import run_kinetic_monte_carlo

    params = _reference_fixture()
    params["output_times"] = [float("nan")]

    with pytest.raises(ValueError, match="output_times"):
        run_kinetic_monte_carlo(**params)


@pytest.mark.parametrize(
    ("overrides", "bad_parameter"),
    [
        ({"gamma": 0.0}, "gamma"),
        ({"gamma": -1.0}, "gamma"),
        ({"a": 0.0}, "a"),
        ({"a": -1.0}, "a"),
        ({"total_time": 0.0}, "total_time"),
        ({"total_time": -1.0}, "total_time"),
        ({"output_times": [0.0]}, "output_time"),
        ({"output_times": [-1.0]}, "output_time"),
        ({"output_times": [100.1]}, "output_time"),
    ],
)
# @id TEST-AIMS-968
# @verifies REQ-AIMS-003
def test_TEST_AIMS_968_rejects_invalid_parameters_before_any_hop(overrides, bad_parameter):
    from ai_materials_scientist.kinetic_monte_carlo import run_kinetic_monte_carlo

    params = _reference_fixture()
    params.update(overrides)

    with pytest.raises(ValueError, match=bad_parameter):
        run_kinetic_monte_carlo(**params)
