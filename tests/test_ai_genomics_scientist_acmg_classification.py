"""Tests for ai_genomics_scientist.acmg_classification (DES-AGENOM-090)."""

from __future__ import annotations


# @id TEST-AGENOM-090
# @verifies REQ-AGENOM-090
def test_TEST_AGENOM_090_pvs1_ps1_matches_p1_pathogenic():
    from ai_genomics_scientist.acmg_classification import run_acmg_classification

    result = run_acmg_classification(["PVS1", "PS1"])

    assert result == {
        "criteria": ["PVS1", "PS1"],
        "classification": "pathogenic",
        "matched_rule": "P1",
    }


# @id TEST-AGENOM-091
# @verifies REQ-AGENOM-090
def test_TEST_AGENOM_091_three_pm_matches_lp4_likely_pathogenic():
    from ai_genomics_scientist.acmg_classification import run_acmg_classification

    result = run_acmg_classification(["PM1", "PM2", "PM3"])

    assert result == {
        "criteria": ["PM1", "PM2", "PM3"],
        "classification": "likely_pathogenic",
        "matched_rule": "LP4",
    }


# @id TEST-AGENOM-092
# @verifies REQ-AGENOM-090
def test_TEST_AGENOM_092_ba1_matches_b1_benign():
    from ai_genomics_scientist.acmg_classification import run_acmg_classification

    result = run_acmg_classification(["BA1"])

    assert result == {
        "criteria": ["BA1"],
        "classification": "benign",
        "matched_rule": "B1",
    }


# @id TEST-AGENOM-093
# @verifies REQ-AGENOM-090
def test_TEST_AGENOM_093_two_bp_matches_lb2_likely_benign():
    from ai_genomics_scientist.acmg_classification import run_acmg_classification

    result = run_acmg_classification(["BP1", "BP2"])

    assert result == {
        "criteria": ["BP1", "BP2"],
        "classification": "likely_benign",
        "matched_rule": "LB2",
    }


# @id TEST-AGENOM-094
# @verifies REQ-AGENOM-090
def test_TEST_AGENOM_094_single_pm1_matches_no_rule():
    from ai_genomics_scientist.acmg_classification import run_acmg_classification

    result = run_acmg_classification(["PM1"])

    assert result == {
        "criteria": ["PM1"],
        "classification": "uncertain_significance",
        "matched_rule": None,
    }


# @id TEST-AGENOM-095
# @verifies REQ-AGENOM-090
def test_TEST_AGENOM_095_pathogenic_and_benign_side_both_match_is_conflicting():
    from ai_genomics_scientist.acmg_classification import run_acmg_classification

    result = run_acmg_classification(["PVS1", "PS1", "BA1"])

    assert result == {
        "criteria": ["PVS1", "PS1", "BA1"],
        "classification": "uncertain_significance",
        "matched_rule": "conflicting_criteria",
    }


# @id TEST-AGENOM-096
# @verifies REQ-AGENOM-090
def test_TEST_AGENOM_096_b1_benign_match_retained_over_lb2_likely_benign():
    from ai_genomics_scientist.acmg_classification import run_acmg_classification

    result = run_acmg_classification(["BA1", "BP1", "BP2"])

    assert result == {
        "criteria": ["BA1", "BP1", "BP2"],
        "classification": "benign",
        "matched_rule": "B1",
    }


# @id TEST-AGENOM-097
# @verifies REQ-AGENOM-090
def test_TEST_AGENOM_097_p1_pathogenic_match_retained_over_lp4_likely_pathogenic():
    from ai_genomics_scientist.acmg_classification import run_acmg_classification

    result = run_acmg_classification(["PVS1", "PS1", "PM1", "PM2", "PM3"])

    assert result == {
        "criteria": ["PVS1", "PS1", "PM1", "PM2", "PM3"],
        "classification": "pathogenic",
        "matched_rule": "P1",
    }


# @id TEST-AGENOM-098
# @verifies REQ-AGENOM-003 REQ-AGENOM-090
def test_TEST_AGENOM_098_invalid_code_is_rejected():
    from ai_genomics_scientist.validation import validate_parameters

    result = validate_parameters("acmg-amp-classification", {"criteria": ["PX1"]})

    assert result["ok"] is False
    assert result["parameter"] == "criteria"
    assert result["constraint"] == "each must be one of the 28 standard ACMG/AMP criterion codes"


# @id TEST-AGENOM-099
# @verifies REQ-AGENOM-003 REQ-AGENOM-090
def test_TEST_AGENOM_099_duplicate_code_is_rejected():
    from ai_genomics_scientist.validation import validate_parameters

    result = validate_parameters("acmg-amp-classification", {"criteria": ["PS1", "PS1"]})

    assert result["ok"] is False
    assert result["parameter"] == "criteria"
    assert result["constraint"] == "must not contain duplicate codes"


# @id TEST-AGENOM-100
# @verifies REQ-AGENOM-003 REQ-AGENOM-090
def test_TEST_AGENOM_100_empty_list_is_rejected():
    from ai_genomics_scientist.validation import validate_parameters

    result = validate_parameters("acmg-amp-classification", {"criteria": []})

    assert result["ok"] is False
    assert result["parameter"] == "criteria"
    assert result["constraint"] == "must be a non-empty list"
