"""Tests for supervised ML modeling (REQ-AIDS-008)."""

import pandas as pd

from ai_data_scientist.ml_modeling import train_model


# @id TEST-AIDS-008
# @verifies REQ-AIDS-008
def test_TEST_AIDS_008():
    df = pd.DataFrame(
        {
            "x1": list(range(40)),
            "x2": [i % 5 for i in range(40)],
            "label": [1 if i % 2 == 0 else 0 for i in range(40)],
        }
    )

    result = train_model(df, target="label", model_type="classification", test_size=0.25)

    assert set(result.metrics) >= {"accuracy", "precision", "recall"}
    assert not (set(result.train_index) & set(result.test_index))
    assert set(result.train_index) | set(result.test_index) == set(df.index)

    regression_df = pd.DataFrame(
        {"x1": list(range(40)), "y": [float(i) * 2.0 + 1.0 for i in range(40)]}
    )
    reg_result = train_model(regression_df, target="y", model_type="regression", test_size=0.25)
    assert set(reg_result.metrics) >= {"rmse", "r2"}
    assert not (set(reg_result.train_index) & set(reg_result.test_index))
