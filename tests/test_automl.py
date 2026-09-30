"""Tests for automated model selection / AutoML (REQ-AIDS-020)."""

import pandas as pd

from ai_data_scientist.automl import run_automl


# @id TEST-AIDS-020
# @verifies REQ-AIDS-020
def test_TEST_AIDS_020():
    df = pd.DataFrame(
        {
            "x1": list(range(60)),
            "x2": [i % 7 for i in range(60)],
            "label": [1 if (i % 3 == 0) else 0 for i in range(60)],
        }
    )

    result = run_automl(df, target="label", model_type="classification")

    assert len(result.ranked_candidates) >= 3
    metrics = [c["metric"] for c in result.ranked_candidates]
    assert metrics == sorted(metrics, reverse=True)
    for candidate in result.ranked_candidates:
        assert "model_name" in candidate
        assert "metric" in candidate
