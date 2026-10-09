"""Tests for ai_data_scientist.statistical_testing (DES-AIDS-108, REQ-AIDS-108)."""

import pytest


# @id TEST-AIDS-397
# @verifies REQ-AIDS-108
def test_TEST_AIDS_397_anova_fixture_matches_expected_statistic():
    from ai_data_scientist.statistical_testing import run_statistical_test

    result = run_statistical_test("anova", groups=[[1, 2, 3], [4, 5, 6], [7, 9, 8]])

    assert result["statistic"] == pytest.approx(27.0, abs=1e-9)
    assert result["p_value"] == pytest.approx(0.0010000000000000002, abs=1e-9)


# @id TEST-AIDS-398
# @verifies REQ-AIDS-108
def test_TEST_AIDS_398_chi_square_fixture_matches_expected_statistic():
    from ai_data_scientist.statistical_testing import run_statistical_test

    result = run_statistical_test("chi_square", table=[[10, 20], [20, 10]])

    assert result["statistic"] == pytest.approx(6.666666666666667, abs=1e-9)
    assert result["p_value"] == pytest.approx(0.009823274507519235, abs=1e-9)
    assert result["dof"] == 1


# @id TEST-AIDS-399
# @verifies REQ-AIDS-108
def test_TEST_AIDS_399_mann_whitney_u_fixture_matches_expected_statistic():
    from ai_data_scientist.statistical_testing import run_statistical_test

    result = run_statistical_test("mann_whitney_u", a=[1, 2, 3], b=[7, 8, 9])

    assert result["statistic"] == pytest.approx(0.0, abs=1e-9)
    assert result["p_value"] == pytest.approx(0.1, abs=1e-9)


# @id TEST-AIDS-400
# @verifies REQ-AIDS-108
def test_TEST_AIDS_400_kruskal_wallis_fixture_matches_expected_statistic():
    from ai_data_scientist.statistical_testing import run_statistical_test

    result = run_statistical_test("kruskal_wallis", groups=[[1, 2, 3], [4, 5, 6], [10, 11, 12]])

    assert result["statistic"] == pytest.approx(7.200000000000003, abs=1e-9)
    assert result["p_value"] == pytest.approx(0.02732372244729252, abs=1e-9)


# @id TEST-AIDS-401
# @verifies REQ-AIDS-108
def test_TEST_AIDS_401_fdr_bh_fixture_matches_expected_results():
    from ai_data_scientist.statistical_testing import run_statistical_test

    result = run_statistical_test("fdr_bh", p_values=[0.01, 0.02, 0.03, 0.2, 0.5])

    assert result["rejected"] == [True, True, True, False, False]
    expected = [0.049999999999999996, 0.049999999999999996, 0.05, 0.25, 0.5]
    for actual, want in zip(result["corrected_p_values"], expected):
        assert actual == pytest.approx(want, abs=1e-9)


# @id TEST-AIDS-402
# @verifies REQ-AIDS-108
def test_TEST_AIDS_402_unknown_test_name_is_rejected():
    from ai_data_scientist.statistical_testing import run_statistical_test

    with pytest.raises(ValueError, match="test"):
        run_statistical_test("unknown")


# @id TEST-AIDS-403
# @verifies REQ-AIDS-108
def test_TEST_AIDS_403_anova_with_one_group_is_rejected():
    from ai_data_scientist.statistical_testing import run_statistical_test

    with pytest.raises(ValueError, match="groups"):
        run_statistical_test("anova", groups=[[1, 2, 3]])


# @id TEST-AIDS-404
# @verifies REQ-AIDS-108
def test_TEST_AIDS_404_anova_all_constant_groups_is_rejected():
    from ai_data_scientist.statistical_testing import run_statistical_test

    with pytest.raises(ValueError, match="variance"):
        run_statistical_test("anova", groups=[[1, 1, 1], [1, 1, 1]])


# @id TEST-AIDS-405
# @verifies REQ-AIDS-108
def test_TEST_AIDS_405_chi_square_zero_row_total_is_rejected():
    from ai_data_scientist.statistical_testing import run_statistical_test

    with pytest.raises(ValueError, match="row and column total"):
        run_statistical_test("chi_square", table=[[0, 0], [5, 5]])


# @id TEST-AIDS-406
# @verifies REQ-AIDS-108
def test_TEST_AIDS_406_fdr_bh_out_of_range_p_value_is_rejected():
    from ai_data_scientist.statistical_testing import run_statistical_test

    with pytest.raises(ValueError, match="p_values"):
        run_statistical_test("fdr_bh", p_values=[0.1, 1.5])
