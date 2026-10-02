"""Tests for the classical Monte Carlo module (DES-AIMS-030 / REQ-AIMS-030)."""

from __future__ import annotations

import numpy as np
import pytest


def _reference_fixture(temperature: float) -> dict:
    L = 20
    return {
        "L": L,
        "J": 1.0,
        "T": temperature,
        "equilibration_sweeps": 2000,
        "sampling_sweeps": 8000,
        "seed": 12345,
        "initial_spins": np.ones((L, L), dtype=np.int64),
    }


# @id TEST-AIMS-030
# @verifies REQ-AIMS-030
def test_TEST_AIMS_030_below_curie_temperature_is_ordered():
    from ai_materials_scientist.classical_monte_carlo import run_classical_monte_carlo

    result = run_classical_monte_carlo(**_reference_fixture(temperature=1.5))

    assert result["mean_abs_magnetization"] > 0.8


# @id TEST-AIMS-932
# @verifies REQ-AIMS-030
def test_TEST_AIMS_932_above_curie_temperature_is_disordered():
    from ai_materials_scientist.classical_monte_carlo import run_classical_monte_carlo

    result = run_classical_monte_carlo(**_reference_fixture(temperature=3.5))

    assert result["mean_abs_magnetization"] < 0.2


# @id TEST-AIMS-933
# @verifies REQ-AIMS-030
def test_TEST_AIMS_933_is_deterministic_given_same_seed():
    from ai_materials_scientist.classical_monte_carlo import run_classical_monte_carlo

    params = _reference_fixture(temperature=1.5)
    result_a = run_classical_monte_carlo(**params)
    result_b = run_classical_monte_carlo(**params)

    assert result_a["mean_energy"] == pytest.approx(result_b["mean_energy"])
    assert result_a["mean_abs_magnetization"] == pytest.approx(result_b["mean_abs_magnetization"])


# @id TEST-AIMS-934
# @verifies REQ-AIMS-030
def test_TEST_AIMS_934_history_excludes_equilibration_sweeps():
    from ai_materials_scientist.classical_monte_carlo import run_classical_monte_carlo

    params = _reference_fixture(temperature=1.5)
    result = run_classical_monte_carlo(**params)

    assert len(result["history"]) == params["sampling_sweeps"]


# @id TEST-AIMS-935
# @verifies REQ-AIMS-030
def test_TEST_AIMS_935_dispatches_through_manifest():
    from ai_materials_scientist.dispatch import load_manifest

    manifest = load_manifest()
    assert (
        manifest["classical-monte-carlo"]["modulePath"]
        == "ai_materials_scientist.classical_monte_carlo"
    )
    assert manifest["classical-monte-carlo"]["functionName"] == "run_classical_monte_carlo"


# @id TEST-AIMS-936
# @verifies REQ-AIMS-003
def test_TEST_AIMS_936_rejects_wrong_shaped_initial_spins():
    from ai_materials_scientist.classical_monte_carlo import run_classical_monte_carlo

    params = _reference_fixture(temperature=1.5)
    params["initial_spins"] = np.ones((params["L"], params["L"] + 1), dtype=np.int64)

    with pytest.raises(ValueError, match="initial_spins"):
        run_classical_monte_carlo(**params)


# @id TEST-AIMS-937
# @verifies REQ-AIMS-003
def test_TEST_AIMS_937_rejects_non_ising_spin_values():
    from ai_materials_scientist.classical_monte_carlo import run_classical_monte_carlo

    params = _reference_fixture(temperature=1.5)
    bad_spins = params["initial_spins"].copy()
    bad_spins[0, 0] = 2
    params["initial_spins"] = bad_spins

    with pytest.raises(ValueError, match="initial_spins"):
        run_classical_monte_carlo(**params)


@pytest.mark.parametrize(
    ("overrides", "bad_parameter"),
    [
        ({"L": 0}, "L"),
        ({"L": -1}, "L"),
        ({"J": 0.0}, "J"),
        ({"J": -1.0}, "J"),
        ({"T": 0.0}, "T"),
        ({"T": -1.0}, "T"),
        ({"equilibration_sweeps": -1}, "equilibration_sweeps"),
        ({"sampling_sweeps": 0}, "sampling_sweeps"),
        ({"sampling_sweeps": -1}, "sampling_sweeps"),
    ],
)
# @id TEST-AIMS-938
# @verifies REQ-AIMS-003
def test_TEST_AIMS_938_rejects_invalid_parameters_before_any_trial_move(overrides, bad_parameter):
    from ai_materials_scientist.classical_monte_carlo import run_classical_monte_carlo

    params = _reference_fixture(temperature=1.5)
    params.update(overrides)
    initial_spins_before = params["initial_spins"].copy()

    with pytest.raises(ValueError, match=bad_parameter):
        run_classical_monte_carlo(**params)

    assert np.array_equal(params["initial_spins"], initial_spins_before)
