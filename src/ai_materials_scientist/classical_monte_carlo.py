"""Classical Monte Carlo lattice sampling module (DES-AIMS-030 / REQ-AIMS-030)."""

from __future__ import annotations

import numpy as np

from ai_materials_scientist.evidence import record_run
from ai_materials_scientist.validation import (
    check_finite_array,
    register_validator,
    validate_parameters,
)

_MODULE_NAME = "classical-monte-carlo"


def _total_energy_per_site(spins: np.ndarray, J: float) -> float:
    """-J * sum over unique nearest-neighbor bonds, divided by N sites."""
    n = spins.size
    right = np.roll(spins, -1, axis=1)
    down = np.roll(spins, -1, axis=0)
    bond_sum = np.sum(spins * right) + np.sum(spins * down)
    return float(-J * bond_sum / n)


def _local_field(spins: np.ndarray, i: int, j: int, L: int) -> int:
    return (
        spins[(i + 1) % L, j]
        + spins[(i - 1) % L, j]
        + spins[i, (j + 1) % L]
        + spins[i, (j - 1) % L]
    )


def _sweep(spins: np.ndarray, L: int, J: float, T: float, rng: np.random.Generator) -> None:
    """One raster-order full-lattice sweep of single-site Metropolis trial moves."""
    random_values = rng.random((L, L))
    for i in range(L):
        for j in range(L):
            s = spins[i, j]
            neighbor_sum = _local_field(spins, i, j, L)
            delta_e = 2.0 * J * s * neighbor_sum
            if delta_e <= 0 or random_values[i, j] < np.exp(-delta_e / T):
                spins[i, j] = -s


def _mc_validator(params: dict) -> dict:
    """DES-AIMS-002 registered validator for module_name='classical-monte-carlo'."""
    if params["L"] <= 0:
        return {"ok": False, "parameter": "L", "constraint": "L > 0"}
    if params["J"] <= 0:
        return {"ok": False, "parameter": "J", "constraint": "J > 0"}
    if params["T"] <= 0:
        return {"ok": False, "parameter": "T", "constraint": "T > 0"}
    if params["equilibration_sweeps"] < 0:
        return {
            "ok": False,
            "parameter": "equilibration_sweeps",
            "constraint": "equilibration_sweeps >= 0",
        }
    if params["sampling_sweeps"] <= 0:
        return {
            "ok": False,
            "parameter": "sampling_sweeps",
            "constraint": "sampling_sweeps > 0",
        }
    initial_spins = params["initial_spins"]
    finite_check = check_finite_array("initial_spins", initial_spins)
    if not finite_check["ok"]:
        return finite_check
    if initial_spins.shape != (params["L"], params["L"]):
        return {
            "ok": False,
            "parameter": "initial_spins",
            "constraint": "initial_spins.shape == (L, L)",
        }
    if not np.all(np.isin(initial_spins, (-1, 1))):
        return {
            "ok": False,
            "parameter": "initial_spins",
            "constraint": "every spin must be +1 or -1",
        }
    return {"ok": True}


register_validator(_MODULE_NAME, _mc_validator)


def _validate(L, J, T, equilibration_sweeps, sampling_sweeps, initial_spins) -> None:
    result = validate_parameters(
        _MODULE_NAME,
        {
            "L": L,
            "J": J,
            "T": T,
            "equilibration_sweeps": equilibration_sweeps,
            "sampling_sweeps": sampling_sweeps,
            "initial_spins": initial_spins,
        },
    )
    if not result["ok"]:
        raise ValueError(f"{result['parameter']}: {result['constraint']}")


# @id CODE-AIMS-030
# @implements REQ-AIMS-030 REQ-AIMS-003
# @design DES-AIMS-030
def run_classical_monte_carlo(
    L: int,
    J: float,
    T: float,
    equilibration_sweeps: int,
    sampling_sweeps: int,
    seed: int,
    initial_spins: np.ndarray,
) -> dict:
    """Run Metropolis-criterion single-site Ising sweeps (REQ-AIMS-030).

    Rejects any out-of-domain parameter (REQ-AIMS-003) before any spin-flip
    trial move, and never mutates ``initial_spins``.
    """
    _validate(L, J, T, equilibration_sweeps, sampling_sweeps, initial_spins)

    spins = initial_spins.astype(np.int64).copy()
    rng = np.random.default_rng(seed)

    for _ in range(equilibration_sweeps):
        _sweep(spins, L, J, T, rng)

    history = []
    for _ in range(sampling_sweeps):
        _sweep(spins, L, J, T, rng)
        energy_per_site = _total_energy_per_site(spins, J)
        magnetization_per_site = float(np.sum(spins)) / spins.size
        history.append(
            {"energy_per_site": energy_per_site, "magnetization_per_site": magnetization_per_site}
        )

    mean_energy = float(np.mean([h["energy_per_site"] for h in history]))
    mean_abs_magnetization = float(np.mean([abs(h["magnetization_per_site"]) for h in history]))

    return {
        "mean_energy": mean_energy,
        "mean_abs_magnetization": mean_abs_magnetization,
        "history": history,
    }


# @id CODE-AIMS-901
# @implements REQ-AIMS-030 REQ-AIMS-004 REQ-AIMS-005
# @design DES-AIMS-030
def run_classical_monte_carlo_with_evidence(**kwargs) -> dict:
    """Run classical Monte Carlo and wrap the result as a reproducible RunRecord."""
    result = run_classical_monte_carlo(**kwargs)
    energies = np.array([h["energy_per_site"] for h in result["history"]], dtype=np.float64)
    magnetizations = np.array(
        [h["magnetization_per_site"] for h in result["history"]], dtype=np.float64
    )
    return record_run(
        module_name=_MODULE_NAME,
        unit_system="ising-reduced",
        params={k: v for k, v in kwargs.items() if k != "initial_spins"},
        arrays={"energy_history": energies, "magnetization_history": magnetizations},
        seed=kwargs["seed"],
    )
