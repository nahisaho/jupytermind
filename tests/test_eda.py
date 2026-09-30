"""Tests for exploratory data analysis (REQ-AIDS-005)."""

import pandas as pd

from ai_data_scientist.eda import explore


# @id TEST-AIDS-005
# @verifies REQ-AIDS-005
def test_TEST_AIDS_005():
    df = pd.DataFrame({"x": [1, 2, 3, 4, None], "y": ["a", "b", "c", "d", "e"]})

    report = explore(df)

    reference_describe = df.describe()
    assert report.describe["x"]["mean"] == reference_describe["x"]["mean"]
    assert report.describe["x"]["std"] == reference_describe["x"]["std"]

    reference_info_counts = df.count().to_dict()
    assert report.non_null_counts == reference_info_counts

    assert report.dtypes["x"] == str(df["x"].dtype)
    assert report.dtypes["y"] == str(df["y"].dtype)
