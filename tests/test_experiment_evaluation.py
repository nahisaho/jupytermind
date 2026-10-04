"""Tests for A/B testing and experiment evaluation (REQ-AIDS-022)."""

from collections.abc import Callable

import numpy as np
import pandas as pd
import pytest
from scipy import stats as scipy_stats
from sklearn.metrics import roc_auc_score

from ai_data_scientist.experiment_evaluation import evaluate_experiment


# @id TEST-AIDS-022
# @verifies REQ-AIDS-022
def test_TEST_AIDS_022():
    control = pd.Series([10.1, 9.8, 10.3, 9.9, 10.0, 9.7, 10.2, 9.95, 10.05, 9.85])
    treatment = pd.Series([12.1, 11.8, 12.3, 11.9, 12.0, 11.7, 12.2, 11.95, 12.05, 11.85])

    result = evaluate_experiment(control, treatment, test="ttest")

    reference_stat, reference_p = scipy_stats.ttest_ind(control, treatment)

    assert abs(result.statistic - reference_stat) < 1e-6
    assert abs(result.p_value - reference_p) < 1e-6
    assert isinstance(result.interpretation, str) and len(result.interpretation) > 0

    ja_result = evaluate_experiment(control, treatment, test="ttest", language="ja")
    assert isinstance(ja_result.interpretation, str) and len(ja_result.interpretation) > 0


def _paired_bootstrap_reference(
    control: pd.Series,
    treatment: pd.Series,
    *,
    y_true: pd.Series | None = None,
    metric_fn: Callable[[pd.Series, pd.Series], float] | None = None,
    iterations: int = 1000,
    confidence_level: float = 0.95,
    random_state: int | None = None,
) -> tuple[float, tuple[float, float]]:
    rng = np.random.default_rng(random_state)
    control_values = control.reset_index(drop=True)
    treatment_values = treatment.reset_index(drop=True)
    y_true_values = None if y_true is None else y_true.reset_index(drop=True)

    def sample_indices() -> np.ndarray:
        if y_true_values is None:
            return rng.integers(0, len(control_values), size=len(control_values))

        unique_counts = y_true_values.value_counts(sort=False)
        if 1 < len(unique_counts) < len(control_values):
            return np.concatenate(
                [
                    rng.choice(
                        np.flatnonzero(y_true_values.to_numpy() == label),
                        size=int(count),
                        replace=True,
                    )
                    for label, count in unique_counts.items()
                ]
            )
        return rng.integers(0, len(control_values), size=len(control_values))

    def compute_difference(indices: np.ndarray | None = None) -> float:
        if indices is None:
            control_sample = control_values
            treatment_sample = treatment_values
            y_true_sample = y_true_values
        else:
            control_sample = control_values.iloc[indices].reset_index(drop=True)
            treatment_sample = treatment_values.iloc[indices].reset_index(drop=True)
            y_true_sample = (
                None
                if y_true_values is None
                else y_true_values.iloc[indices].reset_index(drop=True)
            )
        if metric_fn is None:
            return float((treatment_sample - control_sample).mean())
        assert y_true_sample is not None
        return float(
            metric_fn(y_true_sample, treatment_sample) - metric_fn(y_true_sample, control_sample)
        )

    observed_difference = compute_difference()
    bootstrap_differences = np.array(
        [compute_difference(sample_indices()) for _ in range(iterations)],
        dtype=float,
    )
    alpha = 1.0 - confidence_level
    confidence_interval = (
        float(np.quantile(bootstrap_differences, alpha / 2.0)),
        float(np.quantile(bootstrap_differences, 1.0 - (alpha / 2.0))),
    )
    return observed_difference, confidence_interval


# @id TEST-AIDS-161
# @verifies REQ-AIDS-079
def test_TEST_AIDS_161_paired_t_matches_scipy_reference():
    control = pd.Series([0.71, 0.63, 0.68, 0.74, 0.69, 0.66, 0.72, 0.64])
    treatment = pd.Series([0.76, 0.68, 0.72, 0.75, 0.73, 0.70, 0.74, 0.69])

    result = evaluate_experiment(control, treatment, test="paired_t")

    reference_statistic, reference_p_value = scipy_stats.ttest_rel(control, treatment)
    independent_statistic, independent_p_value = scipy_stats.ttest_ind(control, treatment)

    assert abs(result.statistic - reference_statistic) < 1e-6
    assert abs(result.p_value - reference_p_value) < 1e-6
    assert independent_p_value != pytest.approx(result.p_value)
    assert independent_statistic != pytest.approx(result.statistic)


# @id TEST-AIDS-162
# @verifies REQ-AIDS-080
def test_TEST_AIDS_162_wilcoxon_matches_scipy_reference():
    control = pd.Series([0.81, 0.76, 0.79, 0.83, 0.75, 0.78, 0.82, 0.77])
    treatment = pd.Series([0.84, 0.79, 0.80, 0.85, 0.78, 0.80, 0.85, 0.79])

    result = evaluate_experiment(control, treatment, test="wilcoxon", language="ja")

    reference_statistic, reference_p_value = scipy_stats.wilcoxon(control, treatment)

    assert abs(result.statistic - reference_statistic) < 1e-6
    assert abs(result.p_value - reference_p_value) < 1e-6
    assert "p値" in result.interpretation


