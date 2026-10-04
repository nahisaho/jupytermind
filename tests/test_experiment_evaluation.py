"""Tests for A/B testing and experiment evaluation (REQ-AIDS-022).

CHANGE-010 (REQ-AIDS-079..081) adds TEST-AIDS-161..168 for paired
significance tests (paired_t, wilcoxon, paired_bootstrap).
"""

from collections.abc import Callable

import numpy as np
import pandas as pd
import pytest
from scipy import stats as scipy_stats
from sklearn.metrics import roc_auc_score

from ai_data_scientist import experiment_evaluation
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


# @id TEST-AIDS-220
# @verifies REQ-AIDS-090
def test_TEST_AIDS_220_summarize_seed_variability_reports_mean_range_and_sign_counts():
    expected_pairs = {
        42: (0.812100, 0.812250),
        7: (0.812040, 0.812126),
        2026: (0.812080, 0.812166),
    }

    def compare_fn(split_seed: int, model_seed: int | None):
        assert model_seed is None
        return expected_pairs[split_seed]

    summary = experiment_evaluation.summarize_seed_variability(
        compare_fn,
        split_seeds=[42, 7, 2026],
    )

    assert [result.split_seed for result in summary.results] == [42, 7, 2026]
    assert [result.improvement for result in summary.results] == pytest.approx(
        [0.000150, 0.000086, 0.000086], abs=1e-9
    )
    assert summary.mean_improvement == pytest.approx(0.00010733333333333333, abs=1e-12)
    assert summary.seed_variability == pytest.approx(0.000064, abs=1e-12)
    assert summary.sign_counts == {"positive": 3, "zero": 0, "negative": 0}


# @id TEST-AIDS-223
# @verifies REQ-AIDS-090
def test_TEST_AIDS_223_summarize_seed_variability_preserves_optional_model_seeds():
    summary = experiment_evaluation.summarize_seed_variability(
        lambda split_seed, model_seed: {
            (101, 11): (0.8100, 0.8200),
            (102, 12): (0.8100, 0.8100),
            (103, 13): (0.8100, 0.8000),
        }[(split_seed, model_seed)],
        split_seeds=[101, 102, 103],
        model_seeds=[11, 12, 13],
    )

    assert [result.split_seed for result in summary.results] == [101, 102, 103]
    assert [result.model_seed for result in summary.results] == [11, 12, 13]
    assert [result.improvement for result in summary.results] == pytest.approx(
        [0.0100, 0.0000, -0.0100], abs=1e-12
    )
    assert summary.mean_improvement == pytest.approx(0.0, abs=1e-12)
    assert summary.seed_variability == pytest.approx(0.02, abs=1e-12)
    assert summary.sign_counts == {"positive": 1, "zero": 1, "negative": 1}


# @id TEST-AIDS-221
# @verifies REQ-AIDS-091
def test_TEST_AIDS_221_judge_improvement_uses_seed_variability_threshold():
    summary = experiment_evaluation.summarize_seed_variability(
        lambda split_seed, model_seed: {
            42: (0.812100, 0.812250),
            7: (0.812040, 0.812126),
            2026: (0.812080, 0.812166),
        }[split_seed],
        split_seeds=[42, 7, 2026],
    )

    threshold_decision = experiment_evaluation.judge_improvement(
        summary, candidate_improvement=0.000021
    )
    near_threshold = experiment_evaluation.judge_improvement(
        summary, candidate_improvement=0.000063
    )
    adopted = experiment_evaluation.judge_improvement(summary, candidate_improvement=0.000080)
    regression = experiment_evaluation.judge_improvement(summary, candidate_improvement=-0.000005)

    assert threshold_decision.threshold == pytest.approx(0.000064, abs=1e-12)
    assert threshold_decision.classification == "within_seed_variability"
    assert near_threshold.classification == "within_seed_variability"
    assert adopted.classification == "adopt"
    assert regression.classification == "regression"


