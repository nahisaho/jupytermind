"""Tests for automated model selection / AutoML (REQ-AIDS-020, REQ-AIDS-077, REQ-AIDS-078)."""

import pandas as pd
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression

from ai_data_scientist.automl import run_automl
from ai_data_scientist.ml_modeling import train_model


def _make_classification_df() -> pd.DataFrame:
    features, labels = make_classification(
        n_samples=72,
        n_features=4,
        n_informative=3,
        n_redundant=0,
        n_clusters_per_class=1,
        weights=[0.7, 0.3],
        class_sep=1.4,
        random_state=2,
    )
    df = pd.DataFrame(features, columns=["x1", "x2", "x3", "x4"])
    df["label"] = labels
    return df


# @id TEST-AIDS-020
# @verifies REQ-AIDS-020
def test_TEST_AIDS_020():
    df = pd.DataFrame(
        {
            "x1": list(range(60)),
            "x2": [i % 7 for i in range(60)],
            "label": [1 if (i % 3 == 0) else 0 for i in range(60)],
        }
    )

    result = run_automl(df, target="label", model_type="classification")

    assert len(result.ranked_candidates) >= 3
    metrics = [c["metric"] for c in result.ranked_candidates]
    assert metrics == sorted(metrics, reverse=True)
    for candidate in result.ranked_candidates:
        assert "model_name" in candidate
        assert "metric" in candidate


# @id TEST-AIDS-191
# @verifies REQ-AIDS-077
def test_TEST_AIDS_191():
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

    result = run_automl(
        df,
        target="label",
        model_type="classification",
        scoring="roc_auc",
        cv_splits=shared_splits,
    )

    metrics = [candidate["metric"] for candidate in result.ranked_candidates]
    assert metrics == sorted(metrics, reverse=True)
    assert result.cv_splits == shared_splits
    for candidate in result.ranked_candidates:
        assert candidate["fold_scores"]
        assert candidate["result"].cv_splits == shared_splits


# @id TEST-AIDS-192
# @verifies REQ-AIDS-077
def test_TEST_AIDS_192():
    df = _make_classification_df()

    result = run_automl(
        df,
        target="label",
        model_type="classification",
        cv_strategy="StratifiedKFold",
        n_splits=4,
        scoring="log_loss",
    )

    metrics = [candidate["metric"] for candidate in result.ranked_candidates]
    assert metrics == sorted(metrics)


# @id TEST-AIDS-193
# @verifies REQ-AIDS-078
def test_TEST_AIDS_193():
    df = _make_classification_df()

    result = run_automl(
        df,
        target="label",
        model_type="classification",
        scoring="roc_auc",
        cv_strategy="StratifiedKFold",
        n_splits=4,
        candidate_estimators={"custom_logreg": LogisticRegression(max_iter=1000)},
    )

    model_names = [candidate["model_name"] for candidate in result.ranked_candidates]
    assert "custom_logreg" in model_names
