"""Automated model selection (AutoML).

Implements DES-AIDS-018 (REQ-AIDS-020): trains multiple candidate model
types via the supervised modeling and tuning interfaces and reports a
ranked comparison of their evaluation metrics.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ai_data_scientist.ml_modeling import MODEL_BUILDERS, train_model

_PRIMARY_METRIC = {"classification": "accuracy", "regression": "r2"}


@dataclass(frozen=True)
class AutoMLResult:
    ranked_candidates: list


# @id CODE-AIDS-020
# @implements REQ-AIDS-020
# @design DES-AIDS-018
def run_automl(df: pd.DataFrame, target: str, model_type: str = "classification") -> AutoMLResult:
    """Train several candidate model types and rank them by metric."""
    metric_name = _PRIMARY_METRIC[model_type]
    candidates = []
    for model_name in MODEL_BUILDERS[model_type]:
        result = train_model(df, target=target, model_type=model_type, model_name=model_name)
        candidates.append({"model_name": model_name, "metric": result.metrics[metric_name]})

    ranked = sorted(candidates, key=lambda c: c["metric"], reverse=True)
    return AutoMLResult(ranked_candidates=ranked)
