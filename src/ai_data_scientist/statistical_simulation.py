"""Bootstrap confidence intervals and statistical power analysis.

Implements DES-AIDS-109 (REQ-AIDS-109): `bootstrap_confidence_interval`
via `scipy.stats.bootstrap` and `power_analysis` via
`statsmodels.stats.power.TTestIndPower`.

Change: CHANGE-039
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats as scipy_stats
from statsmodels.stats.power import TTestIndPower


def _is_finite_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _is_finite_positive(value) -> bool:
    return _is_finite_number(value) and value > 0


# @id CODE-AIDS-163
# @implements REQ-AIDS-109
# @design DES-AIDS-109
def bootstrap_confidence_interval(
    data: list[float],
    statistic: str = "mean",
    confidence_level: float = 0.95,
    n_resamples: int = 2000,
    random_state: int | None = 42,
) -> dict[str, float]:
    """Compute a bootstrap confidence interval for the sample mean.

    Pure function: no network, database, or ML-model call (DES-AIDS-109).
    """
    if not isinstance(data, list) or len(data) < 2 or not all(_is_finite_number(v) for v in data):
        raise ValueError("data: must be a list of >= 2 finite numbers")
    if statistic != "mean":
        raise ValueError("statistic: must be 'mean'")
    if not _is_finite_number(confidence_level) or not (0 < confidence_level < 1):
        raise ValueError("confidence_level: must be in (0, 1)")
    if not isinstance(n_resamples, int) or isinstance(n_resamples, bool) or n_resamples < 1:
        raise ValueError("n_resamples: must be a positive integer")
    if random_state is not None and (
        not isinstance(random_state, int) or isinstance(random_state, bool) or random_state < 0
    ):
        raise ValueError("random_state: must be None or a non-negative integer")

    result = scipy_stats.bootstrap(
        (data,),
        np.mean,
        confidence_level=confidence_level,
        n_resamples=n_resamples,
        random_state=random_state,
        method="percentile",
    )
    return {
        "low": float(result.confidence_interval.low),
        "high": float(result.confidence_interval.high),
    }


# @id CODE-AIDS-164
# @implements REQ-AIDS-109
# @design DES-AIDS-109
def power_analysis(
    effect_size: float,
    alpha: float = 0.05,
    nobs1: float | None = None,
    power: float | None = None,
    ratio: float = 1.0,
) -> dict[str, float]:
    """Compute the missing value of nobs1/power via `TTestIndPower`.

    Pure function: no network, database, or ML-model call (DES-AIDS-109).
    """
    if (nobs1 is None) == (power is None):
        raise ValueError("nobs1, power: exactly one of nobs1/power must be None")
    if not _is_finite_positive(effect_size):
        raise ValueError("effect_size: must be a finite positive number")
    if not _is_finite_number(alpha) or not (0 < alpha < 1):
        raise ValueError("alpha: must be in (0, 1)")
    if not _is_finite_positive(ratio):
        raise ValueError("ratio: must be a finite positive number")
    if power is not None and (not _is_finite_number(power) or not (0 < power < 1)):
        raise ValueError("power: must be in (0, 1)")
    if nobs1 is not None and not _is_finite_positive(nobs1):
        raise ValueError("nobs1: must be a finite number > 0")

    analysis = TTestIndPower()
    if power is None:
        computed_power = analysis.power(
            effect_size=effect_size, nobs1=nobs1, alpha=alpha, ratio=ratio
        )
        return {"nobs1": float(nobs1), "power": float(computed_power)}
    computed_nobs1 = analysis.solve_power(
        effect_size=effect_size, power=power, alpha=alpha, ratio=ratio
    )
    return {"nobs1": float(computed_nobs1), "power": float(power)}
