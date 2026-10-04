"""Automated model selection (AutoML).

Implements DES-AIDS-018 (REQ-AIDS-020): trains multiple candidate model
types via the supervised modeling and tuning interfaces and reports a
ranked comparison of their evaluation metrics.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import pandas as pd

from ai_data_scientist.ml_modeling import (
    _DEFAULT_SCORING,
    MODEL_BUILDERS,
    _metric_direction,
    build_cv_splits,
    train_model,
)


@dataclass(frozen=True)
class AutoMLResult:
    ranked_candidates: list
    scoring: str | None = None
    cv_splits: list[tuple[list, list]] | None = None


# @id CODE-AIDS-124
# @implements REQ-AIDS-078
# @design DES-AIDS-065 DES-AIDS-066
def build_candidate_estimators(
    model_type: str, candidate_estimators: dict[str, object | Callable[..., object]] | None = None
) -> dict[str, object | Callable[..., object] | None]:
    """Build the AutoML candidate registry."""
    candidates: dict[str, object | Callable[..., object] | None] = {
        name: None for name in MODEL_BUILDERS[model_type]
    }
    if candidate_estimators:
        candidates.update(candidate_estimators)
    return candidates


# @id CODE-AIDS-020
# @implements REQ-AIDS-020
# @design DES-AIDS-018
def run_automl(
    df: pd.DataFrame,
    target: str,
    model_type: str = "classification",
    scoring: str | None = None,
    cv_strategy: str | None = None,
    n_splits: int = 5,
    random_state: int = 42,
    groups: str | Sequence[Any] | pd.Series | None = None,
    cv_splits: Sequence[tuple[Sequence[Any], Sequence[Any]]] | None = None,
    candidate_estimators: dict[str, object | Callable[..., object]] | None = None,
) -> AutoMLResult:
    """Train several candidate model types and rank them by metric."""
    metric_name = scoring or _DEFAULT_SCORING[model_type]

    # @id CODE-AIDS-100
    # @implements REQ-AIDS-077 REQ-AIDS-078
    # @design DES-AIDS-065
    shared_cv_splits = build_cv_splits(
        df=df,
        target=target,
        model_type=model_type,
        cv_strategy=cv_strategy,
        n_splits=n_splits,
        random_state=random_state,
        groups=groups,
        cv_splits=cv_splits,
    )
    candidates = []
    for model_name, estimator in build_candidate_estimators(
        model_type, candidate_estimators
    ).items():
        result = train_model(
            df,
            target=target,
            model_type=model_type,
            model_name=model_name if estimator is None else next(iter(MODEL_BUILDERS[model_type])),
            scoring=scoring,
            cv_strategy=cv_strategy,
            n_splits=n_splits,
            random_state=random_state,
            groups=groups,
            cv_splits=shared_cv_splits,
            estimator=estimator,
        )
        candidates.append(
            {
                "model_name": model_name,
                "metric": result.metrics[metric_name],
                "fold_scores": result.fold_scores,
                "result": result,
            }
        )

    ranked = sorted(
        candidates,
        key=lambda candidate: candidate["metric"],
        reverse=_metric_direction(model_type, scoring),
    )
    return AutoMLResult(ranked_candidates=ranked, scoring=metric_name, cv_splits=shared_cv_splits)