# @id TEST-AIDS-163
# @verifies REQ-AIDS-080
def test_TEST_AIDS_163_paired_tests_require_equal_length_inputs():
    control = pd.Series([0.8, 0.82, 0.81])
    treatment = pd.Series([0.83, 0.84])

    with pytest.raises(ValueError, match="equal-length inputs"):
        evaluate_experiment(control, treatment, test="wilcoxon")


# @id TEST-AIDS-164
# @verifies REQ-AIDS-081
def test_TEST_AIDS_164_paired_bootstrap_supports_prediction_metric_comparison():
    y_true = pd.Series([0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
    control = pd.Series([0.12, 0.58, 0.31, 0.69, 0.37, 0.63, 0.46, 0.67, 0.22, 0.72, 0.41, 0.65])
    treatment = pd.Series([0.08, 0.66, 0.25, 0.76, 0.29, 0.71, 0.39, 0.78, 0.17, 0.81, 0.34, 0.74])

    result = evaluate_experiment(
        control,
        treatment,
        test="paired_bootstrap",
        y_true=y_true,
        metric_fn=roc_auc_score,
        iterations=400,
        confidence_level=0.95,
        random_state=11,
    )

    reference_statistic, reference_interval = _paired_bootstrap_reference(
        control,
        treatment,
        y_true=y_true,
        metric_fn=roc_auc_score,
        iterations=400,
        confidence_level=0.95,
        random_state=11,
    )

    assert result.statistic == pytest.approx(reference_statistic, abs=1e-6)
    assert np.isnan(result.p_value)
    assert result.confidence_interval is not None
    assert result.confidence_interval[0] == pytest.approx(reference_interval[0], abs=1e-6)
    assert result.confidence_interval[1] == pytest.approx(reference_interval[1], abs=1e-6)
    assert "does not provide a hypothesis-test p-value" in result.interpretation


# @id TEST-AIDS-165
# @verifies REQ-AIDS-081
def test_TEST_AIDS_165_paired_bootstrap_supports_fold_score_comparison():
    control = pd.Series([0.812, 0.804, 0.798, 0.821, 0.809])
    treatment = pd.Series([0.818, 0.809, 0.803, 0.832, 0.814])

    result = evaluate_experiment(
        control,
        treatment,
        test="paired_bootstrap",
        iterations=500,
        confidence_level=0.9,
        random_state=23,
    )

    reference_statistic, reference_interval = _paired_bootstrap_reference(
        control,
        treatment,
        iterations=500,
        confidence_level=0.9,
        random_state=23,
    )

    assert result.statistic == pytest.approx(reference_statistic, abs=1e-6)
    assert np.isnan(result.p_value)
    assert result.confidence_interval == pytest.approx(reference_interval, abs=1e-6)


# @id TEST-AIDS-166
# @verifies REQ-AIDS-081
def test_TEST_AIDS_166_paired_bootstrap_requires_metric_fn_and_y_true_together():
    control = pd.Series([0.1, 0.4, 0.3, 0.7])
    treatment = pd.Series([0.2, 0.5, 0.35, 0.8])
    y_true = pd.Series([0, 1, 0, 1])

    with pytest.raises(ValueError, match="metric_fn and y_true"):
        evaluate_experiment(control, treatment, test="paired_bootstrap", y_true=y_true)

    with pytest.raises(ValueError, match="metric_fn and y_true"):
        evaluate_experiment(
            control,
            treatment,
            test="paired_bootstrap",
            metric_fn=roc_auc_score,
        )


# @id TEST-AIDS-167
# @verifies REQ-AIDS-079 REQ-AIDS-080 REQ-AIDS-081
@pytest.mark.parametrize(
    ("test_name", "kwargs"),
    [
        ("paired_t", {}),
        ("wilcoxon", {}),
        ("paired_bootstrap", {"iterations": 50, "confidence_level": 0.9}),
    ],
)
def test_TEST_AIDS_167_paired_paths_reject_non_finite_values(
    test_name: str,
    kwargs: dict[str, object],
):
    control = pd.Series([0.8, np.nan, 0.81], index=["a", "b", "c"])
    treatment = pd.Series([0.82, 0.83, 0.84], index=["a", "b", "c"])

    with pytest.raises(ValueError, match="finite paired values"):
        evaluate_experiment(control, treatment, test=test_name, **kwargs)


# @id TEST-AIDS-168
# @verifies REQ-AIDS-079 REQ-AIDS-080 REQ-AIDS-081
@pytest.mark.parametrize(
    ("test_name", "kwargs"),
    [
        ("paired_t", {}),
        ("wilcoxon", {}),
        (
            "paired_bootstrap",
            {
                "iterations": 50,
                "confidence_level": 0.9,
                "y_true": pd.Series([0, 1, 0], index=["x", "y", "z"]),
                "metric_fn": roc_auc_score,
            },
        ),
    ],
)
def test_TEST_AIDS_168_paired_paths_require_identical_indexes(
    test_name: str,
    kwargs: dict[str, object],
):
    control = pd.Series([0.8, 0.81, 0.82], index=["a", "b", "c"])
    treatment = pd.Series([0.83, 0.84, 0.85], index=["a", "x", "c"])

    with pytest.raises(ValueError, match="identical indexes|paired input index"):
        evaluate_experiment(control, treatment, test=test_name, **kwargs)
