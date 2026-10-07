"""Tests for supervised ML modeling (REQ-AIDS-008, REQ-AIDS-074, REQ-AIDS-075, REQ-AIDS-078)."""

import numpy as np
import pandas as pd
import pytest
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.svm import SVC

from ai_data_scientist.ml_modeling import train_model


def _make_classification_fixture() -> tuple[pd.DataFrame, pd.Series]:
    features, labels = make_classification(
        n_samples=60,
        n_features=4,
        n_informative=3,
        n_redundant=0,
        n_clusters_per_class=1,
        weights=[0.7, 0.3],
        class_sep=1.5,
        random_state=0,
    )
    df = pd.DataFrame(features, columns=["x1", "x2", "x3", "x4"])
    df["label"] = labels
    groups = pd.Series(np.repeat(np.arange(15), 4), index=df.index, name="group")
    return df, groups


# @id TEST-AIDS-008
# @verifies REQ-AIDS-008
def test_TEST_AIDS_008():
    df = pd.DataFrame(
        {
            "x1": list(range(40)),
            "x2": [i % 5 for i in range(40)],
            "label": [1 if i % 2 == 0 else 0 for i in range(40)],
        }
    )

    result = train_model(df, target="label", model_type="classification", test_size=0.25)

    assert set(result.metrics) >= {"accuracy", "precision", "recall"}
    assert not (set(result.train_index) & set(result.test_index))
    assert set(result.train_index) | set(result.test_index) == set(df.index)

    regression_df = pd.DataFrame(
        {"x1": list(range(40)), "y": [float(i) * 2.0 + 1.0 for i in range(40)]}
    )
    reg_result = train_model(regression_df, target="y", model_type="regression", test_size=0.25)
    assert set(reg_result.metrics) >= {"rmse", "r2"}
    assert not (set(reg_result.train_index) & set(reg_result.test_index))


# @id TEST-AIDS-185
# @verifies REQ-AIDS-074 REQ-AIDS-075
def test_TEST_AIDS_185():
    df, _ = _make_classification_fixture()

    result = train_model(
        df,
        target="label",
        model_type="classification",
        model_name="logistic_regression",
        cv_strategy="StratifiedKFold",
        n_splits=4,
        scoring="roc_auc",
    )

    assert result.scoring == "roc_auc"
    assert len(result.fold_scores) == 4
    assert len(result.cv_splits) == 4
    assert result.train_index == result.cv_splits[0][0]
    assert result.test_index == result.cv_splits[0][1]
    assert list(result.oof_predictions.index) == list(df.index)
    assert list(result.oof_probabilities.index) == list(df.index)
    assert list(result.oof_probabilities.columns) == sorted(df["label"].unique().tolist())

    positive_class = result.oof_probabilities.columns[-1]
    assert result.metrics["roc_auc"] == pytest.approx(
        roc_auc_score(df["label"], result.oof_probabilities[positive_class]), abs=1e-9
    )

    covered_test_indices = []
    for train_idx, test_idx in result.cv_splits:
        covered_test_indices.extend(test_idx)
        assert not (set(train_idx) & set(test_idx))
        assert set(df.loc[test_idx, "label"]) == {0, 1}
    assert set(covered_test_indices) == set(df.index)
    assert len(covered_test_indices) == len(df.index)

    reused = train_model(
        df,
        target="label",
        model_type="classification",
        model_name="logistic_regression",
        scoring="roc_auc",
        cv_splits=result.cv_splits,
    )
    assert reused.cv_splits == result.cv_splits


# @id TEST-AIDS-186
# @verifies REQ-AIDS-074 REQ-AIDS-075
def test_TEST_AIDS_186():
    df, groups = _make_classification_fixture()

    result = train_model(
        df,
        target="label",
        model_type="classification",
        model_name="logistic_regression",
        cv_strategy="GroupKFold",
        n_splits=3,
        groups=groups,
        scoring="log_loss",
    )

    assert result.scoring == "log_loss"
    assert len(result.fold_scores) == 3
    assert len(result.cv_splits) == 3
    assert result.metrics["log_loss"] == pytest.approx(
        log_loss(df["label"], result.oof_probabilities, labels=result.oof_probabilities.columns),
        abs=1e-9,
    )

    for train_idx, test_idx in result.cv_splits:
        assert not set(groups.loc[train_idx]) & set(groups.loc[test_idx])


