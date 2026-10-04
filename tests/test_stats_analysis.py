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


# @id TEST-AIDS-119
# @verifies REQ-AIDS-063
def test_TEST_AIDS_119_non_significant_pvalue_states_no_clear_correlation(monkeypatch):
    import ai_data_scientist.stats_analysis as stats_analysis

    monkeypatch.setattr(
        stats_analysis.scipy_stats, "pearsonr", lambda a, b: (0.01, 0.85), raising=False
    )
    df = pd.DataFrame({"a": [1, 2, 3], "b": [3, 1, 2]})

    en_result = correlation(df, "a", "b", language="en")
    assert "no statistically clear correlation" in en_result.interpretation
    assert "weak" not in en_result.interpretation

    ja_result = correlation(df, "a", "b", language="ja")
    assert "統計的に明確な相関は見られません" in ja_result.interpretation


# @id TEST-AIDS-120
# @verifies REQ-AIDS-063
def test_TEST_AIDS_120_non_significant_applies_regardless_of_magnitude(monkeypatch):
    import ai_data_scientist.stats_analysis as stats_analysis

    monkeypatch.setattr(
        stats_analysis.scipy_stats, "pearsonr", lambda a, b: (0.9, 0.2), raising=False
    )
    df = pd.DataFrame({"a": [1, 2, 3], "b": [3, 1, 2]})

    result = correlation(df, "a", "b", language="en")
    assert "no statistically clear correlation" in result.interpretation


# @id TEST-AIDS-121
# @verifies REQ-AIDS-063
def test_TEST_AIDS_121_pvalue_equal_to_threshold_is_non_significant(monkeypatch):
    import ai_data_scientist.stats_analysis as stats_analysis

    monkeypatch.setattr(
        stats_analysis.scipy_stats, "pearsonr", lambda a, b: (0.5, 0.05), raising=False
    )
    df = pd.DataFrame({"a": [1, 2, 3], "b": [3, 1, 2]})

    result = correlation(df, "a", "b", language="en")
    assert "no statistically clear correlation" in result.interpretation


# @id TEST-AIDS-123
# @verifies REQ-AIDS-063
def test_TEST_AIDS_123_custom_significance_threshold_applied(monkeypatch):
    import ai_data_scientist.stats_analysis as stats_analysis

    monkeypatch.setattr(
        stats_analysis.scipy_stats, "pearsonr", lambda a, b: (0.5, 0.08), raising=False
    )
    df = pd.DataFrame({"a": [1, 2, 3], "b": [3, 1, 2]})

    # 0.08 is non-significant at the default 0.05 threshold...
    default_result = correlation(df, "a", "b", language="en")
    assert "no statistically clear correlation" in default_result.interpretation

    # ...but significant once the threshold is raised to 0.10.
    widened_result = correlation(df, "a", "b", language="en", significance_threshold=0.10)
    assert "no statistically clear correlation" not in widened_result.interpretation
    # The existing magnitude/direction wording is unchanged for the
    # significant case (REQ-AIDS-063 unchanged-path acceptance clause).
    assert "moderate positive correlation" in widened_result.interpretation


# @id TEST-AIDS-124
# @verifies REQ-AIDS-065
def test_TEST_AIDS_124_near_zero_pvalue_displays_bounded():
    from ai_data_scientist.stats_analysis import p_display

    assert p_display(0.0) == "p < 1e-4"
    assert p_display(1e-10) == "p < 1e-4"
    assert "p < 1e-4" not in f"{0.05:.4g}"


# @id TEST-AIDS-125
# @verifies REQ-AIDS-065
def test_TEST_AIDS_125_pvalue_at_or_above_bound_displays_numeric():
    from ai_data_scientist.stats_analysis import p_display

    assert p_display(1e-4) == "p=0.0001"
    assert p_display(0.05) == "p=0.05"


# @id TEST-AIDS-126
# @verifies REQ-AIDS-065
def test_TEST_AIDS_126_interpretation_uses_bounded_pvalue_display(monkeypatch):
    import ai_data_scientist.stats_analysis as stats_analysis

    monkeypatch.setattr(
        stats_analysis.scipy_stats, "pearsonr", lambda a, b: (0.9, 1e-10), raising=False
    )
    df = pd.DataFrame({"a": [1, 2, 3], "b": [3, 1, 2]})

    en_result = correlation(df, "a", "b", language="en")
    assert "p < 1e-4" in en_result.interpretation

    ja_result = correlation(df, "a", "b", language="ja")
    assert "p < 1e-4" in ja_result.interpretation


# @id TEST-AIDS-131
# @verifies REQ-AIDS-067
def test_TEST_AIDS_131_nan_statistic_states_could_not_be_computed(monkeypatch):
    """GitHub #47: a NaN coefficient/p-value (e.g. from a column with missing
    values) must not be silently described as a magnitude/direction/
    significance claim."""
    import math

    import ai_data_scientist.stats_analysis as stats_analysis

    monkeypatch.setattr(
        stats_analysis.scipy_stats, "pearsonr", lambda a, b: (math.nan, math.nan), raising=False
    )
    df = pd.DataFrame({"a": [1, 2, 3], "b": [3, 1, 2]})

    en_result = correlation(df, "a", "b", language="en")
    assert "could not be computed" in en_result.interpretation
    assert "strong" not in en_result.interpretation
    assert "weak" not in en_result.interpretation
    assert "no statistically clear correlation" not in en_result.interpretation
    assert math.isnan(en_result.statistic)
    assert math.isnan(en_result.p_value)

    ja_result = correlation(df, "a", "b", language="ja")
    assert "算出できません" in ja_result.interpretation or "算出不能" in ja_result.interpretation


# @id TEST-AIDS-132
# @verifies REQ-AIDS-067
def test_TEST_AIDS_132_nan_coefficient_only_also_states_could_not_be_computed(monkeypatch):
    import math

    import ai_data_scientist.stats_analysis as stats_analysis

    monkeypatch.setattr(
        stats_analysis.scipy_stats, "pearsonr", lambda a, b: (math.nan, 0.5), raising=False
    )
    df = pd.DataFrame({"a": [1, 2, 3], "b": [3, 1, 2]})

    result = correlation(df, "a", "b", language="en")
    assert "could not be computed" in result.interpretation
