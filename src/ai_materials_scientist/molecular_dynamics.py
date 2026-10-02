"""Molecular dynamics trajectory integration module (DES-AIMS-020 / REQ-AIMS-020)."""

from __future__ import annotations

import numpy as np

from ai_materials_scientist.evidence import record_run
from ai_materials_scientist.validation import (
    check_finite_array,
    check_positive_output_interval,
    check_positive_step_count,
    register_validator,
    validate_parameters,
)

_MODULE_NAME = "molecular-dynamics"
_MIN_SEPARATION_SIGMA = 0.8


# @id CODE-AIMS-020
# @implements REQ-AIMS-020
# @design DES-AIMS-020
def compute_dt_bound(epsilon: float, sigma: float, mass: float) -> float:
    """Conservative explicit stability bound dt_bound = 0.005*sigma*sqrt(mass/epsilon)."""
    return 0.005 * sigma * (mass / epsilon) ** 0.5


def _minimum_image_displacements(positions: np.ndarray, box_length: float) -> np.ndarray:
    """Pairwise displacement[i, j] = positions[i] - positions[j] under min-image."""
    diff = positions[:, None, :] - positions[None, :, :]
    return diff - box_length * np.round(diff / box_length)


def _pair_distances(positions: np.ndarray, box_length: float) -> np.ndarray:
    disp = _minimum_image_displacements(positions, box_length)
    dist = np.sqrt(np.sum(disp**2, axis=-1))
    np.fill_diagonal(dist, np.inf)
    return dist


def _lj_potential(r: np.ndarray, epsilon: float, sigma: float) -> np.ndarray:
    sr6 = (sigma / r) ** 6
    return 4 * epsilon * (sr6**2 - sr6)


def _lj_radial_force_magnitude(r: np.ndarray, epsilon: float, sigma: float) -> np.ndarray:
    """F(r) = -dU/dr; positive is repulsive."""
    sr6 = (sigma / r) ** 6
    return 24 * epsilon / r * (2 * sr6**2 - sr6)


def _forces_and_potential(
    positions: np.ndarray, box_length: float, cutoff: float, epsilon: float, sigma: float
) -> tuple[np.ndarray, float]:
    """Shifted-force Lennard-Jones forces (per particle) and total pair potential."""
    n = positions.shape[0]
    disp = _minimum_image_displacements(positions, box_length)
    dist = np.sqrt(np.sum(disp**2, axis=-1))
    np.fill_diagonal(dist, np.inf)

    within_cutoff = dist < cutoff
    f_cutoff = _lj_radial_force_magnitude(np.array(cutoff), epsilon, sigma)
    u_cutoff = _lj_potential(np.array(cutoff), epsilon, sigma)

    forces = np.zeros_like(positions)
    total_potential = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            if not within_cutoff[i, j]:
                continue
            r = dist[i, j]
            f_shifted = _lj_radial_force_magnitude(r, epsilon, sigma) - f_cutoff
            u_shifted = _lj_potential(r, epsilon, sigma) - u_cutoff - (r - cutoff) * (-f_cutoff)
            unit_vec = disp[i, j] / r
            force_on_i = f_shifted * unit_vec
            forces[i] += force_on_i
            forces[j] -= force_on_i
            total_potential += u_shifted
    return forces, total_potential


def _md_validator(params: dict) -> dict:
    """DES-AIMS-002 registered validator for module_name='molecular-dynamics'."""
    lj_params = params["lj_params"]
    mass = lj_params["mass"]
    epsilon = lj_params["epsilon"]
    sigma = lj_params["sigma"]
    box_length = params["box_length"]
    cutoff = params["cutoff"]
    dt = params["dt"]

    if mass <= 0:
        return {"ok": False, "parameter": "mass", "constraint": "mass > 0"}
    if epsilon <= 0:
        return {"ok": False, "parameter": "epsilon", "constraint": "epsilon > 0"}
    if sigma <= 0:
        return {"ok": False, "parameter": "sigma", "constraint": "sigma > 0"}
    if box_length <= 0:
        return {"ok": False, "parameter": "box_length", "constraint": "box_length > 0"}
    if dt <= 0:
        return {"ok": False, "parameter": "dt", "constraint": "dt > 0"}
    if cutoff <= 0:
        return {"ok": False, "parameter": "cutoff", "constraint": "cutoff > 0"}

    positions_check = check_finite_array("positions0", params["positions0"])
    if not positions_check["ok"]:
        return positions_check
    velocities_check = check_finite_array("velocities0", params["velocities0"])
    if not velocities_check["ok"]:
        return velocities_check
    steps_check = check_positive_step_count(params["steps"])
    if not steps_check["ok"]:
        return steps_check
    interval_check = check_positive_output_interval(params["output_every"])
    if not interval_check["ok"]:
        return interval_check

    if cutoff > box_length / 2:
        return {
            "ok": False,
            "parameter": "cutoff",
            "constraint": "cutoff <= box_length / 2",
        }

    distances = _pair_distances(params["positions0"], box_length)
    min_separation = _MIN_SEPARATION_SIGMA * sigma
    if np.any(distances < min_separation):
        return {
            "ok": False,
            "parameter": "positions0",
            "constraint": f"every pairwise separation >= {min_separation} (0.8*sigma)",
        }

    dt_bound = compute_dt_bound(epsilon, sigma, mass)
    if dt > dt_bound:
        return {
            "ok": False,
            "parameter": "dt",
            "constraint": f"dt <= dt_bound ({dt_bound})",
        }
    return {"ok": True}


