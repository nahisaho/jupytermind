"""A/B testing and experiment evaluation.

Implements DES-AIDS-020 (REQ-AIDS-022): computes the statistical
significance of the observed difference between two groups and reports
the result with a bilingual markdown interpretation.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

MetricFn = Callable[[pd.Series, pd.Series], float]

_SUPPORTED_TESTS = ("ttest", "paired_t", "wilcoxon", "paired_bootstrap")


# @id CODE-AIDS-101
# @implements REQ-AIDS-081
# @design DES-AIDS-069
@dataclass(frozen=True)
class ExperimentResult:
    statistic: float
    p_value: float
    interpretation: str
    confidence_interval: tuple[float, float] | None = None


def _interpret(p_value: float, language: str) -> str:
    significant = p_value < 0.05
    if language == "ja":
        verdict = "統計的に有意な差があります" if significant else "統計的に有意な差は見られません"
        return f"p値は {p_value:.4g} で、{verdict} (有意水準0.05)。"
    verdict = (
        "a statistically significant difference"
        if significant
        else "no statistically significant difference"
    )
    return f"The p-value is {p_value:.4g}, indicating {verdict} (alpha=0.05)."


def _interpret_bootstrap_interval(
    statistic: float,
    confidence_interval: tuple[float, float],
    confidence_level: float,
    language: str,
) -> str:
    percent = confidence_level * 100.0
    if language == "ja":
        return (
            f"推定された treatment-control 差は {statistic:.4g} で、"
            f"{percent:.1f}% ブートストラップ信頼区間は "
            f"[{confidence_interval[0]:.4g}, {confidence_interval[1]:.4g}] です。"
            "この経路は区間推定のみを返し、仮説検定のp値は返しません。"
        )
    return (
        f"The estimated treatment-minus-control difference is {statistic:.4g}, "
        f"with a {percent:.1f}% bootstrap confidence interval of "
        f"[{confidence_interval[0]:.4g}, {confidence_interval[1]:.4g}]. "
        "This path reports interval estimation only and does not provide a hypothesis-test "
        "p-value."
    )


def _as_numeric_series(values: pd.Series, *, name: str) -> pd.Series:
    try:
        numeric = pd.to_numeric(values, errors="raise")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must contain numeric paired values.") from exc
    if not np.isfinite(numeric.to_numpy(dtype=float, copy=False)).all():
        raise ValueError(f"{name} must contain only finite paired values.")
    return numeric


# @id CODE-AIDS-102
# @implements REQ-AIDS-079 REQ-AIDS-080 REQ-AIDS-081
# @design DES-AIDS-067 DES-AIDS-068
def _validate_paired_inputs(
    control: pd.Series,
    treatment: pd.Series,
    *,
    y_true: pd.Series | None = None,
    metric_fn: MetricFn | None = None,
    iterations: int = 1000,
    confidence_level: float = 0.95,
) -> tuple[pd.Series, pd.Series, pd.Series | None]:
    if len(control) != len(treatment):
        raise ValueError("Paired experiment tests require equal-length inputs.")
    if not control.index.equals(treatment.index):
        raise ValueError(
            "Paired experiment tests require control and treatment to share identical indexes."
        )

    control_series = _as_numeric_series(control, name="control")
    treatment_series = _as_numeric_series(treatment, name="treatment")

    if (metric_fn is None) != (y_true is None):
        raise ValueError("Paired bootstrap requires metric_fn and y_true together.")

    truth_series = None
    if y_true is not None:
        if len(y_true) != len(control):
            raise ValueError(
                "Paired bootstrap requires y_true to align with control and treatment."
            )
        if not y_true.index.equals(control.index):
            raise ValueError("Paired bootstrap requires y_true to share the paired input index.")
        truth_series = _as_numeric_series(y_true, name="y_true")

    if isinstance(iterations, bool) or int(iterations) != iterations or int(iterations) <= 0:
        raise ValueError("Paired bootstrap requires iterations to be a positive integer.")
    if not 0.0 < float(confidence_level) < 1.0:
        raise ValueError("Paired bootstrap requires confidence_level to be between 0 and 1.")

    return control_series, treatment_series, truth_series


# @id CODE-AIDS-022
# @implements REQ-AIDS-022
# @design DES-AIDS-020
def _run_independent_ttest(
    control: pd.Series,
    treatment: pd.Series,
    *,
    language: str,
) -> ExperimentResult:
    statistic, p_value = scipy_stats.ttest_ind(control, treatment)
    return ExperimentResult(
        statistic=float(statistic),
        p_value=float(p_value),
        interpretation=_interpret(float(p_value), language),
    )


# @id CODE-AIDS-103
# @implements REQ-AIDS-079 REQ-AIDS-080
# @design DES-AIDS-067 DES-AIDS-069
def _run_paired_test(
    control: pd.Series,
    treatment: pd.Series,
    *,
    test: str,
    language: str,
) -> ExperimentResult:
    control_series, treatment_series, _ = _validate_paired_inputs(control, treatment)
    if test == "paired_t":
        statistic, p_value = scipy_stats.ttest_rel(control_series, treatment_series)
    else:
        statistic, p_value = scipy_stats.wilcoxon(control_series, treatment_series)
    return ExperimentResult(
        statistic=float(statistic),
        p_value=float(p_value),
        interpretation=_interpret(float(p_value), language),
    )


def _compute_difference(
    control: pd.Series,
    treatment: pd.Series,
    *,
    y_true: pd.Series | None = None,
    metric_fn: MetricFn | None = None,
) -> float:
    if metric_fn is None:
        return float((treatment - control).mean())
    assert y_true is not None
    return float(metric_fn(y_true, treatment) - metric_fn(y_true, control))


def _sample_paired_indices(
    sample_size: int,
    rng: np.random.Generator,
    *,
    y_true: pd.Series | None = None,
) -> np.ndarray:
    if y_true is None:
        return rng.integers(0, sample_size, size=sample_size)

    unique_counts = y_true.value_counts(sort=False)
    if 1 < len(unique_counts) < sample_size:
        return np.concatenate(
            [
                rng.choice(
                    np.flatnonzero(y_true.to_numpy() == label),
                    size=int(count),
                    replace=True,
                )
                for label, count in unique_counts.items()
            ]
        )
    return rng.integers(0, sample_size, size=sample_size)


# @id CODE-AIDS-104
# @implements REQ-AIDS-081
# @design DES-AIDS-068 DES-AIDS-069
def _run_paired_bootstrap(
    control: pd.Series,
    treatment: pd.Series,
    *,
    language: str,
    y_true: pd.Series | None = None,
    metric_fn: MetricFn | None = None,
    iterations: int = 1000,
    confidence_level: float = 0.95,
    random_state: int | None = None,
) -> ExperimentResult:
    control_series, treatment_series, truth_series = _validate_paired_inputs(
        control,
        treatment,
        y_true=y_true,
        metric_fn=metric_fn,
        iterations=iterations,
        confidence_level=confidence_level,
    )

    observed_difference = _compute_difference(
        control_series,
        treatment_series,
        y_true=truth_series,
        metric_fn=metric_fn,
    )

    rng = np.random.default_rng(random_state)
    sample_size = len(control_series)
    bootstrap_differences = np.empty(int(iterations), dtype=float)

    for index in range(int(iterations)):
        sample_indices = _sample_paired_indices(sample_size, rng, y_true=truth_series)
        control_sample = control_series.iloc[sample_indices].reset_index(drop=True)
        treatment_sample = treatment_series.iloc[sample_indices].reset_index(drop=True)
        truth_sample = (
            None
            if truth_series is None
            else truth_series.iloc[sample_indices].reset_index(drop=True)
        )
        bootstrap_differences[index] = _compute_difference(
            control_sample,
            treatment_sample,
            y_true=truth_sample,
            metric_fn=metric_fn,
        )

    alpha = 1.0 - float(confidence_level)
    confidence_interval = (
        float(np.quantile(bootstrap_differences, alpha / 2.0)),
        float(np.quantile(bootstrap_differences, 1.0 - (alpha / 2.0))),
    )

    return ExperimentResult(
        statistic=observed_difference,
        p_value=math.nan,
        interpretation=_interpret_bootstrap_interval(
            observed_difference,
            confidence_interval,
            float(confidence_level),
            language,
        ),
        confidence_interval=confidence_interval,
    )


# @id CODE-AIDS-105
# @implements REQ-AIDS-079 REQ-AIDS-080 REQ-AIDS-081
# @design DES-AIDS-067 DES-AIDS-068 DES-AIDS-069
def evaluate_experiment(
    control: pd.Series,
    treatment: pd.Series,
    test: str = "ttest",
    language: str = "en",
    *,
    y_true: pd.Series | None = None,
    metric_fn: MetricFn | None = None,
    iterations: int = 1000,
    confidence_level: float = 0.95,
    random_state: int | None = None,
) -> ExperimentResult:
    """Compute the significance of the difference between ``control`` and ``treatment``."""
    if test not in _SUPPORTED_TESTS:
        raise ValueError(f"Unsupported experiment test: {test!r}")

    if test == "ttest":
        return _run_independent_ttest(control, treatment, language=language)
    if test in {"paired_t", "wilcoxon"}:
        return _run_paired_test(control, treatment, test=test, language=language)
    return _run_paired_bootstrap(
        control,
        treatment,
        language=language,
        y_true=y_true,
        metric_fn=metric_fn,
        iterations=iterations,
        confidence_level=confidence_level,
        random_state=random_state,
    )
