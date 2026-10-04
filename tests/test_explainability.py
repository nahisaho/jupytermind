"""Tests for model explainability (REQ-AIDS-021/082/083/084)."""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from ai_data_scientist.explainability import explain_model
from ai_data_scientist.ml_modeling import train_model


# @id TEST-AIDS-021
# @verifies REQ-AIDS-021
def test_TEST_AIDS_021():
    rng = np.random.default_rng(0)
    n = 80
    important = np.arange(n) % 2
    noise = rng.integers(0, 5, size=n)
    df = pd.DataFrame({"important": important, "noise": noise, "label": important})

    result = train_model(df, target="label", model_type="classification", test_size=0.2)

    explanation = explain_model(result.model, feature_names=["important", "noise"])

    reference_importances = dict(zip(["important", "noise"], result.model.feature_importances_))
    reference_top = max(reference_importances, key=reference_importances.get)

    assert explanation.ranking[0] == reference_top
    assert set(explanation.feature_importances) == {"important", "noise"}
    assert explanation.importance_kind == "split"


# @id TEST-AIDS-169
# @verifies REQ-AIDS-082
def test_TEST_AIDS_169():
    df = pd.DataFrame(
        {
            "important": [0, 0, 0, 1, 1, 1, 0, 1] * 12,
            "noise": [0, 1, 2, 2, 1, 0, 1, 2] * 12,
            "label": [0, 0, 0, 1, 1, 1, 0, 1] * 12,
        }
    )

    result = train_model(
        df,
        target="label",
        model_type="classification",
        model_name="logistic_regression",
        test_size=0.25,
    )

    explanation = explain_model(result.model, feature_names=["important", "noise"])

    reference_importances = abs(result.model.coef_).reshape(-1)
    reference = dict(zip(["important", "noise"], reference_importances))

    assert explanation.feature_importances == pytest.approx(reference)
    assert explanation.ranking == sorted(reference, key=reference.get, reverse=True)
    assert explanation.importance_kind == "coefficient_magnitude"


