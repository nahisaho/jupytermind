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


# @id TEST-AIDS-053
# @verifies REQ-AIDS-043
def test_TEST_AIDS_053_categorical_summary_counts_and_ratios():
    df = pd.DataFrame({"species": ["cat", "cat", "dog", "dog", "dog"]})

    report = explore(df)

    summary = report.categorical_summary["species"]
    assert summary["unique_count"] == 2
    assert summary["truncated"] is False
    top_values = {entry["value"]: entry for entry in summary["top_values"]}
    assert top_values["dog"]["count"] == 3
    assert top_values["dog"]["ratio"] == 3 / 5
    assert top_values["cat"]["count"] == 2
    assert top_values["cat"]["ratio"] == 2 / 5


# @id TEST-AIDS-054
# @verifies REQ-AIDS-043
def test_TEST_AIDS_054_missing_summary_counts_and_ratio_for_every_column():
    df = pd.DataFrame(
        {
            "x": [1, 2, None, None],
            "all_missing": [None, None, None, None],
            "complete": ["a", "b", "c", "d"],
        }
    )

    report = explore(df)

    assert report.missing_summary["x"]["missing_count"] == 2
    assert report.missing_summary["x"]["missing_ratio"] == 0.5
    assert report.missing_summary["all_missing"]["missing_count"] == 4
    assert report.missing_summary["all_missing"]["missing_ratio"] == 1.0
    assert report.missing_summary["complete"]["missing_count"] == 0
    assert report.missing_summary["complete"]["missing_ratio"] == 0.0
    # all_missing is an object/category dtype with no non-null values: the
    # categorical summary must still be well-formed, not raise.
    assert report.categorical_summary["all_missing"]["unique_count"] == 0
    assert report.categorical_summary["all_missing"]["top_values"] == []


# @id TEST-AIDS-055
# @verifies REQ-AIDS-043
def test_TEST_AIDS_055_categorical_summary_truncates_to_top_n():
    df = pd.DataFrame({"code": [f"v{i}" for i in range(20)]})

    report = explore(df, top_n=5)

    summary = report.categorical_summary["code"]
    assert summary["unique_count"] == 20
    assert summary["truncated"] is True
    assert len(summary["top_values"]) == 5


# @id TEST-AIDS-056
# @verifies REQ-AIDS-043
def test_TEST_AIDS_056_empty_and_no_categorical_dataframes_are_stable():
    empty_report = explore(pd.DataFrame())
    assert empty_report.categorical_summary == {}
    assert empty_report.missing_summary == {}

    numeric_only = pd.DataFrame({"x": [1, 2, 3]})
    numeric_report = explore(numeric_only)
    assert numeric_report.categorical_summary == {}
    assert numeric_report.missing_summary["x"]["missing_count"] == 0
