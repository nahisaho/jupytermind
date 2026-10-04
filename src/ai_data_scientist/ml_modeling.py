"""Supervised ML modeling.

Implements DES-AIDS-012 (REQ-AIDS-008): splits a dataframe into train/test
partitions, trains the requested classification or regression model, and
reports the appropriate evaluation metrics for that model type.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    log_loss,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold, KFold, StratifiedKFold, train_test_split

MODEL_BUILDERS = {
    "classification": {
        "random_forest": lambda **params: RandomForestClassifier(random_state=42, **params),
        "logistic_regression": lambda **params: LogisticRegression(max_iter=1000, **params),
        "gradient_boosting": lambda **params: GradientBoostingClassifier(random_state=42, **params),
    },
    "regression": {
        "random_forest": lambda **params: RandomForestRegressor(random_state=42, **params),
        "linear_regression": lambda **params: LinearRegression(**params),
        "gradient_boosting": lambda **params: GradientBoostingRegressor(random_state=42, **params),
    },
}

_DEFAULT_SCORING = {"classification": "accuracy", "regression": "r2"}


@dataclass(frozen=True)
class ModelResult:
    model: object
    metrics: dict
    train_index: list
    test_index: list
    scoring: str | None = None
    fold_scores: list[float] | None = None
    cv_splits: list[tuple[list, list]] | None = None
    oof_predictions: pd.Series | None = None
    oof_probabilities: pd.DataFrame | None = None


# @id CODE-AIDS-119
# @implements REQ-AIDS-074
# @design DES-AIDS-062
def build_cv_splits(
    df: pd.DataFrame,
    target: str,
    model_type: str,
    cv_strategy: str | None,
    n_splits: int,
    random_state: int,
    groups: str | Sequence[Any] | pd.Series | None = None,
    cv_splits: Sequence[tuple[Sequence[Any], Sequence[Any]]] | None = None,
) -> list[tuple[list, list]] | None:
    """Build or normalize reusable cross-validation splits."""
    _validate_cv_dataframe_index(df)
    if cv_splits is not None:
        normalized = [(list(train_idx), list(test_idx)) for train_idx, test_idx in cv_splits]
        if not normalized:
            raise ValueError("cv_splits must not be empty")
        _validate_cv_splits(df.index, normalized)
        return normalized
    if cv_strategy is None:
        return None
    if n_splits < 2:
        raise ValueError("n_splits must be at least 2")

    features = df.drop(columns=[target])
    labels = df[target]
    if cv_strategy == "StratifiedKFold":
        if model_type != "classification":
            raise ValueError("StratifiedKFold is supported only for classification")
        splitter = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
        split_iter = splitter.split(features, labels)
    elif cv_strategy == "KFold":
        splitter = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
        split_iter = splitter.split(features, labels)
    elif cv_strategy == "GroupKFold":
        group_values = _normalize_groups(df, groups)
        splitter = GroupKFold(n_splits=n_splits)
        split_iter = splitter.split(features, labels, group_values)
    else:
        raise ValueError(f"Unsupported cv_strategy: {cv_strategy!r}")

    normalized = [
        (df.index[train_positions].tolist(), df.index[test_positions].tolist())
        for train_positions, test_positions in split_iter
    ]
    _validate_cv_splits(df.index, normalized)
    return normalized


# @id CODE-AIDS-120
# @implements REQ-AIDS-078
# @design DES-AIDS-066
def resolve_estimator(
    model_type: str,
    model_name: str | None = None,
    estimator: object | Callable[..., object] | None = None,
    model_params: dict[str, Any] | None = None,
) -> object:
    """Resolve a built-in model or external estimator into a fresh estimator."""
    model_params = dict(model_params or {})
    if estimator is not None:
        return _materialize_external_estimator(estimator, model_params)

    builders = MODEL_BUILDERS.get(model_type)
    if builders is None:
        raise ValueError(f"Unsupported model_type: {model_type!r}")
    resolved_model_name = model_name or next(iter(builders))
    if resolved_model_name not in builders:
        raise ValueError(f"Unsupported model_name {resolved_model_name!r} for {model_type!r}")
    return builders[resolved_model_name](**model_params)


# @id CODE-AIDS-121
# @implements REQ-AIDS-075
# @design DES-AIDS-063
def compute_score(
    model_type: str,
    scoring: str,
    y_true: pd.Series,
    predictions: pd.Series,
    probabilities: pd.DataFrame | None = None,
) -> float:
    """Compute the requested score from held-out predictions."""
    if model_type == "classification":
        if scoring == "accuracy":
            return float(accuracy_score(y_true, predictions))
        if scoring == "precision":
            return float(precision_score(y_true, predictions, average="macro", zero_division=0))
        if scoring == "recall":
            return float(recall_score(y_true, predictions, average="macro", zero_division=0))
        if scoring == "roc_auc":
            probabilities = _require_probabilities(probabilities, scoring)
            if probabilities.shape[1] == 2:
                return float(roc_auc_score(y_true, probabilities.iloc[:, -1]))
            return float(roc_auc_score(y_true, probabilities, multi_class="ovr"))
        if scoring == "log_loss":
            probabilities = _require_probabilities(probabilities, scoring)
            return float(log_loss(y_true, probabilities, labels=list(probabilities.columns)))
        raise ValueError(f"Unsupported scoring {scoring!r} for classification")

    if scoring == "r2":
        return float(r2_score(y_true, predictions))
    if scoring == "rmse":
        return float(np.sqrt(mean_squared_error(y_true, predictions)))
    raise ValueError(f"Unsupported scoring {scoring!r} for regression")


def _metric_direction(model_type: str, scoring: str | None) -> bool:
    selected = scoring or _DEFAULT_SCORING[model_type]
    return selected not in {"log_loss", "rmse"}


def _materialize_external_estimator(
    estimator: object | Callable[..., object], model_params: dict[str, Any]
) -> object:
    if hasattr(estimator, "fit") and hasattr(estimator, "predict"):
        resolved = clone(estimator)
        if model_params:
            if not hasattr(resolved, "set_params"):
                raise ValueError("External estimator does not support parameter overrides")
            resolved = resolved.set_params(**model_params)
        return resolved
    if callable(estimator):
        resolved = estimator(**model_params)
        if not hasattr(resolved, "fit") or not hasattr(resolved, "predict"):
            raise ValueError("Resolved estimator must implement fit and predict")
        return resolved
    raise ValueError("External estimator must be cloneable or callable")


def _normalize_groups(
    df: pd.DataFrame, groups: str | Sequence[Any] | pd.Series | None
) -> pd.Series:
    if groups is None:
        raise ValueError("groups are required when cv_strategy='GroupKFold'")
    if isinstance(groups, str):
        if groups not in df.columns:
            raise ValueError(f"Unknown groups column: {groups!r}")
        return df[groups]
    group_series = pd.Series(groups, index=df.index)
    if len(group_series) != len(df.index):
        raise ValueError("groups must have one value per input row")
    return group_series


def _require_probabilities(probabilities: pd.DataFrame | None, scoring: str) -> pd.DataFrame:
    if probabilities is None:
        raise ValueError(f"scoring={scoring!r} requires an estimator with predict_proba")
    return probabilities


def _predict_probabilities(model: object, x_test: pd.DataFrame) -> pd.DataFrame | None:
    if not hasattr(model, "predict_proba"):
        return None
    probability_values = model.predict_proba(x_test)
    classes = list(getattr(model, "classes_", range(probability_values.shape[1])))
    return pd.DataFrame(probability_values, index=x_test.index, columns=classes)


def _validate_cv_dataframe_index(df: pd.DataFrame) -> None:
    if not df.index.is_unique:
        raise ValueError("Cross-validation requires a DataFrame with unique index labels")


def _validate_cv_splits(
    index: pd.Index, cv_splits: Sequence[tuple[Sequence[Any], Sequence[Any]]]
) -> None:
    allowed_labels = set(index.tolist())
    test_counts: Counter[Any] = Counter()

    for fold_number, (train_idx, test_idx) in enumerate(cv_splits, start=1):
        train_labels = list(train_idx)
        test_labels = list(test_idx)
        unknown_labels = (set(train_labels) | set(test_labels)) - allowed_labels
        if unknown_labels:
            raise ValueError(
                "cv_splits fold "
                f"{fold_number} contains unknown index labels: {sorted(unknown_labels)!r}"
            )
        overlap = set(train_labels) & set(test_labels)
        if overlap:
            raise ValueError(
                f"cv_splits fold {fold_number} has train/test overlap: {sorted(overlap)!r}"
            )
        duplicate_test_labels = [
            label for label, count in Counter(test_labels).items() if count > 1
        ]
        if duplicate_test_labels:
            raise ValueError(
                "cv_splits fold "
                f"{fold_number} repeats test index labels: {sorted(duplicate_test_labels)!r}"
            )
        test_counts.update(test_labels)

    missing_test_labels = [label for label in index if test_counts[label] == 0]
    duplicate_test_coverage = [label for label, count in test_counts.items() if count > 1]
    if missing_test_labels:
        raise ValueError(
            "cv_splits must assign every row to exactly one test fold; "
            f"missing test coverage for: {missing_test_labels!r}"
        )
    if duplicate_test_coverage:
        raise ValueError(
            "cv_splits must assign every row to exactly one test fold; "
            f"duplicate test coverage for: {sorted(duplicate_test_coverage)!r}"
        )


def _classification_metrics(
    y_true: pd.Series,
    predictions: pd.Series,
    scoring: str | None,
    probabilities: pd.DataFrame | None,
) -> dict[str, float]:
    metrics = {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, average="macro", zero_division=0)),
        "recall": float(recall_score(y_true, predictions, average="macro", zero_division=0)),
    }
    if scoring and scoring not in metrics:
        metrics[scoring] = compute_score(
            "classification", scoring, y_true, predictions, probabilities
        )
    return metrics


def _regression_metrics(
    y_true: pd.Series, predictions: pd.Series, scoring: str | None
) -> dict[str, float]:
    metrics = {
        "rmse": float(np.sqrt(mean_squared_error(y_true, predictions))),
        "r2": float(r2_score(y_true, predictions)),
    }
    if scoring and scoring not in metrics:
        metrics[scoring] = compute_score("regression", scoring, y_true, predictions)
    return metrics


# @id CODE-AIDS-008
# @implements REQ-AIDS-008
# @design DES-AIDS-012
def train_model(
    df: pd.DataFrame,
    target: str,
    model_type: str = "classification",
    model_name: str = "random_forest",
    test_size: float = 0.2,
    random_state: int = 42,
    scoring: str | None = None,
    cv_strategy: str | None = None,
    n_splits: int = 5,
    groups: str | Sequence[Any] | pd.Series | None = None,
    cv_splits: Sequence[tuple[Sequence[Any], Sequence[Any]]] | None = None,
    estimator: object | Callable[..., object] | None = None,
    **model_params,
) -> ModelResult:
    """Train a classification or regression model on ``df``.

    Defaults to the legacy single holdout split. When cross-validation is
    requested, returns fold scores and out-of-fold artifacts aligned to the
    original row order.
    """
    if model_type not in MODEL_BUILDERS:
        raise ValueError(f"Unsupported model_type: {model_type!r}")

    feature_columns = [c for c in df.columns if c != target]
    x = df[feature_columns]
    y = df[target]
    selected_scoring = scoring or _DEFAULT_SCORING[model_type]

    # @id CODE-AIDS-122
    # @implements REQ-AIDS-074 REQ-AIDS-075 REQ-AIDS-078
    # @design DES-AIDS-063
    normalized_cv_splits = build_cv_splits(
        df=df,
        target=target,
        model_type=model_type,
        cv_strategy=cv_strategy,
        n_splits=n_splits,
        random_state=random_state,
        groups=groups,
        cv_splits=cv_splits,
    )
    if normalized_cv_splits is None:
        train_idx, test_idx = train_test_split(
            df.index, test_size=test_size, random_state=random_state
        )
        model = resolve_estimator(
            model_type=model_type,
            model_name=model_name,
            estimator=estimator,
            model_params=model_params,
        )
        model.fit(x.loc[train_idx], y.loc[train_idx])
        predictions = pd.Series(model.predict(x.loc[test_idx]), index=test_idx)
        probabilities = (
            _predict_probabilities(model, x.loc[test_idx])
            if model_type == "classification"
            else None
        )
        metrics = (
            _classification_metrics(y.loc[test_idx], predictions, scoring, probabilities)
            if model_type == "classification"
            else _regression_metrics(y.loc[test_idx], predictions, scoring)
        )
        return ModelResult(
            model=model,
            metrics=metrics,
            train_index=list(train_idx),
            test_index=list(test_idx),
            scoring=scoring,
        )

    oof_predictions = pd.Series(index=df.index, dtype=object)
    oof_probabilities: pd.DataFrame | None = None
    fold_scores: list[float] = []

    for train_idx, test_idx in normalized_cv_splits:
        fold_model = resolve_estimator(
            model_type=model_type,
            model_name=model_name,
            estimator=estimator,
            model_params=model_params,
        )
        x_train = x.loc[train_idx]
        x_test = x.loc[test_idx]
        y_train = y.loc[train_idx]
        y_test = y.loc[test_idx]
        fold_model.fit(x_train, y_train)

        fold_predictions = pd.Series(fold_model.predict(x_test), index=test_idx)
        oof_predictions.loc[test_idx] = fold_predictions
        fold_probabilities = (
            _predict_probabilities(fold_model, x_test) if model_type == "classification" else None
        )
        if fold_probabilities is not None:
            if oof_probabilities is None:
                oof_probabilities = pd.DataFrame(
                    index=df.index, columns=fold_probabilities.columns, dtype=float
                )
            oof_probabilities.loc[test_idx, fold_probabilities.columns] = fold_probabilities

        fold_scores.append(
            compute_score(
                model_type, selected_scoring, y_test, fold_predictions, fold_probabilities
            )
        )

    final_model = resolve_estimator(
        model_type=model_type,
        model_name=model_name,
        estimator=estimator,
        model_params=model_params,
    )
    final_model.fit(x, y)

    cast_predictions = oof_predictions.astype(y.dtype)
    metrics = (
        _classification_metrics(y, cast_predictions, scoring, oof_probabilities)
        if model_type == "classification"
        else _regression_metrics(y, cast_predictions.astype(float), scoring)
    )
    metrics[selected_scoring] = compute_score(
        model_type,
        selected_scoring,
        y,
        cast_predictions if model_type == "classification" else cast_predictions.astype(float),
        oof_probabilities,
    )

    return ModelResult(
        model=final_model,
        metrics=metrics,
        train_index=list(normalized_cv_splits[0][0]),
        test_index=list(normalized_cv_splits[0][1]),
        scoring=selected_scoring,
        fold_scores=fold_scores,
        cv_splits=normalized_cv_splits,
        oof_predictions=cast_predictions,
        oof_probabilities=oof_probabilities,
    )