# @id TEST-AIDS-170
# @verifies REQ-AIDS-084
def test_TEST_AIDS_170():
    rng = np.random.default_rng(1)
    n = 120
    important = np.tile([0, 1], n // 2)
    noise = rng.integers(0, 4, size=n)
    df = pd.DataFrame({"important": important, "noise": noise, "label": important})

    result = train_model(
        df,
        target="label",
        model_type="classification",
        model_name="logistic_regression",
        test_size=0.25,
    )

    explanation = explain_model(
        result.model,
        feature_names=["important", "noise"],
        method="permutation",
        x=df[["important", "noise"]],
        y=df["label"],
        scoring="accuracy",
        n_repeats=8,
        random_state=7,
    )

    assert explanation.importance_kind == "permutation"
    assert explanation.scoring == "accuracy"
    assert explanation.ranking[0] == "important"
    assert explanation.feature_importances["important"] > explanation.feature_importances["noise"]


# @id TEST-AIDS-171
# @verifies REQ-AIDS-083
def test_TEST_AIDS_171():
    df = pd.DataFrame(
        {
            "important": [0, 0, 0, 1, 1, 1, 0, 1] * 12,
            "noise": [0, 1, 2, 2, 1, 0, 1, 2] * 12,
            "label": [0, 0, 0, 1, 1, 1, 0, 1] * 12,
        }
    )

    result = train_model(
        df,
        target="label",
        model_type="classification",
        model_name="logistic_regression",
        test_size=0.25,
    )
    rows = df.loc[[0, 3, 4], ["important", "noise"]]

    explanation = explain_model(
        result.model,
        feature_names=["important", "noise"],
        method="signed_contributions",
        x=rows,
    )

    assert explanation.contribution_kind in {"linear", "shap"}
    assert explanation.importance_kind == "mean_absolute_signed_contribution"
    assert explanation.ranking[0] == "important"
    assert len(explanation.signed_contributions) == len(rows)
    assert explanation.signed_contributions[0]["important"] == pytest.approx(0.0)
    assert explanation.signed_contributions[1]["important"] > 0.0
    assert explanation.additivity_check["passed"] is True
    assert explanation.additivity_check["max_abs_error"] <= 1e-6


# @id TEST-AIDS-172
# @verifies REQ-AIDS-083
def test_TEST_AIDS_172():
    class FakePredContribModel:
        def predict(self, frame, pred_contrib=False, raw_score=False):
            values = frame.to_numpy(dtype=float)
            raw = values[:, 0] * 2.0 + values[:, 1] * -0.5 + 1.25
            if pred_contrib:
                return np.column_stack(
                    [values[:, 0] * 2.0, values[:, 1] * -0.5, np.full(len(values), 1.25)]
                )
            if raw_score:
                return raw
            return raw

    rows = pd.DataFrame({"signal": [1.0, 3.0], "noise": [2.0, 1.0]})

    explanation = explain_model(
        FakePredContribModel(),
        feature_names=["signal", "noise"],
        method="signed_contributions",
        x=rows,
    )

    assert explanation.contribution_kind == "pred_contrib"
    assert explanation.importance_kind == "mean_absolute_signed_contribution"
    assert explanation.ranking[0] == "signal"
    assert explanation.baseline_values == pytest.approx([1.25, 1.25])
    assert explanation.raw_predictions == pytest.approx([2.25, 6.75])
    assert explanation.additivity_check["passed"] is True
    assert explanation.additivity_check["max_abs_error"] <= 1e-12


# @id TEST-AIDS-173
# @verifies REQ-AIDS-083
def test_TEST_AIDS_173(monkeypatch):
    df = pd.DataFrame(
        {
            "important": [0, 0, 0, 1, 1, 1, 0, 1] * 12,
            "noise": [0, 1, 2, 2, 1, 0, 1, 2] * 12,
            "label": [0, 0, 0, 1, 1, 1, 0, 1] * 12,
        }
    )

    result = train_model(
        df,
        target="label",
        model_type="classification",
        model_name="logistic_regression",
        test_size=0.25,
    )
    rows = df.loc[[0, 3, 4], ["important", "noise"]]

    monkeypatch.setattr(
        "ai_data_scientist.explainability.import_module",
        lambda name: (_ for _ in ()).throw(ModuleNotFoundError(name)),
    )

    explanation = explain_model(
        result.model,
        feature_names=["important", "noise"],
        method="signed_contributions",
        x=rows,
    )

    assert explanation.contribution_kind == "linear"
    assert explanation.additivity_check["checked_against_model_output"] is True
    assert explanation.additivity_check["passed"] is True


# @id TEST-AIDS-174
# @verifies REQ-AIDS-083
def test_TEST_AIDS_174(monkeypatch):
    class FakeShapModule:
        @staticmethod
        def Explainer(model, frame):
            def run(rows):
                values = rows.to_numpy(dtype=float) * np.array([2.0, -0.5])
                base_values = np.full(len(rows), 1.0)
                return SimpleNamespace(values=values, base_values=base_values)

            return run

    class LinearModelWithoutRawAccess:
        coef_ = np.array([[2.0, -0.5]])
        intercept_ = np.array([1.0])

        def decision_function(self, frame):
            values = frame.to_numpy(dtype=float)
            return values[:, 0] * 2.0 + values[:, 1] * -0.5 + 1.0

    rows = pd.DataFrame({"signal": [1.0, 3.0], "noise": [2.0, 1.0]})
    monkeypatch.setattr(
        "ai_data_scientist.explainability.import_module", lambda name: FakeShapModule()
    )

    explanation = explain_model(
        LinearModelWithoutRawAccess(),
        feature_names=["signal", "noise"],
        method="signed_contributions",
        x=rows,
    )

    assert explanation.contribution_kind == "shap"
    assert explanation.baseline_values == pytest.approx([1.0, 1.0])
    assert explanation.raw_predictions == pytest.approx([2.0, 6.5])
    assert explanation.additivity_check["passed"] is True
    assert explanation.additivity_check["max_abs_error"] <= 1e-12


# @id TEST-AIDS-175
# @verifies REQ-AIDS-083
def test_TEST_AIDS_175():
    class PredContribWithoutRawModel:
        def predict(self, frame, *, pred_contrib=False):
            if not pred_contrib:
                raise TypeError("raw output unavailable")
            values = frame.to_numpy(dtype=float)
            return np.column_stack(
                [values[:, 0] * 2.0, values[:, 1] * -0.5, np.full(len(values), 1.25)]
            )

    rows = pd.DataFrame({"signal": [1.0, 3.0], "noise": [2.0, 1.0]})

    explanation = explain_model(
        PredContribWithoutRawModel(),
        feature_names=["signal", "noise"],
        method="signed_contributions",
        x=rows,
    )

    assert explanation.contribution_kind == "pred_contrib"
    assert explanation.raw_predictions is None
    assert explanation.additivity_check["checked_against_model_output"] is False
    assert explanation.additivity_check["passed"] is None
    assert explanation.additivity_check["max_abs_error"] is None


# @id TEST-AIDS-176
# @verifies REQ-AIDS-083
def test_TEST_AIDS_176(monkeypatch):
    class InvalidPredContribWithShapFallbackModel:
        def predict(self, frame, pred_contrib=False):
            if pred_contrib:
                values = frame.to_numpy(dtype=float)
                return values.reshape(len(frame), 2, 1)
            raise TypeError("raw output unavailable")

    class FakeShapModule:
        @staticmethod
        def Explainer(model, frame):
            def run(rows):
                values = rows.to_numpy(dtype=float) * np.array([2.0, -0.5])
                base_values = np.full(len(rows), 1.0)
                return SimpleNamespace(values=values, base_values=base_values)

            return run

    rows = pd.DataFrame({"signal": [1.0, 3.0], "noise": [2.0, 1.0]})
    monkeypatch.setattr(
        "ai_data_scientist.explainability.import_module", lambda name: FakeShapModule()
    )

    explanation = explain_model(
        InvalidPredContribWithShapFallbackModel(),
        feature_names=["signal", "noise"],
        method="signed_contributions",
        x=rows,
    )

    assert explanation.contribution_kind == "shap"
    assert explanation.baseline_values == pytest.approx([1.0, 1.0])
    assert explanation.raw_predictions is None
    assert explanation.additivity_check["checked_against_model_output"] is False
    assert explanation.additivity_check["passed"] is None

    class InvalidPredContribLinearFallbackModel:
        coef_ = np.array([[2.0, -0.5]])
        intercept_ = np.array([1.0])

        def predict(self, frame, pred_contrib=False):
            if pred_contrib:
                return np.ones((len(frame), 4))
            raise TypeError("raw output unavailable")

        def decision_function(self, frame):
            values = frame.to_numpy(dtype=float)
            return values[:, 0] * 2.0 + values[:, 1] * -0.5 + 1.0

    monkeypatch.setattr(
        "ai_data_scientist.explainability.import_module",
        lambda name: (_ for _ in ()).throw(ModuleNotFoundError(name)),
    )

    rows = pd.DataFrame({"signal": [1.0, 3.0], "noise": [2.0, 1.0]})
    linear_explanation = explain_model(
        InvalidPredContribLinearFallbackModel(),
        feature_names=["signal", "noise"],
        method="signed_contributions",
        x=rows,
    )

    assert linear_explanation.contribution_kind == "linear"
    assert linear_explanation.raw_predictions == pytest.approx([2.0, 6.5])
    assert linear_explanation.additivity_check["checked_against_model_output"] is True
    assert linear_explanation.additivity_check["passed"] is True


# @id TEST-AIDS-177
# @verifies REQ-AIDS-083
def test_TEST_AIDS_177(monkeypatch):
    class WrongRowCountPredContribModel:
        coef_ = np.array([[2.0, -0.5]])
        intercept_ = np.array([1.0])

        def predict(self, frame, pred_contrib=False):
            if pred_contrib:
                return np.ones((len(frame) + 1, 3))
            raise TypeError("raw output unavailable")

        def decision_function(self, frame):
            values = frame.to_numpy(dtype=float)
            return values[:, 0] * 2.0 + values[:, 1] * -0.5 + 1.0

    monkeypatch.setattr(
        "ai_data_scientist.explainability.import_module",
        lambda name: (_ for _ in ()).throw(ModuleNotFoundError(name)),
    )

    rows = pd.DataFrame({"signal": [1.0, 3.0], "noise": [2.0, 1.0]})
    explanation = explain_model(
        WrongRowCountPredContribModel(),
        feature_names=["signal", "noise"],
        method="signed_contributions",
        x=rows,
    )

    assert explanation.contribution_kind == "linear"
    assert explanation.raw_predictions == pytest.approx([2.0, 6.5])
    assert explanation.additivity_check["checked_against_model_output"] is True
    assert explanation.additivity_check["passed"] is True
