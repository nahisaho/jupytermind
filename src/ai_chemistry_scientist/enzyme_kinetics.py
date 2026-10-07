"""Michaelis-Menten enzyme kinetics module (DES-ACHEM-140 / REQ-ACHEM-140).

Pure function module: no network, database, or ML-model call (ADR-0117).
"""

from __future__ import annotations

import math
import statistics

import numpy as np
from scipy.optimize import curve_fit

from ai_chemistry_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "enzyme-kinetics"
_MIN_POINTS = 3


def _michaelis_menten(s, vmax, km):
    return vmax * s / (km + s)


def _is_finite_float_list(values) -> bool:
    return isinstance(values, list) and all(
        isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in values
    )


def _enzyme_kinetics_validator(params: dict) -> dict:
    """DES-ACHEM-002 registered atomic validator for this module."""
    substrate_concentrations = params.get("substrate_concentrations")
    velocities = params.get("velocities")

    if not _is_finite_float_list(substrate_concentrations):
        return fail("substrate_concentrations", "must be a list of finite floats")
    if len(substrate_concentrations) < _MIN_POINTS:
        return fail(
            "substrate_concentrations",
            "length must match velocities and be >= 3",
        )
    if any(c <= 0 for c in substrate_concentrations):
        return fail("substrate_concentrations", "must be a list of finite floats")

    if not _is_finite_float_list(velocities):
        return fail("velocities", "must be a list of finite floats")
    if len(velocities) != len(substrate_concentrations):
        return fail("velocities", "length must match substrate_concentrations and be >= 3")

    if len(set(velocities)) < 2:
        return fail("velocities", "must contain at least 2 distinct values")
    if len(set(substrate_concentrations)) < 2:
        return fail("substrate_concentrations", "must contain at least 2 distinct values")

    return ok()


register_validator(_MODULE_NAME, _enzyme_kinetics_validator)


# @id CODE-ACHEM-140
# @implements REQ-ACHEM-140
# @design DES-ACHEM-140
def run_enzyme_kinetics(substrate_concentrations: list[float], velocities: list[float]) -> dict:
    """Fit the Michaelis-Menten model via nonlinear least squares.

    Receives already-validated ``substrate_concentrations``/``velocities``
    (its handler wrapper's DES-ACHEM-002 call); a convergence failure or a
    converged-but-nonphysical fit raises ``ValueError`` per ADR-0117's
    shared post-fit policy, distinct from the pre-fit dict-shape
    validation above.
    """
    substrate_arr = np.asarray(substrate_concentrations, dtype=np.float64)
    velocities_arr = np.asarray(velocities, dtype=np.float64)

    p0 = [max(velocities), statistics.median(substrate_concentrations)]
    try:
        fitted, _ = curve_fit(_michaelis_menten, substrate_arr, velocities_arr, p0=p0)
    except RuntimeError as exc:
        raise ValueError("substrate_concentrations/velocities: fit did not converge") from exc

    vmax, km = fitted
    if not all(math.isfinite(v) for v in fitted) or vmax <= 0 or km <= 0:
        raise ValueError(
            "substrate_concentrations/velocities: fitted parameters must be finite "
            "with vmax > 0 and km > 0"
        )

    predicted = _michaelis_menten(substrate_arr, vmax, km)
    residual_ss = float(np.sum((velocities_arr - predicted) ** 2))
    total_ss = float(np.sum((velocities_arr - np.mean(velocities_arr)) ** 2))
    r_squared = 1 - residual_ss / total_ss

    return {
        "vmax": float(vmax),
        "km": float(km),
        "r_squared": float(r_squared),
    }
