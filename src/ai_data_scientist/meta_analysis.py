"""Meta-analysis effect-size pooling (DES-AIDS-103 / REQ-AIDS-103).

Pure function module: no network, database, or ML-model call.
"""

from __future__ import annotations

import math


def _is_finite_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _is_finite_positive_float(value) -> bool:
    return (
        isinstance(value, float)
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0
    )


# @id CODE-AIDS-157
# @implements REQ-AIDS-103
# @design DES-AIDS-103
def pool_effect_sizes(effects: list[float], standard_errors: list[float]) -> dict[str, float]:
    """Pool per-study effect sizes via fixed-effect and DerSimonian-Laird random-effects models."""
    if not isinstance(effects, list) or not all(_is_finite_number(v) for v in effects):
        raise ValueError("effects: must be a list of finite numbers")
    if not isinstance(standard_errors, list) or not all(
        _is_finite_positive_float(v) for v in standard_errors
    ):
        raise ValueError("standard_errors: must be a list of finite floats greater than 0")
    if len(effects) != len(standard_errors):
        raise ValueError("effects, standard_errors: must be the same length")
    if len(effects) < 2:
        raise ValueError("effects, standard_errors: must contain at least 2 studies")
    if any(se**2 == 0.0 for se in standard_errors):
        raise ValueError(
            "standard_errors: value too small, squared standard error underflows to zero"
        )

    k = len(effects)
    weights = [1.0 / se**2 for se in standard_errors]
    sum_w = sum(weights)
    pooled_fe = sum(w * e for w, e in zip(weights, effects)) / sum_w
    se_fe = math.sqrt(1.0 / sum_w)

    df = k - 1
    q_statistic = sum(w * (e - pooled_fe) ** 2 for w, e in zip(weights, effects))
    i_squared = 0.0 if q_statistic == 0 else max(0.0, (q_statistic - df) / q_statistic * 100)

    sum_w_sq = sum(w**2 for w in weights)
    tau_squared = max(0.0, (q_statistic - df) / (sum_w - sum_w_sq / sum_w))

    weights_re = [1.0 / (se**2 + tau_squared) for se in standard_errors]
    sum_w_re = sum(weights_re)
    pooled_re = sum(w * e for w, e in zip(weights_re, effects)) / sum_w_re
    se_re = math.sqrt(1.0 / sum_w_re)

    return {
        "pooled_fe": pooled_fe,
        "se_fe": se_fe,
        "q_statistic": q_statistic,
        "i_squared": i_squared,
        "tau_squared": tau_squared,
        "pooled_re": pooled_re,
        "se_re": se_re,
    }
