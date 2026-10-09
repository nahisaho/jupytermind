"""Statistical analysis.

Implements DES-AIDS-008 (REQ-AIDS-006): correlation/statistical tests
reported alongside a natural-language interpretation in the requested
response language. DES-AIDS-106 (REQ-AIDS-106) extends this module with
a single-covariate Cox proportional-hazards regression wrapping
`statsmodels.duration.hazard_regression.PHReg`. DES-AIDS-107
(REQ-AIDS-107) further extends this module with a non-parametric
Kaplan-Meier survival-function estimate wrapping
`statsmodels.duration.survfunc.SurvfuncRight`.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.tools.sm_exceptions
from scipy import stats as scipy_stats
from statsmodels.duration.hazard_regression import PHReg
from statsmodels.duration.survfunc import SurvfuncRight


@dataclass(frozen=True)
class StatResult:
    statistic: float
    p_value: float
    interpretation: str


def p_display(p_value: float) -> str:
    """Format ``p_value`` for display, bounding near-zero values (DES-AIDS-053).

    Change: CHANGE-004 (REQ-AIDS-065).
    """
    if p_value < 1e-4:
        return "p < 1e-4"
    return f"p={p_value:.4g}"


# @id CODE-AIDS-087
# @implements REQ-AIDS-067
# @design DES-AIDS-055
def _interpret(
    r: float,
    p_value: float,
    language: str,
    significance_threshold: float = 0.05,
) -> str:
    if math.isnan(r) or math.isnan(p_value):
        if language == "ja":
            return "相関係数を算出できません(統計量がNaNです)。欠損値を確認してください。"
        return (
            "The correlation could not be computed (the statistic is NaN); "
            "check the input columns for missing values."
        )
    p_text = p_display(p_value)
    if p_value >= significance_threshold:
        if language == "ja":
            return f"相関係数は {r:.4f} ({p_text}) で、統計的に明確な相関は見られません。"
        return (
            f"The correlation coefficient is {r:.4f} ({p_text}), and no "
            "statistically clear correlation is observed."
        )
    strength = "strong" if abs(r) >= 0.7 else "moderate" if abs(r) >= 0.3 else "weak"
    direction = "positive" if r >= 0 else "negative"
    if language == "ja":
        strength_ja = {"strong": "強い", "moderate": "中程度の", "weak": "弱い"}[strength]
        direction_ja = "正" if r >= 0 else "負"
        return f"相関係数は {r:.4f} ({p_text}) で、{strength_ja}{direction_ja}の相関が見られます。"
    return (
        f"The correlation coefficient is {r:.4f} ({p_text}), indicating a "
        f"{strength} {direction} correlation."
    )


def _is_finite_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _is_event_flag(value) -> bool:
    if isinstance(value, bool):
        return True
    return isinstance(value, int) and value in (0, 1)


def _event_value(value) -> int:
    return int(value)


# @id CODE-AIDS-160
# @implements REQ-AIDS-106
# @design DES-AIDS-106
def cox_ph_regression(
    durations: list[float], events: list[int], covariate: list[float]
) -> dict[str, float]:
    """Fit a single-covariate Cox proportional-hazards model via `statsmodels.PHReg`.

    Pure function: no network, database, or ML-model call (DES-AIDS-106).
    """
    if not isinstance(durations, list) or not all(_is_finite_number(v) for v in durations):
        raise ValueError("durations: must be a list of finite numbers")
    if not isinstance(covariate, list) or not all(_is_finite_number(v) for v in covariate):
        raise ValueError("covariate: must be a list of finite numbers")
    if len(durations) != len(covariate):
        raise ValueError("durations, covariate: must be the same length")
    if len(durations) < 2:
        raise ValueError("durations, covariate: must contain at least 2 entries")
    if any(d <= 0 for d in durations):
        raise ValueError("durations: must be strictly positive")
    if len(set(covariate)) < 2:
        raise ValueError("covariate: must not be all-identical")

    if not isinstance(events, list) or not all(_is_event_flag(v) for v in events):
        raise ValueError("events: must be a list of 0/1 or boolean values")
    if len(events) != len(durations):
        raise ValueError("durations, events: must be the same length")
    events_int = [_event_value(v) for v in events]
    if sum(events_int) < 2:
        raise ValueError("events: must contain at least 2 events")

    durations_array = np.asarray(durations, dtype=np.float64)
    events_array = np.asarray(events_int, dtype=np.int64)
    covariate_column = np.asarray(covariate, dtype=np.float64).reshape(-1, 1)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", statsmodels.tools.sm_exceptions.ConvergenceWarning)
        try:
            result = PHReg(durations_array, covariate_column, status=events_array).fit()
        except Exception as exc:
            raise ValueError("durations, covariate: fit did not converge") from exc

        converged = not any(
            issubclass(w.category, statsmodels.tools.sm_exceptions.ConvergenceWarning)
            for w in caught
        )

    coefficient = float(result.params[0])
    standard_error = float(result.bse[0])
    p_value = float(result.pvalues[0])

    if (
        not converged
        or not math.isfinite(coefficient)
        or not math.isfinite(standard_error)
        or not math.isfinite(p_value)
    ):
        raise ValueError("durations, covariate: fit did not converge")

    hazard_ratio = math.exp(coefficient)
    ci_lower = math.exp(coefficient - 1.96 * standard_error)
    ci_upper = math.exp(coefficient + 1.96 * standard_error)

    return {
        "coefficient": coefficient,
        "standard_error": standard_error,
        "p_value": p_value,
        "hazard_ratio": hazard_ratio,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
    }


# @id CODE-AIDS-161
# @implements REQ-AIDS-107
# @design DES-AIDS-107
def kaplan_meier_estimate(durations: list[float], events: list[int]) -> dict[str, list[float]]:
    """Estimate the Kaplan-Meier survival curve via `statsmodels.SurvfuncRight`.

    Pure function: no network, database, or ML-model call (DES-AIDS-107).
    """
    if not isinstance(durations, list) or not all(_is_finite_number(v) for v in durations):
        raise ValueError("durations: must be a list of finite numbers")
    if len(durations) < 1:
        raise ValueError("durations: must contain at least 1 entry")
    if any(d <= 0 for d in durations):
        raise ValueError("durations: must be positive")

    if not isinstance(events, list) or not all(_is_event_flag(v) for v in events):
        raise ValueError("events: must be a list of 0/1 or boolean values")
    if len(events) != len(durations):
        raise ValueError("durations, events: must be the same length")
    events_int = [_event_value(v) for v in events]
    if sum(events_int) < 1:
        raise ValueError("events: must contain at least 1 event")

    durations_array = np.asarray(durations, dtype=np.float64)
    events_array = np.asarray(events_int, dtype=np.int64)

    surv = SurvfuncRight(durations_array, events_array)

    return {
        "times": [float(t) for t in surv.surv_times],
        "survival_prob": [float(p) for p in surv.surv_prob],
        "survival_se": [float(se) for se in surv.surv_prob_se],
    }


# @id CODE-AIDS-006
# @implements REQ-AIDS-006 REQ-AIDS-063 REQ-AIDS-065
# @design DES-AIDS-008 DES-AIDS-051 DES-AIDS-053
def correlation(
    df: pd.DataFrame,
    col_a: str,
    col_b: str,
    language: str = "en",
    significance_threshold: float = 0.05,
) -> StatResult:
    """Compute the Pearson correlation between two columns of ``df``."""
    if not 0.0 <= significance_threshold <= 1.0:
        raise ValueError("significance_threshold must be within [0.0, 1.0].")
    r, p_value = scipy_stats.pearsonr(df[col_a], df[col_b])
    return StatResult(
        statistic=float(r),
        p_value=float(p_value),
        interpretation=_interpret(float(r), float(p_value), language, significance_threshold),
    )