# @id TEST-AIDS-222
# @verifies REQ-AIDS-092
def test_TEST_AIDS_222_selection_bias_holdout_reports_selection_and_evaluation_gains():
    df = pd.DataFrame(
        {
            "feature": np.linspace(0.0, 0.9, 10),
            "target": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        },
        index=[f"row_{idx}" for idx in range(10)],
    )
    callback_calls: list[tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]] = []

    def evaluate_candidate_fn(
        train_df: pd.DataFrame,
        selection_df: pd.DataFrame,
        evaluation_df: pd.DataFrame,
        baseline: str,
        candidates: list[str],
    ) -> dict[str, object]:
        callback_calls.append(
            (
                tuple(train_df.index),
                tuple(selection_df.index),
                tuple(evaluation_df.index),
            )
        )
        assert baseline == "baseline"
        assert candidates == ["candidate_a", "candidate_b"]
        return {
            "selected_candidate": "candidate_a",
            "selection_metrics": {
                "baseline": 0.800000,
                "candidate_a": 0.800224,
                "candidate_b": 0.800180,
            },
            "evaluation_metrics": {
                "baseline": 0.799000,
                "candidate_a": 0.799135,
                "candidate_b": 0.799100,
            },
        }

    result = experiment_evaluation.evaluate_selection_bias_holdout(
        df,
        "target",
        baseline="baseline",
        candidates=["candidate_a", "candidate_b"],
        evaluate_candidate_fn=evaluate_candidate_fn,
        split_seed=42,
        train_fraction=0.6,
        selection_fraction=0.2,
        evaluation_fraction=0.2,
    )

    assert len(callback_calls) == 1
    train_index, selection_index, evaluation_index = callback_calls[0]
    assert len(train_index) == 6
    assert len(selection_index) == 2
    assert len(evaluation_index) == 2
    assert set(train_index).isdisjoint(selection_index)
    assert set(train_index).isdisjoint(evaluation_index)
    assert set(selection_index).isdisjoint(evaluation_index)
    assert set(train_index) | set(selection_index) | set(evaluation_index) == set(df.index)

    assert result.selected_candidate == "candidate_a"
    assert result.selection_improvement == pytest.approx(0.000224, abs=1e-12)
    assert result.evaluation_improvement == pytest.approx(0.000135, abs=1e-12)
    assert result.optimism == pytest.approx(0.000089, abs=1e-12)


# @id TEST-AIDS-224
# @verifies REQ-AIDS-092
def test_TEST_AIDS_224_selection_bias_holdout_uses_selection_winner_not_evaluation_preference():
    df = pd.DataFrame(
        {
            "feature": np.linspace(0.0, 0.9, 10),
            "target": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        },
        index=[f"row_{idx}" for idx in range(10)],
    )

    result = experiment_evaluation.evaluate_selection_bias_holdout(
        df,
        "target",
        baseline="baseline",
        candidates=["candidate_a", "candidate_b"],
        evaluate_candidate_fn=lambda train_df, selection_df, evaluation_df, baseline, candidates: {
            "selected_candidate": "candidate_b",
            "selection_metrics": {
                "baseline": 0.800000,
                "candidate_a": 0.800224,
                "candidate_b": 0.800180,
            },
            "evaluation_metrics": {
                "baseline": 0.799000,
                "candidate_a": 0.799135,
                "candidate_b": 0.799210,
            },
        },
        split_seed=42,
        train_fraction=0.6,
        selection_fraction=0.2,
        evaluation_fraction=0.2,
    )

    assert result.selected_candidate == "candidate_a"
    assert result.selection_improvement == pytest.approx(0.000224, abs=1e-12)
    assert result.evaluation_improvement == pytest.approx(0.000135, abs=1e-12)
    assert result.optimism == pytest.approx(0.000089, abs=1e-12)


# @id TEST-AIDS-225
# @verifies REQ-AIDS-092
def test_TEST_AIDS_225_selection_bias_holdout_breaks_selection_ties_by_candidate_order():
    df = pd.DataFrame(
        {
            "feature": np.linspace(0.0, 0.9, 10),
            "target": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        },
        index=[f"row_{idx}" for idx in range(10)],
    )

    result = experiment_evaluation.evaluate_selection_bias_holdout(
        df,
        "target",
        baseline="baseline",
        candidates=["candidate_c", "candidate_a", "candidate_b"],
        evaluate_candidate_fn=lambda train_df, selection_df, evaluation_df, baseline, candidates: {
            "selected_candidate": "candidate_b",
            "selection_metrics": {
                "baseline": 0.800000,
                "candidate_c": 0.800210,
                "candidate_a": 0.800210,
                "candidate_b": 0.800210,
            },
            "evaluation_metrics": {
                "baseline": 0.799000,
                "candidate_c": 0.799120,
                "candidate_a": 0.799150,
                "candidate_b": 0.799190,
            },
        },
    )

    assert result.selected_candidate == "candidate_c"
    assert result.selection_improvement == pytest.approx(0.000210, abs=1e-12)
    assert result.evaluation_improvement == pytest.approx(0.000120, abs=1e-12)
    assert result.optimism == pytest.approx(0.000090, abs=1e-12)


