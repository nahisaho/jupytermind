"""A/B testing and experiment evaluation.

Implements DES-AIDS-020 (REQ-AIDS-022): computes the statistical
significance of the observed difference between two groups and reports
the result with a bilingual markdown interpretation.

CHANGE-010 (REQ-AIDS-079..081) adds paired_t/wilcoxon/paired_bootstrap
paths (DES-AIDS-067..069, CODE-AIDS-101..105).
CHANGE-016 (REQ-AIDS-090..092) adds repeated multi-seed comparison,
seed-variability adoption thresholds, and three-way holdout selection-bias
evaluation (DES-AIDS-090..092, CODE-AIDS-131..140).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

MetricFn = Callable[[pd.Series, pd.Series], float]
SeedComparisonFn = Callable[[int, int | None], tuple[float, float]]
SelectionBiasFn = Callable[[pd.DataFrame, pd.DataFrame, pd.DataFrame, str, list[str]], dict]

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


# @id CODE-AIDS-131
# @implements REQ-AIDS-090
# @design DES-AIDS-090
@dataclass(frozen=True)
class SeedComparisonResult:
    split_seed: int
    model_seed: int | None
    control_metric: float
    treatment_metric: float
    improvement: float


# @id CODE-AIDS-132
# @implements REQ-AIDS-090
# @design DES-AIDS-090
@dataclass(frozen=True)
class SeedComparisonSummary:
    results: tuple[SeedComparisonResult, ...]
    mean_improvement: float
    seed_variability: float
    sign_counts: dict[str, int]


# @id CODE-AIDS-133
# @implements REQ-AIDS-091
# @design DES-AIDS-091
@dataclass(frozen=True)
class AdoptionDecision:
    candidate_improvement: float
    threshold: float
    classification: str


# @id CODE-AIDS-134
# @implements REQ-AIDS-092
# @design DES-AIDS-092
@dataclass(frozen=True)
class SelectionBiasHoldoutResult:
    train_index: tuple
    selection_index: tuple
    evaluation_index: tuple
    selected_candidate: str
    selection_improvement: float
    evaluation_improvement: float
    optimism: float
    assumption_findings: tuple | None = None


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


# @id CODE-AIDS-135
# @implements REQ-AIDS-090 REQ-AIDS-092
# @design DES-AIDS-090 DES-AIDS-092
def _as_float_pair(values: tuple[float, float]) -> tuple[float, float]:
    if len(values) != 2:
        raise ValueError("Comparison callbacks must return exactly two metric values.")
    control_metric, treatment_metric = values
    control_metric = float(control_metric)
    treatment_metric = float(treatment_metric)
    if not np.isfinite([control_metric, treatment_metric]).all():
        raise ValueError("Comparison callbacks must return only finite metric values.")
    return control_metric, treatment_metric


# @id CODE-AIDS-136
# @implements REQ-AIDS-090
# @design DES-AIDS-090
def summarize_seed_variability(
    compare_fn: SeedComparisonFn,
    *,
    split_seeds: Sequence[int],
    model_seeds: Sequence[int | None] | None = None,
) -> SeedComparisonSummary:
    """Repeat one comparison across seeds and summarize observed variability."""
    effective_split_seeds = list(split_seeds)
    if len(effective_split_seeds) == 0:
        raise ValueError("split_seeds must contain at least one seed.")

    effective_model_seeds = (
        [None] * len(effective_split_seeds) if model_seeds is None else list(model_seeds)
    )
    if len(effective_model_seeds) != len(effective_split_seeds):
        raise ValueError("model_seeds must be omitted or match split_seeds in length.")

    results: list[SeedComparisonResult] = []
    improvements: list[float] = []
    sign_counts = {"positive": 0, "zero": 0, "negative": 0}

    for split_seed, model_seed in zip(effective_split_seeds, effective_model_seeds, strict=True):
        control_metric, treatment_metric = _as_float_pair(compare_fn(split_seed, model_seed))
        improvement = float(treatment_metric - control_metric)
        results.append(
            SeedComparisonResult(
                split_seed=int(split_seed),
                model_seed=None if model_seed is None else int(model_seed),
                control_metric=control_metric,
                treatment_metric=treatment_metric,
                improvement=improvement,
            )
        )
        improvements.append(improvement)
        if improvement > 0:
            sign_counts["positive"] += 1
        elif improvement < 0:
            sign_counts["negative"] += 1
        else:
            sign_counts["zero"] += 1

    return SeedComparisonSummary(
        results=tuple(results),
        mean_improvement=float(np.mean(improvements)),
        seed_variability=float(max(improvements) - min(improvements)),
        sign_counts=sign_counts,
    )


# @id CODE-AIDS-137
# @implements REQ-AIDS-091
# @design DES-AIDS-091
def judge_improvement(
    summary: SeedComparisonSummary,
    *,
    candidate_improvement: float | None = None,
    threshold: float | None = None,
) -> AdoptionDecision:
    """Classify an improvement against the observed seed-variability threshold."""
    effective_improvement = (
        summary.mean_improvement if candidate_improvement is None else float(candidate_improvement)
    )
    effective_threshold = summary.seed_variability if threshold is None else float(threshold)
    if not np.isfinite(effective_improvement):
        raise ValueError("judge_improvement requires a finite candidate_improvement.")
    if not np.isfinite(effective_threshold):
        raise ValueError("judge_improvement requires a finite threshold.")
    if effective_improvement < 0:
        classification = "regression"
    elif effective_improvement <= effective_threshold:
        classification = "within_seed_variability"
    else:
        classification = "adopt"
    return AdoptionDecision(
        candidate_improvement=effective_improvement,
        threshold=effective_threshold,
        classification=classification,
    )


# @id CODE-AIDS-138
# @implements REQ-AIDS-092
# @design DES-AIDS-092
def _split_holdout_partitions(
    df: pd.DataFrame,
    *,
    split_seed: int,
    train_fraction: float,
    selection_fraction: float,
    evaluation_fraction: float,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    fractions = np.array(
        [float(train_fraction), float(selection_fraction), float(evaluation_fraction)], dtype=float
    )
    if np.any(fractions <= 0.0):
        raise ValueError("train/selection/evaluation fractions must be positive.")
    if not np.isclose(float(fractions.sum()), 1.0):
        raise ValueError("train/selection/evaluation fractions must sum to 1.")

    total_rows = len(df)
    if total_rows < 3:
        raise ValueError("Selection-bias holdout evaluation requires at least 3 rows.")

    raw_counts = fractions * total_rows
    counts = np.floor(raw_counts).astype(int)
    remainder = total_rows - int(counts.sum())
    if remainder > 0:
        residual_order = np.argsort(-(raw_counts - counts))
        for position in residual_order[:remainder]:
            counts[position] += 1
    while np.any(counts == 0):
        zero_positions = np.flatnonzero(counts == 0)
        donor_candidates = np.flatnonzero(counts > 1)
        if len(donor_candidates) == 0:
            raise ValueError(
                "train/selection/evaluation fractions must yield non-empty partitions."
            )
        donor_position = int(donor_candidates[np.argmax(counts[donor_candidates])])
        counts[donor_position] -= 1
        counts[int(zero_positions[0])] += 1

    rng = np.random.default_rng(split_seed)
    shuffled_positions = rng.permutation(total_rows)
    train_end = int(counts[0])
    selection_end = int(counts[0] + counts[1])
    train_positions = shuffled_positions[:train_end]
    selection_positions = shuffled_positions[train_end:selection_end]
    evaluation_positions = shuffled_positions[selection_end:]

    return (
        df.iloc[train_positions].copy(),
        df.iloc[selection_positions].copy(),
        df.iloc[evaluation_positions].copy(),
    )


# @id CODE-AIDS-139
# @implements REQ-AIDS-092
# @design DES-AIDS-092
def _extract_selection_bias_metrics(
    evaluation_payload: dict,
    *,
    baseline: str,
) -> tuple[dict[str, float], dict[str, float]]:
    try:
        selection_metrics = evaluation_payload["selection_metrics"]
        evaluation_metrics = evaluation_payload["evaluation_metrics"]
    except KeyError as exc:
        raise ValueError(
            "evaluate_candidate_fn must return selection_metrics and evaluation_metrics."
        ) from exc
    normalized_selection = {str(name): float(value) for name, value in selection_metrics.items()}
    normalized_evaluation = {str(name): float(value) for name, value in evaluation_metrics.items()}
    for metric_name, metric_map in (
        ("selection_metrics", normalized_selection),
        ("evaluation_metrics", normalized_evaluation),
    ):
        if baseline not in metric_map:
            raise ValueError(f"evaluate_candidate_fn must include baseline in {metric_name}.")
        if not np.isfinite(list(metric_map.values())).all():
            raise ValueError(
                f"evaluate_candidate_fn must return only finite values in {metric_name}."
            )
    return normalized_selection, normalized_evaluation


def _choose_selection_winner(
    selection_metrics: dict[str, float],
    *,
    baseline: str,
    candidates: list[str],
) -> str:
    missing_candidates = [
        candidate for candidate in candidates if candidate not in selection_metrics
    ]
    if missing_candidates:
        raise ValueError(
            "evaluate_candidate_fn must include every candidate in selection_metrics: "
            + ", ".join(missing_candidates)
        )
    return max(
        candidates,
        key=lambda candidate: (selection_metrics[candidate], -candidates.index(candidate)),
    )


# @id CODE-AIDS-140
# @implements REQ-AIDS-092
# @design DES-AIDS-092
def evaluate_selection_bias_holdout(
    df: pd.DataFrame,
    target: str,
    *,
    baseline: str,
    candidates: list[str],
    evaluate_candidate_fn: SelectionBiasFn,
    split_seed: int = 42,
    train_fraction: float = 0.6,
    selection_fraction: float = 0.2,
    evaluation_fraction: float = 0.2,
    assumption_manifest: object | None = None,
) -> SelectionBiasHoldoutResult:
    """Evaluate selection optimism using disjoint train/selection/evaluation subsets."""
    if target not in df.columns:
        raise ValueError(f"target column {target!r} is not present in the dataframe.")
    train_df, selection_df, evaluation_df = _split_holdout_partitions(
        df,
        split_seed=split_seed,
        train_fraction=train_fraction,
        selection_fraction=selection_fraction,
        evaluation_fraction=evaluation_fraction,
    )

    evaluation_payload = evaluate_candidate_fn(
        train_df,
        selection_df,
        evaluation_df,
        baseline,
        candidates,
    )
    selection_metrics, evaluation_metrics = _extract_selection_bias_metrics(
        evaluation_payload,
        baseline=baseline,
    )
    selected_candidate = _choose_selection_winner(
        selection_metrics,
        baseline=baseline,
        candidates=candidates,
    )
    missing_evaluation_candidates = [
        candidate for candidate in candidates if candidate not in evaluation_metrics
    ]
    if missing_evaluation_candidates:
        raise ValueError(
            "evaluate_candidate_fn must include every candidate in evaluation_metrics: "
            + ", ".join(missing_evaluation_candidates)
        )
    selection_improvement = float(selection_metrics[selected_candidate]) - float(
        selection_metrics[baseline]
    )
    evaluation_improvement = float(evaluation_metrics[selected_candidate]) - float(
        evaluation_metrics[baseline]
    )

    assumption_findings = None
    if assumption_manifest is not None:
        from ai_data_scientist.analysis_assumptions import check_manifest

        assumption_findings = check_manifest(assumption_manifest)

    return SelectionBiasHoldoutResult(
        train_index=tuple(train_df.index),
        selection_index=tuple(selection_df.index),
        evaluation_index=tuple(evaluation_df.index),
        selected_candidate=selected_candidate,
        selection_improvement=selection_improvement,
        evaluation_improvement=evaluation_improvement,
        optimism=float(selection_improvement - evaluation_improvement),
        assumption_findings=assumption_findings,
    )


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
