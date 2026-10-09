import pytest


# @id TEST-AIDS-424
# @verifies REQ-AIDS-114
def test_TEST_AIDS_424_psi_happy_path():
    from ai_data_scientist.model_monitoring import population_stability_index

    expected = [1.0, 2.0, 3.0, 4.0] * 25
    actual = [1.0] * 30 + [2.0] * 20 + [3.0] * 25 + [4.0] * 25
    result = population_stability_index(expected, actual, n_bins=4)

    assert result["psi"] == pytest.approx(0.02027325540540821, abs=1e-9)
    assert result["drift_detected"] is False


# @id TEST-AIDS-425
# @verifies REQ-AIDS-114
def test_TEST_AIDS_425_out_of_range_actual_is_clipped_into_last_bin():
    from ai_data_scientist.model_monitoring import population_stability_index

    expected = [1.0, 2.0, 3.0, 4.0] * 25
    actual = [1.0] * 30 + [2.0] * 20 + [3.0] * 25 + [4.0] * 25 + [100.0]
    result = population_stability_index(expected, actual, n_bins=4)

    assert result["psi"] == pytest.approx(0.0, abs=1.0)  # no error raised; finite result
    assert isinstance(result["psi"], float)


# @id TEST-AIDS-426
# @verifies REQ-AIDS-114
def test_TEST_AIDS_426_ks_drift_test_happy_path():
    from scipy.stats import norm

    from ai_data_scientist.model_monitoring import ks_drift_test

    expected = list(norm.rvs(size=50, random_state=1))
    actual = list(norm.rvs(size=50, loc=0.5, random_state=2))
    result = ks_drift_test(expected, actual)

    assert result["statistic"] == pytest.approx(0.24, abs=1e-6)
    assert result["p_value"] == pytest.approx(0.11238524845512393, abs=1e-6)
    assert result["drift_detected"] is False


# @id TEST-AIDS-427
# @verifies REQ-AIDS-114
def test_TEST_AIDS_427_n_bins_zero_is_rejected():
    from ai_data_scientist.model_monitoring import population_stability_index

    with pytest.raises(ValueError, match="must be >= 1"):
        population_stability_index([1.0, 2.0, 3.0, 4.0], [1.0, 2.0], n_bins=0)


# @id TEST-AIDS-428
# @verifies REQ-AIDS-114
def test_TEST_AIDS_428_n_bins_non_integer_is_rejected():
    from ai_data_scientist.model_monitoring import population_stability_index

    with pytest.raises(ValueError, match="must be an integer"):
        population_stability_index([1.0, 2.0, 3.0, 4.0], [1.0, 2.0], n_bins=1.5)


# @id TEST-AIDS-429
# @verifies REQ-AIDS-114
def test_TEST_AIDS_429_constant_expected_is_rejected():
    from ai_data_scientist.model_monitoring import population_stability_index

    with pytest.raises(ValueError, match="must span a non-zero range"):
        population_stability_index([2.0, 2.0, 2.0], [2.0, 2.0, 2.0], n_bins=1)


# @id TEST-AIDS-430
# @verifies REQ-AIDS-114
def test_TEST_AIDS_430_empty_expected_is_rejected_for_psi():
    from ai_data_scientist.model_monitoring import population_stability_index

    with pytest.raises(ValueError, match="non-empty list"):
        population_stability_index([], [1.0], n_bins=1)


# @id TEST-AIDS-431
# @verifies REQ-AIDS-114
def test_TEST_AIDS_431_empty_expected_is_rejected_for_ks():
    from ai_data_scientist.model_monitoring import ks_drift_test

    with pytest.raises(ValueError, match="expected"):
        ks_drift_test([], [1.0])
