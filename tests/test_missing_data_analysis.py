"""Tests for ai_data_scientist.missing_data_analysis (DES-AIDS-110, REQ-AIDS-110).

GitHub #84 / CHANGE-040: REQ-AIDS-110's Acceptance fixtures were corrected
to the empirically-verified values this file already asserted; TEST-AIDS-415
and TEST-AIDS-416 now match the Acceptance text exactly.
"""

import pytest


# @id TEST-AIDS-415
# @verifies REQ-AIDS-110
def test_TEST_AIDS_415_mcar_inconsistent_fixture_matches_expected():
    # Note: matches REQ-AIDS-110's Acceptance fixture (corrected in
    # CHANGE-040 / GitHub #84 to empirically-verified values).
    from ai_data_scientist.missing_data_analysis import diagnose_missingness

    target_column = [1.0, None, 2.0, None, 3.0, None, 4.0, None, 5.0, None]
    probe_column = [20.1, 9.1, 19.9, 8.9, 20.0, 9.0, 20.2, 9.2, 19.8, 8.8]

    result = diagnose_missingness(target_column, probe_column)

    assert result["n_missing"] == 5
    assert result["t_statistic"] == pytest.approx(-110.0000000000002, abs=1e-6)
    assert result["p_value"] == pytest.approx(5.2124653934461314e-14, abs=1e-6)
    assert result["diagnosis"] == "MCAR_inconsistent"
    assert result["note"] == (
        "This is an MCAR-inconsistency heuristic over one probe column only; "
        "it cannot confirm MAR and cannot detect or rule out MNAR."
    )


# @id TEST-AIDS-416
# @verifies REQ-AIDS-110
def test_TEST_AIDS_416_mcar_consistent_for_unrelated_probe_column():
    from ai_data_scientist.missing_data_analysis import diagnose_missingness

    target_column = [1.0, None, 2.0, 3.0, None, 4.0]
    probe_column = [10.0, 9.95, 9.9, 10.05, 10.0, 9.95]

    result = diagnose_missingness(target_column, probe_column)

    assert result["diagnosis"] == "MCAR_consistent"
    assert result["p_value"] == pytest.approx(1.0, abs=1e-6)
    assert result["p_value"] >= 0.05


# @id TEST-AIDS-417
# @verifies REQ-AIDS-110
def test_TEST_AIDS_417_no_missing_values_is_rejected():
    from ai_data_scientist.missing_data_analysis import diagnose_missingness

    with pytest.raises(ValueError, match="at least 1 missing"):
        diagnose_missingness([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])


# @id TEST-AIDS-418
# @verifies REQ-AIDS-110
def test_TEST_AIDS_418_mismatched_lengths_is_rejected():
    from ai_data_scientist.missing_data_analysis import diagnose_missingness

    with pytest.raises(ValueError, match="must be the same length"):
        diagnose_missingness([1.0, None, 2.0], [1.0, 2.0])
