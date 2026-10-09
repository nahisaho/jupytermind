"""Tests for ai_data_scientist.statistical_simulation (DES-AIDS-109, REQ-AIDS-109)."""

import pytest


# @id TEST-AIDS-407
# @verifies REQ-AIDS-109
def test_TEST_AIDS_407_bootstrap_confidence_interval_fixture_matches_expected():
    from ai_data_scientist.statistical_simulation import bootstrap_confidence_interval

    data = [2.1, 3.4, 2.9, 4.1, 3.3, 2.7, 3.8, 3.0, 2.5, 3.6]
    result = bootstrap_confidence_interval(data)

    assert result["low"] == pytest.approx(2.79, abs=1e-6)
    assert result["high"] == pytest.approx(3.5, abs=1e-6)


# @id TEST-AIDS-408
# @verifies REQ-AIDS-109
def test_TEST_AIDS_408_power_analysis_computes_power_from_nobs1():
    from ai_data_scientist.statistical_simulation import power_analysis

    result = power_analysis(effect_size=0.5, nobs1=30, alpha=0.05)

    assert result["power"] == pytest.approx(0.4778965207601643, abs=1e-9)
    assert result["nobs1"] == 30


# @id TEST-AIDS-409
# @verifies REQ-AIDS-109
def test_TEST_AIDS_409_power_analysis_computes_nobs1_from_power():
    from ai_data_scientist.statistical_simulation import power_analysis

    result = power_analysis(effect_size=0.5, power=0.8, alpha=0.05)

    assert result["nobs1"] == pytest.approx(63.76561058891169, abs=1e-6)
    assert result["power"] == pytest.approx(0.8, abs=1e-9)


# @id TEST-AIDS-410
# @verifies REQ-AIDS-109
def test_TEST_AIDS_410_power_analysis_both_supplied_is_rejected():
    from ai_data_scientist.statistical_simulation import power_analysis

    with pytest.raises(ValueError, match="nobs1|power"):
        power_analysis(effect_size=0.5, nobs1=30, power=0.8)


# @id TEST-AIDS-411
# @verifies REQ-AIDS-109
def test_TEST_AIDS_411_power_analysis_neither_supplied_is_rejected():
    from ai_data_scientist.statistical_simulation import power_analysis

    with pytest.raises(ValueError, match="nobs1|power"):
        power_analysis(effect_size=0.5)


# @id TEST-AIDS-412
# @verifies REQ-AIDS-109
def test_TEST_AIDS_412_bootstrap_unsupported_statistic_is_rejected():
    from ai_data_scientist.statistical_simulation import bootstrap_confidence_interval

    with pytest.raises(ValueError, match="statistic"):
        bootstrap_confidence_interval([1.0, 2.0, 3.0], statistic="median")


# @id TEST-AIDS-413
# @verifies REQ-AIDS-109
def test_TEST_AIDS_413_bootstrap_confidence_level_out_of_range_is_rejected():
    from ai_data_scientist.statistical_simulation import bootstrap_confidence_interval

    with pytest.raises(ValueError, match="confidence_level"):
        bootstrap_confidence_interval([1.0, 2.0, 3.0], confidence_level=1.5)


# @id TEST-AIDS-414
# @verifies REQ-AIDS-109
def test_TEST_AIDS_414_power_analysis_alpha_out_of_range_is_rejected():
    from ai_data_scientist.statistical_simulation import power_analysis

    with pytest.raises(ValueError, match="alpha"):
        power_analysis(effect_size=0.5, nobs1=30, alpha=-0.1)
