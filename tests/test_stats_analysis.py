"""Tests for statistical analysis (REQ-AIDS-006)."""

import pandas as pd
import pytest
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


# @id TEST-AIDS-386
# @verifies REQ-AIDS-106
def test_TEST_AIDS_386_fits_fixture_cox_model_exactly():
    from ai_data_scientist.stats_analysis import cox_ph_regression

    durations = [5, 6, 6, 2, 4, 4, 10, 3, 1, 9]
    events = [1, 0, 1, 1, 1, 0, 0, 1, 1, 1]
    covariate = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0]

    result = cox_ph_regression(durations, events, covariate)

    expected = {
        "coefficient": 0.22349901045801113,
        "standard_error": 0.7672385365123494,
        "p_value": 0.7708194705704785,
        "hazard_ratio": 1.2504444029086113,
        "ci_lower": 0.27795709239511945,
        "ci_upper": 5.625368977967218,
    }
    assert result.keys() == expected.keys()
    for key, expected_value in expected.items():
        assert abs(result[key] - expected_value) < 1e-6, (key, result[key])


# @id TEST-AIDS-387
# @verifies REQ-AIDS-106
def test_TEST_AIDS_387_all_identical_covariate_is_rejected():
    from ai_data_scientist.stats_analysis import cox_ph_regression

    with pytest.raises(ValueError, match="must not be all-identical"):
        cox_ph_regression([1, 2, 3, 4], [1, 0, 1, 0], [1, 1, 1, 1])


# @id TEST-AIDS-388
# @verifies REQ-AIDS-106
def test_TEST_AIDS_388_fewer_than_two_events_is_rejected():
    from ai_data_scientist.stats_analysis import cox_ph_regression

    with pytest.raises(ValueError, match="must contain at least 2 events"):
        cox_ph_regression([1, 2, 3, 4], [1, 0, 0, 0], [0, 1, 0, 1])


# @id TEST-AIDS-389
# @verifies REQ-AIDS-106
def test_TEST_AIDS_389_perfectly_separable_data_raises_fit_did_not_converge():
    from ai_data_scientist.stats_analysis import cox_ph_regression

    with pytest.raises(ValueError, match="fit did not converge"):
        cox_ph_regression([1, 2, 3, 4], [1, 1, 1, 1], [0, 0, 1, 1])


# @id TEST-AIDS-390
# @verifies REQ-AIDS-106
def test_TEST_AIDS_390_non_positive_duration_is_rejected():
    from ai_data_scientist.stats_analysis import cox_ph_regression

    with pytest.raises(ValueError, match="durations"):
        cox_ph_regression([0, 2, 3, 4], [1, 0, 1, 0], [0, 1, 0, 1])


# @id TEST-AIDS-391
# @verifies REQ-AIDS-106
def test_TEST_AIDS_391_mismatched_lengths_is_rejected():
    from ai_data_scientist.stats_analysis import cox_ph_regression

    with pytest.raises(ValueError):
        cox_ph_regression([1, 2, 3], [1, 0, 1, 0], [0, 1, 0, 1])


# @id TEST-AIDS-393
# @verifies REQ-AIDS-107
def test_TEST_AIDS_393_kaplan_meier_fixture_matches_expected_curve():
    from ai_data_scientist.stats_analysis import kaplan_meier_estimate

    durations = [5, 6, 6, 2, 4, 4, 10, 3, 1, 9]
    events = [1, 0, 1, 1, 1, 0, 0, 1, 1, 1]
    result = kaplan_meier_estimate(durations, events)

    assert result["times"] == [1, 2, 3, 4, 5, 6, 9]
    expected_prob = [
        0.9,
        0.7999999999999999,
        0.7,
        0.6,
        0.48,
        0.36,
        0.17999999999999997,
    ]
    expected_se = [
        0.09486832980505137,
        0.12649110640673517,
        0.14491376746189435,
        0.15491933384829665,
        0.16395121225535356,
        0.16099689437998485,
        0.15059880477613358,
    ]
    for actual, want in zip(result["survival_prob"], expected_prob):
        assert actual == pytest.approx(want, abs=1e-9)
    for actual, want in zip(result["survival_se"], expected_se):
        assert actual == pytest.approx(want, abs=1e-9)


# @id TEST-AIDS-394
# @verifies REQ-AIDS-107
def test_TEST_AIDS_394_zero_events_is_rejected():
    from ai_data_scientist.stats_analysis import kaplan_meier_estimate

    with pytest.raises(ValueError, match="events"):
        kaplan_meier_estimate([1, 2, 3], [0, 0, 0])


# @id TEST-AIDS-395
# @verifies REQ-AIDS-107
def test_TEST_AIDS_395_mismatched_lengths_is_rejected():
    from ai_data_scientist.stats_analysis import kaplan_meier_estimate

    with pytest.raises(ValueError, match="durations|events"):
        kaplan_meier_estimate([1, 2, 3], [1, 0])


# @id TEST-AIDS-396
# @verifies REQ-AIDS-107
def test_TEST_AIDS_396_non_positive_duration_is_rejected():
    from ai_data_scientist.stats_analysis import kaplan_meier_estimate

    with pytest.raises(ValueError, match="durations"):
        kaplan_meier_estimate([0, 2, 3], [1, 1, 1])
