"""Kinetic Monte Carlo event-driven evolution module (DES-AIMS-040 / REQ-AIMS-040)."""

from __future__ import annotations

import numpy as np

from ai_materials_scientist.evidence import record_run
from ai_materials_scientist.validation import (
    check_finite_array,
    register_validator,
    validate_parameters,
)

_MODULE_NAME = "kinetic-monte-carlo"
_NUM_REALIZATIONS = 200
_HOP_DIRECTIONS = np.array([[1, 0], [-1, 0], [0, 1], [0, -1]])


def _kmc_validator(params: dict) -> dict:
    """DES-AIMS-002 registered validator for module_name='kinetic-monte-carlo'."""
    gamma = params["gamma"]
    a = params["a"]
    total_time = params["total_time"]
    output_times = params["output_times"]

    if gamma <= 0:
        return {"ok": False, "parameter": "gamma", "constraint": "gamma > 0"}
    if a <= 0:
        return {"ok": False, "parameter": "a", "constraint": "a > 0"}
    if total_time <= 0:
        return {"ok": False, "parameter": "total_time", "constraint": "total_time > 0"}
    if len(output_times) == 0:
        return {
            "ok": False,
            "parameter": "output_times",
            "constraint": "output_times must be non-empty",
        }
    finite_check = check_finite_array("output_times", np.asarray(output_times, dtype=np.float64))
    if not finite_check["ok"]:
        return finite_check
    for output_time in output_times:
        if not (0 < output_time <= total_time):
            return {
                "ok": False,
                "parameter": "output_time",
                "constraint": "0 < output_time <= total_time",
            }
    return {"ok": True}


register_validator(_MODULE_NAME, _kmc_validator)


def _validate(gamma, a, total_time, output_times) -> None:
    result = validate_parameters(
        _MODULE_NAME,
        {"gamma": gamma, "a": a, "total_time": total_time, "output_times": output_times},
    )
    if not result["ok"]:
        raise ValueError(f"{result['parameter']}: {result['constraint']}")


# @id CODE-AIMS-040
# @implements REQ-AIMS-040
# @design DES-AIMS-040
def run_kmc_single_realization(
    gamma: float, a: float, total_time: float, seed: int
) -> list[tuple[float, np.ndarray]]:
    """Run one rejection-free (BKL) realization; never advances past total_time.

    Returns the list of (event_time, unwrapped_position) pairs, starting
    with the step-zero event (0.0, origin).
    """
    rng = np.random.default_rng(seed)
    total_rate = 4.0 * gamma
    t = 0.0
    pos = np.zeros(2)
    events: list[tuple[float, np.ndarray]] = [(t, pos.copy())]

    while True:
        dt = rng.exponential(1.0 / total_rate)
        if t + dt > total_time:
            break
        t = t + dt
        direction = rng.integers(0, 4)
        pos = pos + _HOP_DIRECTIONS[direction] * a
        events.append((t, pos.copy()))

    return events


def _displacement_at(events: list[tuple[float, np.ndarray]], query_time: float) -> np.ndarray:
    """Displacement after the last event at or before query_time."""
    last_position = events[0][1]
    for event_time, position in events:
        if event_time > query_time:
            break
        last_position = position
    return last_position


# @id CODE-AIMS-907
# @implements REQ-AIMS-040 REQ-AIMS-003
# @design DES-AIMS-040
def run_kinetic_monte_carlo(
    gamma: float, a: float, total_time: float, output_times: list[float], base_seed: int
) -> dict:
    """Run 200 independent BKL realizations and report displacements (REQ-AIMS-040).

    Rejects any out-of-domain parameter (REQ-AIMS-003) before any hop event
    is drawn.
    """
    _validate(gamma, a, total_time, output_times)

    realization_seeds = [base_seed + i for i in range(_NUM_REALIZATIONS)]
    displacements = np.zeros((len(output_times), _NUM_REALIZATIONS, 2))

    for realization_index, seed in enumerate(realization_seeds):
        events = run_kmc_single_realization(gamma, a, total_time, seed)
        for time_index, query_time in enumerate(output_times):
            displacements[time_index, realization_index] = _displacement_at(events, query_time)

    return {
        "displacements": displacements,
        "times": list(output_times),
        "realization_seeds": realization_seeds,
    }


# @id CODE-AIMS-908
# @implements REQ-AIMS-040 REQ-AIMS-004 REQ-AIMS-005
# @design DES-AIMS-040
def run_kinetic_monte_carlo_with_evidence(**kwargs) -> dict:
    """Run kinetic Monte Carlo and wrap the result as a reproducible RunRecord."""
    result = run_kinetic_monte_carlo(**kwargs)
    return record_run(
        module_name=_MODULE_NAME,
        unit_system="lattice-hop-reduced",
        params={k: v for k, v in kwargs.items() if k != "output_times"},
        arrays={
            "displacements": result["displacements"],
            "times": np.array(result["times"], dtype=np.float64),
        },
        seed=kwargs["base_seed"],
    )
