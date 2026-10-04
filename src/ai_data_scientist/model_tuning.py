"""Hyperparameter tuning and model comparison.

Implements DES-AIDS-017 (REQ-AIDS-019): evaluates multiple parameter sets
or model candidates against the supervised modeling interface and reports
the best-performing configuration with its metric.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import pandas as pd

from ai_data_scientist.ml_modeling import (
    _DEFAULT_SCORING,
    _metric_direction,
    build_cv_splits,
    train_model,
)


@dataclass(frozen=True)
class TuningResult:
    best_params: dict
    best_metric: float
    all_candidates: list
    scoring: str | None = None
    cv_splits: list[tuple[list, list]] | None = None
    best_result: object | None = None


# @id CODE-AIDS-019
# @implements REQ-AIDS-019
# @design DES-AIDS-017
def tune_or_compare(
    df: pd.DataFrame,
    target: str,
    grid: list,
    model_type: str = "classification",
    scoring: str | None = None,
    cv_strategy: str | None = None,
    n_splits: int = 5,
    random_state: int = 42,
    groups: str | Sequence[Any] | pd.Series | None = None,
    cv_splits: Sequence[tuple[Sequence[Any], Sequence[Any]]] | None = None,
) -> TuningResult:
    """Evaluate each parameter set in ``grid`` and report the best one."""
    metric_name = scoring or _DEFAULT_SCORING[model_type]

    # @id CODE-AIDS-123
    # @implements REQ-AIDS-076 REQ-AIDS-078
    # @design DES-AIDS-064
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
    for params in grid:
        params_copy = dict(params)
        result = train_model(
            df,
            target=target,
            model_type=model_type,
            scoring=scoring,
            cv_strategy=cv_strategy,
            n_splits=n_splits,
            random_state=random_state,
            groups=groups,
            cv_splits=shared_cv_splits,
            **params_copy,
        )
        candidates.append(
            {
                "params": params_copy,
                "metric": result.metrics[metric_name],
                "fold_scores": result.fold_scores,
                "result": result,
                "cv_splits": result.cv_splits,
            }
        )

    choose_max = _metric_direction(model_type, scoring)
    best = (
        max(candidates, key=lambda candidate: candidate["metric"])
        if choose_max
        else min(candidates, key=lambda candidate: candidate["metric"])
    )

    return TuningResult(
        best_params=best["params"],
        best_metric=best["metric"],
        all_candidates=candidates,
        scoring=metric_name,
        cv_splits=shared_cv_splits,
        best_result=best["result"],
    )
