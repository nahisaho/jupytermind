"""Pharmacokinetic non-compartmental analysis module (DES-ACHEM-130 / REQ-ACHEM-130).

Pure function module: no network, database, or ML-model call (ADR-0117).
"""

from __future__ import annotations

import math

import numpy as np

from ai_chemistry_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "pharmacokinetic-analysis"
_MIN_POINTS = 4


def _is_finite_float_list(values) -> bool:
    return isinstance(values, list) and all(
        isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in values
    )


def _pharmacokinetics_validator(params: dict) -> dict:
    """DES-ACHEM-002 registered atomic validator for this module."""
    times = params.get("times")
    concentrations = params.get("concentrations")
    dose = params.get("dose")
    n_terminal = params.get("n_terminal", 3)

    if not _is_finite_float_list(times):
        return fail("times", "must be a list of strictly increasing finite floats")
    if len(times) < _MIN_POINTS:
        return fail("times", "must be a list of strictly increasing finite floats, length >= 4")
    if any(times[i] >= times[i + 1] for i in range(len(times) - 1)):
        return fail("times", "must be a list of strictly increasing finite floats")

    if not _is_finite_float_list(concentrations):
        return fail("concentrations", "must be a list of finite floats > 0")
    if len(concentrations) != len(times):
        return fail("concentrations", "must be the same length as times")
    if any(c <= 0 for c in concentrations):
        return fail("concentrations", "must be a list of finite floats > 0")

    if (
        not isinstance(dose, (int, float))
        or isinstance(dose, bool)
        or not math.isfinite(dose)
        or dose <= 0
    ):
        return fail("dose", "must be a finite float > 0")

    if (
        not isinstance(n_terminal, int)
        or isinstance(n_terminal, bool)
        or not (2 <= n_terminal <= len(times))
    ):
        return fail("n_terminal", "must be an integer in [2, len(times)]")

    return ok()


register_validator(_MODULE_NAME, _pharmacokinetics_validator)


# @id CODE-ACHEM-130
# @implements REQ-ACHEM-130
# @design DES-ACHEM-130
def run_pharmacokinetics(
    times: list[float],
    concentrations: list[float],
    dose: float,
    n_terminal: int = 3,
) -> dict:
    """Compute standard non-compartmental PK parameters.

    Receives already-validated ``times``/``concentrations``/``dose``/
    ``n_terminal`` (its handler wrapper's DES-ACHEM-002 call); a
    non-finite or non-positive terminal elimination rate constant raises
    ``ValueError`` per ADR-0118, before any of the four derived fields
    that depend on it are ever computed.
    """
    times_arr = np.asarray(times, dtype=np.float64)
    concentrations_arr = np.asarray(concentrations, dtype=np.float64)

    cmax = float(np.max(concentrations_arr))
    tmax = float(times_arr[int(np.argmax(concentrations_arr))])
    auc_last = float(np.trapezoid(concentrations_arr, times_arr))

    terminal_times = times_arr[-n_terminal:]
    terminal_log_concentrations = np.log(concentrations_arr[-n_terminal:])
    slope, _intercept = np.polyfit(terminal_times, terminal_log_concentrations, deg=1)
    k_el = float(-slope)

    if not math.isfinite(k_el) or k_el <= 0:
        raise ValueError(
            "concentrations/n_terminal: terminal concentrations must yield a positive "
            "elimination rate constant"
        )

    half_life = math.log(2) / k_el
    auc_inf = auc_last + concentrations[-1] / k_el
    clearance = dose / auc_inf
    volume_of_distribution = clearance / k_el

    return {
        "cmax": float(cmax),
        "tmax": float(tmax),
        "auc_last": float(auc_last),
        "auc_inf": float(auc_inf),
        "k_el": float(k_el),
        "half_life": float(half_life),
        "clearance": float(clearance),
        "volume_of_distribution": float(volume_of_distribution),
    }
