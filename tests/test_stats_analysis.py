"""Tests for statistical analysis (REQ-AIDS-006)."""

import pandas as pd
from scipy import stats as scipy_stats

from ai_data_scientist.stats_analysis import correlation


# @id TEST-AIDS-006
# @verifies REQ-AIDS-006
def test_TEST_AIDS_006():
    df = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [2, 4, 5, 4, 5]})

    result = correlation(df, "a", "b")
    reference_r, reference_p = scipy_stats.pearsonr(df["a"], df["b"])

    assert abs(result.statistic - reference_r) < 1e-6
    assert abs(result.p_value - reference_p) < 1e-6
    assert isinstance(result.interpretation, str)
    assert len(result.interpretation) > 0

    ja_result = correlation(df, "a", "b", language="ja")
    assert isinstance(ja_result.interpretation, str)
    assert len(ja_result.interpretation) > 0
