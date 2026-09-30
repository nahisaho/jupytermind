"""Model explainability.

Implements DES-AIDS-019 (REQ-AIDS-021): computes feature importance or
SHAP values for a model trained via the supervised modeling module and
reports them alongside a ranking.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExplainabilityResult:
    feature_importances: dict
    ranking: list


# @id CODE-AIDS-021
# @implements REQ-AIDS-021
# @design DES-AIDS-019
def explain_model(model: object, feature_names: list) -> ExplainabilityResult:
    """Report feature importances for ``model`` ranked by magnitude."""
    if hasattr(model, "feature_importances_"):
        raw_importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        raw_importances = abs(model.coef_).reshape(-1)
    else:
        raise ValueError("Model exposes neither feature_importances_ nor coef_.")

    feature_importances = {
        name: float(value) for name, value in zip(feature_names, raw_importances)
    }
    ranking = sorted(feature_importances, key=feature_importances.get, reverse=True)

    return ExplainabilityResult(feature_importances=feature_importances, ranking=ranking)
