"""Dose-response curve fitting module (DES-ACHEM-120 / REQ-ACHEM-120).

Pure function module: no network, database, or ML-model call (ADR-0117).
"""

from __future__ import annotations

import math
import statistics

import numpy as np
from scipy.optimize import curve_fit

from ai_chemistry_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "dose-response-fitting"
_MIN_POINTS = 4


def _four_param_logistic(c, top, bottom, ic50, hill_slope):
    return bottom + (top - bottom) / (1 + (c / ic50) ** hill_slope)


def _is_finite_float_list(values) -> bool:
    return isinstance(values, list) and all(
        isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in values
    )


def _dose_response_validator(params: dict) -> dict:
    """DES-ACHEM-002 registered atomic validator for this module."""
    concentrations = params.get("concentrations")
    responses = params.get("responses")

    if not _is_finite_float_list(concentrations):
        return fail("concentrations", "must be a list of finite floats")
    if len(concentrations) < _MIN_POINTS:
        return fail("concentrations", "length must match responses and be >= 4")
    if any(c <= 0 for c in concentrations):
        return fail("concentrations", "must be a list of finite floats")

    if not _is_finite_float_list(responses):
        return fail("responses", "must be a list of finite floats")
    if len(responses) != len(concentrations):
        return fail("responses", "length must match concentrations and be >= 4")

    if len(set(responses)) < 2:
        return fail("responses", "must contain at least 2 distinct values")
    if len(set(concentrations)) < 2:
        return fail("concentrations", "must contain at least 2 distinct values")

    return ok()


register_validator(_MODULE_NAME, _dose_response_validator)


# @id CODE-ACHEM-120
# @implements REQ-ACHEM-120
# @design DES-ACHEM-120
def run_dose_response_fit(concentrations: list[float], responses: list[float]) -> dict:
    """Fit the 4-parameter logistic (Hill) model via nonlinear least squares.

    Receives already-validated ``concentrations``/``responses`` (its
    handler wrapper's DES-ACHEM-002 call); a convergence failure or a
    converged-but-nonphysical fit raises ``ValueError`` per ADR-0117's
    shared post-fit policy, distinct from the pre-fit dict-shape
    validation above.
    """
    concentrations_arr = np.asarray(concentrations, dtype=np.float64)
    responses_arr = np.asarray(responses, dtype=np.float64)

    p0 = [
        max(responses),
        min(responses),
        statistics.median(concentrations),
        1.0,
    ]
    try:
        fitted, _ = curve_fit(
            _four_param_logistic,
            concentrations_arr,
            responses_arr,
            p0=p0,
            maxfev=10000,
        )
    except RuntimeError as exc:
        raise ValueError("concentrations/responses: fit did not converge") from exc

    top, bottom, ic50, hill_slope = fitted
    if not all(math.isfinite(v) for v in fitted) or ic50 <= 0:
        raise ValueError("concentrations/responses: fitted parameters must be finite with ic50 > 0")

    predicted = _four_param_logistic(concentrations_arr, top, bottom, ic50, hill_slope)
    residual_ss = float(np.sum((responses_arr - predicted) ** 2))
    total_ss = float(np.sum((responses_arr - np.mean(responses_arr)) ** 2))
    r_squared = 1 - residual_ss / total_ss

    return {
        "top": float(top),
        "bottom": float(bottom),
        "ic50": float(ic50),
        "hill_slope": float(hill_slope),
        "r_squared": float(r_squared),
    }
