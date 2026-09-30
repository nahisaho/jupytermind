"""Tests for feature engineering (REQ-AIDS-015)."""

import pandas as pd

from ai_data_scientist.feature_engineering import engineer_features


# @id TEST-AIDS-015
# @verifies REQ-AIDS-015
def test_TEST_AIDS_015():
    df = pd.DataFrame({"category": ["a", "b", "a", "c"], "value": [1, 2, 3, 4]})

    result = engineer_features(df, operation="one_hot", columns=["category"])

    reference = pd.get_dummies(df, columns=["category"])
    for col in reference.columns:
        assert col in result.dataframe.columns
    pd.testing.assert_frame_equal(
        result.dataframe[reference.columns].astype(reference.dtypes),
        reference,
        check_like=True,
    )
    assert set(result.added_columns) == {c for c in reference.columns if c not in df.columns}
