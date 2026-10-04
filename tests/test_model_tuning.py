"""Tests for model tuning and comparison (REQ-AIDS-019, REQ-AIDS-076, REQ-AIDS-078)."""

import pandas as pd
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression

from ai_data_scientist.ml_modeling import train_model
from ai_data_scientist.model_tuning import tune_or_compare


def _make_classification_df() -> pd.DataFrame:
    features, labels = make_classification(
        n_samples=60,
        n_features=4,
        n_informative=3,
        n_redundant=0,
        n_clusters_per_class=1,
        weights=[0.7, 0.3],
        class_sep=1.5,
        random_state=1,
    )
    df = pd.DataFrame(features, columns=["x1", "x2", "x3", "x4"])
    df["label"] = labels
    return df


# @id TEST-AIDS-019
# @verifies REQ-AIDS-019
def test_TEST_AIDS_019():
    df = pd.DataFrame(
        {
            "x1": list(range(60)),
            "x2": [i % 7 for i in range(60)],
            "label": [1 if (i % 3 == 0) else 0 for i in range(60)],
        }
    )
    grid = [
        {"n_estimators": 5, "max_depth": 2},
        {"n_estimators": 20, "max_depth": 4},
        {"n_estimators": 50, "max_depth": None},
    ]

    result = tune_or_compare(df, target="label", grid=grid, model_type="classification")

    candidate_metrics = [c["metric"] for c in result.all_candidates]
    assert result.best_metric == max(candidate_metrics)
    assert result.best_params in grid
    assert len(result.all_candidates) == len(grid)


# @id TEST-AIDS-154
# @verifies REQ-AIDS-076
def test_TEST_AIDS_154():
    df = _make_classification_df()
    shared_splits = train_model(
        df,
        target="label",
        model_type="classification",
        model_name="logistic_regression",
        cv_strategy="StratifiedKFold",
        n_splits=4,
        scoring="roc_auc",
    ).cv_splits
    grid = [
        {"model_name": "logistic_regression", "C": 0.25},
        {"model_name": "logistic_regression", "C": 1.0},
    ]

    result = tune_or_compare(
        df,
        target="label",
        grid=grid,
        model_type="classification",
        scoring="roc_auc",
        cv_splits=shared_splits,
    )

    candidate_metrics = [candidate["metric"] for candidate in result.all_candidates]
    assert result.best_metric == max(candidate_metrics)
    assert result.cv_splits == shared_splits
    for candidate in result.all_candidates:
        assert candidate["fold_scores"]
        assert candidate["result"].cv_splits == shared_splits


# @id TEST-AIDS-155
# @verifies REQ-AIDS-076
def test_TEST_AIDS_155():
    df = _make_classification_df()
    grid = [
        {"model_name": "logistic_regression", "C": 0.25},
        {"model_name": "logistic_regression", "C": 1.0},
    ]

    result = tune_or_compare(
        df,
        target="label",
        grid=grid,
        model_type="classification",
        cv_strategy="StratifiedKFold",
        n_splits=4,
        scoring="log_loss",
    )

    candidate_metrics = [candidate["metric"] for candidate in result.all_candidates]
    assert result.best_metric == min(candidate_metrics)


# @id TEST-AIDS-156
# @verifies REQ-AIDS-078
def test_TEST_AIDS_156():
    df = _make_classification_df()
    grid = [
        {"estimator": LogisticRegression(max_iter=1000), "C": 0.25},
        {"estimator": LogisticRegression(max_iter=1000), "C": 1.0},
    ]

    result = tune_or_compare(
        df,
        target="label",
        grid=grid,
        model_type="classification",
        cv_strategy="StratifiedKFold",
        n_splits=4,
        scoring="roc_auc",
    )

    assert result.best_params in grid
    assert all(isinstance(candidate["result"].model, LogisticRegression) for candidate in result.all_candidates)