# @id TEST-AIDS-226
# @verifies REQ-AIDS-092
@pytest.mark.parametrize(
    ("row_count", "fractions", "expected_lengths"),
    [
        (3, (0.8, 0.1, 0.1), (1, 1, 1)),
        (11, (0.6, 0.2, 0.2), (7, 2, 2)),
    ],
)
def test_TEST_AIDS_226_selection_bias_holdout_keeps_all_partitions_non_empty(
    row_count: int,
    fractions: tuple[float, float, float],
    expected_lengths: tuple[int, int, int],
):
    df = pd.DataFrame(
        {
            "feature": np.linspace(0.0, float(row_count - 1), row_count),
            "target": [idx % 2 for idx in range(row_count)],
        },
        index=[f"row_{idx}" for idx in range(row_count)],
    )
    observed_partition_lengths: list[tuple[int, int, int]] = []

    def evaluate_candidate_fn(
        train_df: pd.DataFrame,
        selection_df: pd.DataFrame,
        evaluation_df: pd.DataFrame,
        baseline: str,
        candidates: list[str],
    ) -> dict[str, object]:
        observed_partition_lengths.append(
            (len(train_df.index), len(selection_df.index), len(evaluation_df.index))
        )
        return {
            "selection_metrics": {
                "baseline": 0.8,
                "candidate_a": 0.81,
            },
            "evaluation_metrics": {
                "baseline": 0.79,
                "candidate_a": 0.80,
            },
        }

    result = experiment_evaluation.evaluate_selection_bias_holdout(
        df,
        "target",
        baseline="baseline",
        candidates=["candidate_a"],
        evaluate_candidate_fn=evaluate_candidate_fn,
        train_fraction=fractions[0],
        selection_fraction=fractions[1],
        evaluation_fraction=fractions[2],
    )

    assert observed_partition_lengths == [expected_lengths]
    assert all(length > 0 for length in observed_partition_lengths[0])
    assert (
        len(result.train_index),
        len(result.selection_index),
        len(result.evaluation_index),
    ) == expected_lengths


# @id TEST-AIDS-227
# @verifies REQ-AIDS-090
@pytest.mark.parametrize(
    "metric_pair",
    [
        (float("nan"), 0.81),
        (0.80, float("inf")),
    ],
)
def test_TEST_AIDS_227_summarize_seed_variability_rejects_non_finite_metrics(
    metric_pair: tuple[float, float],
):
    with pytest.raises(ValueError, match="finite metric values"):
        experiment_evaluation.summarize_seed_variability(
            lambda split_seed, model_seed: metric_pair,
            split_seeds=[42],
        )


# @id TEST-AIDS-228
# @verifies REQ-AIDS-091
def test_TEST_AIDS_228_judge_improvement_handles_boundary_and_one_seed_cases():
    summary = experiment_evaluation.summarize_seed_variability(
        lambda split_seed, model_seed: {
            42: (0.812100, 0.812250),
            7: (0.812040, 0.812126),
            2026: (0.812080, 0.812166),
        }[split_seed],
        split_seeds=[42, 7, 2026],
    )
    one_seed_summary = experiment_evaluation.summarize_seed_variability(
        lambda split_seed, model_seed: (0.812100, 0.812131),
        split_seeds=[99],
    )

    assert (
        experiment_evaluation.judge_improvement(summary, candidate_improvement=0.0).classification
        == "within_seed_variability"
    )
    assert (
        experiment_evaluation.judge_improvement(
            summary, candidate_improvement=summary.seed_variability
        ).classification
        == "within_seed_variability"
    )
    assert (
        experiment_evaluation.judge_improvement(
            summary,
            candidate_improvement=0.000001,
            threshold=0.0,
        ).classification
        == "adopt"
    )
    assert one_seed_summary.seed_variability == pytest.approx(0.0, abs=1e-12)
    assert experiment_evaluation.judge_improvement(one_seed_summary).classification == "adopt"


# @id TEST-AIDS-229
# @verifies REQ-AIDS-090
def test_TEST_AIDS_229_summarize_seed_variability_accepts_array_like_split_seeds():
    summary = experiment_evaluation.summarize_seed_variability(
        lambda split_seed, model_seed: {
            101: (0.8000, 0.8100),
            102: (0.8000, 0.8120),
        }[split_seed],
        split_seeds=np.array([101, 102]),
    )

    assert [result.split_seed for result in summary.results] == [101, 102]
    assert summary.mean_improvement == pytest.approx(0.011, abs=1e-12)
    assert summary.seed_variability == pytest.approx(0.002, abs=1e-12)


# @id TEST-AIDS-230
# @verifies REQ-AIDS-091
@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"candidate_improvement": float("nan")}, "finite candidate_improvement"),
        ({"candidate_improvement": float("inf")}, "finite candidate_improvement"),
        ({"threshold": float("nan")}, "finite threshold"),
        ({"threshold": float("-inf")}, "finite threshold"),
    ],
)
def test_TEST_AIDS_230_judge_improvement_rejects_non_finite_inputs(
    kwargs: dict[str, float],
    message: str,
):
    summary = experiment_evaluation.summarize_seed_variability(
        lambda split_seed, model_seed: (0.812100, 0.812131),
        split_seeds=[99],
    )

    with pytest.raises(ValueError, match=message):
        experiment_evaluation.judge_improvement(summary, **kwargs)