# @id TEST-AIDS-187
# @verifies REQ-AIDS-075 REQ-AIDS-078
def test_TEST_AIDS_187():
    df, _ = _make_classification_fixture()

    probabilistic_result = train_model(
        df,
        target="label",
        model_type="classification",
        estimator=LogisticRegression(max_iter=1000),
        cv_strategy="StratifiedKFold",
        n_splits=4,
        scoring="roc_auc",
    )

    assert isinstance(probabilistic_result.model, LogisticRegression)
    assert "roc_auc" in probabilistic_result.metrics
    assert probabilistic_result.cv_splits is not None

    non_probabilistic_result = train_model(
        df,
        target="label",
        model_type="classification",
        estimator=SVC(),
        cv_strategy="StratifiedKFold",
        n_splits=4,
        scoring="accuracy",
    )
    assert non_probabilistic_result.oof_probabilities is None
    assert non_probabilistic_result.oof_predictions is not None

    with pytest.raises(ValueError, match="predict_proba"):
        train_model(
            df,
            target="label",
            model_type="classification",
            estimator=SVC(),
            cv_strategy="StratifiedKFold",
            n_splits=4,
            scoring="roc_auc",
        )


# @id TEST-AIDS-194
# @verifies REQ-AIDS-074
@pytest.mark.parametrize(
    ("cv_splits", "message"),
    [
        ([([0, 1, 2], [2, 3]), ([3, 4, 5], [0, 1, 4, 5])], "train/test overlap"),
        ([([0, 1, 2], [3, 99]), ([3, 4, 5], [0, 1, 2, 4, 5])], "unknown index labels"),
        ([([0, 1, 2, 5], [3, 4]), ([3], [0, 1, 2, 4, 5])], "duplicate test coverage"),
        ([([0, 1, 2], [3]), ([2, 3], [0, 1, 4, 5])], "missing test coverage"),
    ],
)
def test_TEST_AIDS_194(cv_splits, message):
    df, _ = _make_classification_fixture()
    small_df = df.iloc[:6].copy()

    with pytest.raises(ValueError, match=message):
        train_model(
            small_df,
            target="label",
            model_type="classification",
            model_name="logistic_regression",
            scoring="accuracy",
            cv_splits=cv_splits,
        )

    duplicate_index_df = small_df.copy()
    duplicate_index_df.index = [0] * len(duplicate_index_df)
    with pytest.raises(ValueError, match="unique index labels"):
        train_model(
            duplicate_index_df,
            target="label",
            model_type="classification",
            model_name="logistic_regression",
            cv_strategy="StratifiedKFold",
            n_splits=4,
            scoring="accuracy",
        )


# @id TEST-AIDS-352
# @verifies REQ-AIDS-100
def test_TEST_AIDS_352():
    """Zero usable feature columns in the holdout path raises a clear ValueError."""
    df = pd.DataFrame({"y": [0, 1, 0, 1, 0, 1, 0, 1]})
    target = "y"

    with pytest.raises(ValueError) as excinfo:
        train_model(df, target=target, model_type="classification")

    assert str(excinfo.value) == (
        f"train_model: no usable feature columns remain for target {target!r}; "
        f"df has 0 feature column(s) after excluding the target — "
        f"check upstream feature preparation/cleaning."
    )


# @id TEST-AIDS-353
# @verifies REQ-AIDS-100
def test_TEST_AIDS_353():
    """Zero usable feature columns in the cross-validation path raises the same
    clear ValueError, before any fold is iterated."""
    df = pd.DataFrame({"label": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]})
    target = "label"

    with pytest.raises(ValueError) as excinfo:
        train_model(
            df,
            target=target,
            model_type="classification",
            cv_strategy="StratifiedKFold",
            n_splits=5,
        )

    assert str(excinfo.value) == (
        f"train_model: no usable feature columns remain for target {target!r}; "
        f"df has 0 feature column(s) after excluding the target — "
        f"check upstream feature preparation/cleaning."
    )


# @id TEST-AIDS-354
# @verifies REQ-AIDS-100
def test_TEST_AIDS_354():
    """A non-empty feature matrix is unaffected by the new guard (no regression)."""
    df = pd.DataFrame(
        {
            "x1": list(range(40)),
            "label": [1 if i % 2 == 0 else 0 for i in range(40)],
        }
    )

    result = train_model(df, target="label", model_type="classification", test_size=0.25)

    assert set(result.metrics) >= {"accuracy", "precision", "recall"}
