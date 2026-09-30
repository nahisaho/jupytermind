"""Tests for data cleaning operations (REQ-AIDS-004)."""

import pandas as pd

from ai_data_scientist.cleaning import clean_dataset


# @id TEST-AIDS-004
# @verifies REQ-AIDS-004
def test_TEST_AIDS_004():
    df = pd.DataFrame(
        {
            "a": [1, 1, 2, None, 4],
            "b": [10, 10, 20, 30, None],
        }
    )

    dedup = clean_dataset(df, operation="drop_duplicates")
    assert dedup.rows_before == 5
    assert dedup.rows_after == 4
    assert dedup.rows_removed == 1
    assert dedup.columns_affected == ["a", "b"]

    dropped = clean_dataset(df, operation="drop_na", columns=["a"])
    assert dropped.rows_before == 5
    assert dropped.rows_after == 4
    assert dropped.rows_removed == 1

    filled = clean_dataset(df, operation="fillna", columns=["b"], fill_value=0)
    assert filled.dataframe["b"].isna().sum() == 0
    assert filled.columns_affected == ["b"]
