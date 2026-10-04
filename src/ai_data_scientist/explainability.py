"""Model explainability.

Implements DES-AIDS-019 plus CHANGE-011's DES-AIDS-070/071/072: preserves the
legacy feature-importance ranking by default, and adds opt-in signed local
contributions and permutation importance.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Literal

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance


@dataclass(frozen=True)
class ExplainabilityResult:
    feature_importances: dict[str, float]
    ranking: list[str]
    importance_kind: str = "unknown"
    contribution_kind: str | None = None
    signed_contributions: list[dict[str, float]] | None = None
    baseline_values: list[float] | None = None
    raw_predictions: list[float] | None = None
    additivity_check: dict[str, float | bool | None] | None = None
    scoring: str | None = None


def _as_feature_frame(x: Any, feature_names: list[str]) -> pd.DataFrame:
    if x is None:
        raise ValueError("x is required for this explainability method.")
    if isinstance(x, pd.DataFrame):
        return x.loc[:, feature_names].copy()

    values = np.asarray(x)
    if values.ndim != 2 or values.shape[1] != len(feature_names):
        raise ValueError("x must be a 2D array-like with one column per feature name.")
    return pd.DataFrame(values, columns=feature_names)


def _build_ranking(feature_importances: dict[str, float]) -> list[str]:
    return sorted(feature_importances, key=feature_importances.get, reverse=True)


def _build_feature_importance_map(
    feature_names: list[str], raw_importances: np.ndarray
) -> dict[str, float]:
    return {name: float(value) for name, value in zip(feature_names, np.asarray(raw_importances))}


# @id CODE-AIDS-107
# @implements REQ-AIDS-082
# @design DES-AIDS-070
def _compute_default_importance(
    model: object, feature_names: list[str]
) -> tuple[dict[str, float], list[str], str]:
    """Return the legacy global-importance ranking and its explicit kind."""
    if hasattr(model, "feature_importances_"):
        raw_importances = np.asarray(model.feature_importances_, dtype=float)
        importance_kind = "split"
    elif hasattr(model, "coef_"):
        raw_importances = np.abs(np.asarray(model.coef_, dtype=float)).reshape(-1)
        importance_kind = "coefficient_magnitude"
    else:
        raise ValueError("Model exposes neither feature_importances_ nor coef_.")

    feature_importances = _build_feature_importance_map(feature_names, raw_importances)
    return feature_importances, _build_ranking(feature_importances), importance_kind


# @id CODE-AIDS-110
# @implements REQ-AIDS-083
# @design DES-AIDS-071
def _predict_raw_output(model: object, frame: pd.DataFrame) -> np.ndarray | None:
    """Best-effort raw-output prediction for additivity checks."""
    if hasattr(model, "decision_function"):
        raw = np.asarray(model.decision_function(frame), dtype=float)
        return raw.reshape(-1)

    for kwargs in ({"raw_score": True}, {"output_margin": True}):
        try:
            raw = np.asarray(model.predict(frame, **kwargs), dtype=float)
        except (TypeError, ValueError):
            continue
        if raw.ndim == 1:
            return raw
        if raw.ndim == 2 and raw.shape[1] == 1:
            return raw.reshape(-1)

    if hasattr(model, "predict") and not hasattr(model, "predict_proba"):
        try:
            raw = np.asarray(model.predict(frame), dtype=float)
        except (TypeError, ValueError):
            return None
        if raw.ndim == 1:
            return raw
        if raw.ndim == 2 and raw.shape[1] == 1:
            return raw.reshape(-1)

    return None


def _finalize_signed_result(
    feature_names: list[str],
    contribution_kind: str,
    contributions: np.ndarray,
    baseline_values: np.ndarray,
    raw_predictions: np.ndarray | None,
) -> ExplainabilityResult:
    contributions = np.asarray(contributions, dtype=float)
    baseline_values = np.asarray(baseline_values, dtype=float).reshape(-1)
    reconstructed = baseline_values + contributions.sum(axis=1)

    if raw_predictions is None:
        raw_prediction_values = None
        checked_against_model_output = False
        max_abs_error = None
        passed = None
    else:
        raw_predictions = np.asarray(raw_predictions, dtype=float).reshape(-1)
        raw_prediction_values = raw_predictions.astype(float).tolist()
        checked_against_model_output = True
        max_abs_error = float(np.max(np.abs(reconstructed - raw_predictions)))
        passed = bool(max_abs_error <= 1e-6)
    signed_contributions = [
        {name: float(value) for name, value in zip(feature_names, row)} for row in contributions
    ]
    feature_importances = _build_feature_importance_map(
        feature_names, np.mean(np.abs(contributions), axis=0)
    )

    return ExplainabilityResult(
        feature_importances=feature_importances,
        ranking=_build_ranking(feature_importances),
        importance_kind="mean_absolute_signed_contribution",
        contribution_kind=contribution_kind,
        signed_contributions=signed_contributions,
        baseline_values=baseline_values.astype(float).tolist(),
        raw_predictions=raw_prediction_values,
        additivity_check={
            "passed": passed,
            "max_abs_error": max_abs_error,
            "checked_against_model_output": checked_against_model_output,
        },
    )


def _normalize_shap_output(
    values: np.ndarray, base_values: np.ndarray, n_rows: int, n_features: int
) -> tuple[np.ndarray, np.ndarray] | None:
    values = np.asarray(values, dtype=float)
    base_values = np.asarray(base_values, dtype=float)

    if values.ndim == 3:
        values = values[..., -1]
    if values.ndim != 2 or values.shape != (n_rows, n_features):
        return None

    if base_values.ndim == 0:
        baseline = np.full(n_rows, float(base_values))
    elif base_values.ndim == 1:
        baseline = base_values.reshape(-1)
    elif base_values.ndim == 2:
        baseline = base_values[:, -1].reshape(-1)
    else:
        return None

    if baseline.shape[0] != n_rows:
        return None
    return values, baseline


# @id CODE-AIDS-109
# @implements REQ-AIDS-083
# @design DES-AIDS-071
def _compute_signed_contributions(
    model: object, frame: pd.DataFrame, feature_names: list[str]
) -> ExplainabilityResult:
    """Return signed local contributions from the best available provider."""
    try:
        native = np.asarray(model.predict(frame, pred_contrib=True), dtype=float)
    except (AttributeError, TypeError, ValueError):
        native = None

    if native is not None and native.ndim == 2 and native.shape[0] == len(frame):
        if native.shape[1] == len(feature_names) + 1:
            contributions = native[:, :-1]
            baseline_values = native[:, -1]
        elif native.shape[1] == len(feature_names):
            contributions = native
            baseline_values = np.zeros(native.shape[0], dtype=float)
        else:
            contributions = None
            baseline_values = None

        if contributions is not None and baseline_values is not None:
            return _finalize_signed_result(
                feature_names,
                contribution_kind="pred_contrib",
                contributions=contributions,
                baseline_values=baseline_values,
                raw_predictions=_predict_raw_output(model, frame),
            )

    try:
        shap = import_module("shap")
    except ModuleNotFoundError:
        shap = None

    if shap is not None:
        try:
            explanation = shap.Explainer(model, frame)(frame)
        except (AttributeError, NotImplementedError, TypeError, ValueError):
            explanation = None
        if explanation is not None:
            normalized = _normalize_shap_output(
                explanation.values,
                explanation.base_values,
                n_rows=len(frame),
                n_features=len(feature_names),
            )
            if normalized is not None:
                values, baseline_values = normalized
                return _finalize_signed_result(
                    feature_names,
                    contribution_kind="shap",
                    contributions=values,
                    baseline_values=baseline_values,
                    raw_predictions=_predict_raw_output(model, frame),
                )

    if hasattr(model, "coef_") and hasattr(model, "intercept_"):
        coef = np.asarray(model.coef_, dtype=float).reshape(-1)
        if coef.shape[0] != len(feature_names):
            raise ValueError("Linear contribution path requires one coefficient per feature.")
        baseline_values = np.full(len(frame), float(np.asarray(model.intercept_).reshape(-1)[0]))
        contributions = frame.to_numpy(dtype=float) * coef
        return _finalize_signed_result(
            feature_names,
            contribution_kind="linear",
            contributions=contributions,
            baseline_values=baseline_values,
            raw_predictions=_predict_raw_output(model, frame),
        )

    raise ValueError(
        "Signed contributions are unavailable for this model. Install optional "
        "`shap`, use a model with native pred_contrib support, or request "
        '`method="permutation"` instead.'
    )


# @id CODE-AIDS-108
# @implements REQ-AIDS-084
# @design DES-AIDS-072
def _compute_permutation_importance(
    model: object,
    frame: pd.DataFrame,
    y: Any,
    feature_names: list[str],
    scoring: str | None,
    n_repeats: int,
    random_state: int,
) -> ExplainabilityResult:
    """Return permutation importance with explicit scoring metadata."""
    if y is None:
        raise ValueError("y is required when method='permutation'.")

    result = permutation_importance(
        model,
        frame,
        np.asarray(y),
        scoring=scoring,
        n_repeats=n_repeats,
        random_state=random_state,
    )
    feature_importances = _build_feature_importance_map(feature_names, result.importances_mean)
    return ExplainabilityResult(
        feature_importances=feature_importances,
        ranking=_build_ranking(feature_importances),
        importance_kind="permutation",
        scoring=scoring,
    )


# @id CODE-AIDS-106
# @implements REQ-AIDS-021 REQ-AIDS-082 REQ-AIDS-083 REQ-AIDS-084
# @design DES-AIDS-019 DES-AIDS-070 DES-AIDS-071 DES-AIDS-072
def explain_model(
    model: object,
    feature_names: list[str],
    *,
    method: Literal["default", "signed_contributions", "permutation"] = "default",
    x: Any = None,
    y: Any = None,
    scoring: str | None = None,
    n_repeats: int = 5,
    random_state: int = 42,
) -> ExplainabilityResult:
    """Explain ``model`` with legacy ranking, signed contributions, or permutation importance."""
    if method == "default":
        feature_importances, ranking, importance_kind = _compute_default_importance(
            model, feature_names
        )
        return ExplainabilityResult(
            feature_importances=feature_importances,
            ranking=ranking,
            importance_kind=importance_kind,
        )

    frame = _as_feature_frame(x, feature_names)
    if method == "signed_contributions":
        return _compute_signed_contributions(model, frame, feature_names)
    if method == "permutation":
        return _compute_permutation_importance(
            model=model,
            frame=frame,
            y=y,
            feature_names=feature_names,
            scoring=scoring,
            n_repeats=n_repeats,
            random_state=random_state,
        )

    raise ValueError(f"Unsupported explainability method: {method!r}")
