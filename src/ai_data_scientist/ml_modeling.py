"""Supervised ML modeling.

Implements DES-AIDS-012 (REQ-AIDS-008): splits a dataframe into train/test
partitions, trains the requested classification or regression model, and
reports the appropriate evaluation metrics for that model type.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

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


@dataclass(frozen=True)
class ModelResult:
    model: object
    metrics: dict
    train_index: list
    test_index: list


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
    **model_params,
) -> ModelResult:
    """Train a classification or regression model on ``df``.

    Splits ``df`` into non-overlapping train/test partitions, fits the
    requested ``model_type``/``model_name``, and reports its evaluation
    metrics (accuracy/precision/recall for classification, rmse/r2 for
    regression).
    """
    if model_type not in MODEL_BUILDERS:
        raise ValueError(f"Unsupported model_type: {model_type!r}")
    builders = MODEL_BUILDERS[model_type]
    if model_name not in builders:
        raise ValueError(f"Unsupported model_name {model_name!r} for {model_type!r}")

    feature_columns = [c for c in df.columns if c != target]
    x = df[feature_columns]
    y = df[target]

    train_idx, test_idx = train_test_split(df.index, test_size=test_size, random_state=random_state)

    model = builders[model_name](**model_params)
    model.fit(x.loc[train_idx], y.loc[train_idx])
    predictions = model.predict(x.loc[test_idx])
    y_test = y.loc[test_idx]

    if model_type == "classification":
        metrics = {
            "accuracy": float(accuracy_score(y_test, predictions)),
            "precision": float(
                precision_score(y_test, predictions, average="macro", zero_division=0)
            ),
            "recall": float(recall_score(y_test, predictions, average="macro", zero_division=0)),
        }
    else:
        metrics = {
            "rmse": float(np.sqrt(mean_squared_error(y_test, predictions))),
            "r2": float(r2_score(y_test, predictions)),
        }

    return ModelResult(
        model=model,
        metrics=metrics,
        train_index=list(train_idx),
        test_index=list(test_idx),
    )