register_validator(_MODULE_NAME, _md_validator)


def _validate(positions0, velocities0, lj_params, box_length, cutoff, dt, steps, output_every):
    result = validate_parameters(
        _MODULE_NAME,
        {
            "positions0": positions0,
            "velocities0": velocities0,
            "lj_params": lj_params,
            "box_length": box_length,
            "cutoff": cutoff,
            "dt": dt,
            "steps": steps,
            "output_every": output_every,
        },
    )
    if not result["ok"]:
        raise ValueError(f"{result['parameter']}: {result['constraint']}")


# @id CODE-AIMS-909
# @implements REQ-AIMS-020 REQ-AIMS-003
# @design DES-AIMS-020
def run_molecular_dynamics(
    positions0: np.ndarray,
    velocities0: np.ndarray,
    lj_params: dict,
    box_length: float,
    cutoff: float,
    dt: float,
    steps: int,
    output_every: int,
) -> dict:
    """Integrate Newton's equations of motion with velocity-Verlet (REQ-AIMS-020).

    Rejects any out-of-domain parameter (REQ-AIMS-003) before performing any
    integration step or mutating ``positions0``/``velocities0``.
    """
    _validate(positions0, velocities0, lj_params, box_length, cutoff, dt, steps, output_every)

    epsilon = lj_params["epsilon"]
    sigma = lj_params["sigma"]
    mass = lj_params["mass"]

    positions = positions0.astype(np.float64).copy()
    velocities = velocities0.astype(np.float64).copy()

    def _kinetic(v: np.ndarray) -> float:
        return float(0.5 * mass * np.sum(v**2))

    forces, potential = _forces_and_potential(positions, box_length, cutoff, epsilon, sigma)
    accel = forces / mass

    snapshots = [{"positions": positions.copy(), "velocities": velocities.copy()}]
    energies = [_kinetic(velocities) + potential]
    times = [0.0]

    for step in range(1, steps + 1):
        velocities_half = velocities + 0.5 * dt * accel
        positions = positions + dt * velocities_half
        forces, potential = _forces_and_potential(positions, box_length, cutoff, epsilon, sigma)
        accel = forces / mass
        velocities = velocities_half + 0.5 * dt * accel

        if step % output_every == 0:
            snapshots.append({"positions": positions.copy(), "velocities": velocities.copy()})
            energies.append(_kinetic(velocities) + potential)
            times.append(step * dt)

    dt_bound = compute_dt_bound(epsilon, sigma, mass)
    return {
        "snapshots": snapshots,
        "energies": energies,
        "times": times,
        "dt_bound": dt_bound,
    }


# @id CODE-AIMS-910
# @implements REQ-AIMS-020 REQ-AIMS-004 REQ-AIMS-005
# @design DES-AIMS-020
def run_molecular_dynamics_with_evidence(**kwargs) -> dict:
    """Run molecular dynamics and wrap the result as a reproducible RunRecord."""
    result = run_molecular_dynamics(**kwargs)
    return record_run(
        module_name=_MODULE_NAME,
        unit_system="lennard-jones-reduced",
        params={k: v for k, v in kwargs.items() if k not in ("positions0", "velocities0")},
        arrays={
            "positions": np.stack([s["positions"] for s in result["snapshots"]]),
            "velocities": np.stack([s["velocities"] for s in result["snapshots"]]),
            "energies": np.array(result["energies"], dtype=np.float64),
            "times": np.array(result["times"], dtype=np.float64),
        },
        seed=None,
    )
