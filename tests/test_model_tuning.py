"""Tests for hyperparameter tuning and model comparison (REQ-AIDS-019)."""

import pandas as pd

from ai_data_scientist.model_tuning import tune_or_compare


# @id TEST-AIDS-019
# @verifies REQ-AIDS-019
def test_TEST_AIDS_019():
    df = pd.DataFrame(
        {
            "x1": list(range(60)),
            "x2": [i % 7 for i in range(60)],
            "label": [1 if (i % 3 == 0) else 0 for i in range(60)],
        }
    )
    grid = [
        {"n_estimators": 5, "max_depth": 2},
        {"n_estimators": 20, "max_depth": 4},
        {"n_estimators": 50, "max_depth": None},
    ]

    result = tune_or_compare(df, target="label", grid=grid, model_type="classification")

    candidate_metrics = [c["metric"] for c in result.all_candidates]
    assert result.best_metric == max(candidate_metrics)
    assert result.best_params in grid
    assert len(result.all_candidates) == len(grid)
