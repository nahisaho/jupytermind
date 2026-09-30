"""Hyperparameter tuning and model comparison.

Implements DES-AIDS-017 (REQ-AIDS-019): evaluates multiple parameter sets
or model candidates against the supervised modeling interface and reports
the best-performing configuration with its metric.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ai_data_scientist.ml_modeling import train_model

_PRIMARY_METRIC = {"classification": "accuracy", "regression": "r2"}
_LOWER_IS_BETTER = {"classification": False, "regression": False}


@dataclass(frozen=True)
class TuningResult:
    best_params: dict
    best_metric: float
    all_candidates: list


# @id CODE-AIDS-019
# @implements REQ-AIDS-019
# @design DES-AIDS-017
def tune_or_compare(
    df: pd.DataFrame,
    target: str,
    grid: list,
    model_type: str = "classification",
) -> TuningResult:
    """Evaluate each parameter set in ``grid`` and report the best one."""
    metric_name = _PRIMARY_METRIC[model_type]
    candidates = []
    for params in grid:
        result = train_model(df, target=target, model_type=model_type, **params)
        candidates.append({"params": params, "metric": result.metrics[metric_name]})

    best = max(candidates, key=lambda c: c["metric"])

    return TuningResult(
        best_params=best["params"],
        best_metric=best["metric"],
        all_candidates=candidates,
    )
