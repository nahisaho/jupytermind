"""Tests for ai_genomics_scientist.mirna_target_prediction (DES-AGENOM-120)."""

from __future__ import annotations


# @id TEST-AGENOM-119
# @verifies REQ-AGENOM-120
def test_TEST_AGENOM_119_let7_mirna_matches_two_utr_positions():
    from ai_genomics_scientist.mirna_target_prediction import run_mirna_target_prediction

    mirna = "UGAGGUAGUAGGUUGUAUAGUU"
    utr = "AAACTACCTCAAACTACCTCGG"

    result = run_mirna_target_prediction(mirna, utr)

    assert result == {"seed": "CTACCTC", "match_positions": [3, 13]}


# @id TEST-AGENOM-120
# @verifies REQ-AGENOM-120
def test_TEST_AGENOM_120_overlapping_occurrences_are_both_detected():
    from ai_genomics_scientist.mirna_target_prediction import run_mirna_target_prediction

    mirna = "UUUUUUUUUAGUU"
    utr = "AAAAAAAAG"

    result = run_mirna_target_prediction(mirna, utr)

    assert result == {"seed": "AAAAAAA", "match_positions": [0, 1]}


# @id TEST-AGENOM-121
# @verifies REQ-AGENOM-003 REQ-AGENOM-120
def test_TEST_AGENOM_121_short_mirna_is_rejected():
    from ai_genomics_scientist.validation import validate_parameters

    result = validate_parameters(
        "mirna-target-prediction", {"mirna": "UGAGGU", "utr": "AAACTACCTCAAA"}
    )

    assert result["ok"] is False
    assert result["parameter"] == "mirna"
    assert result["constraint"] == "must be at least 8 nucleotides"


# @id TEST-AGENOM-122
# @verifies REQ-AGENOM-003 REQ-AGENOM-120
def test_TEST_AGENOM_122_lowercase_mirna_is_rejected():
    from ai_genomics_scientist.validation import validate_parameters

    result = validate_parameters(
        "mirna-target-prediction",
        {"mirna": "ugagguagua", "utr": "AAACTACCTCAAA"},
    )

    assert result["ok"] is False
    assert result["parameter"] == "mirna"
    assert result["constraint"] == "must be uppercase over {A,C,G,U}"


# @id TEST-AGENOM-123
# @verifies REQ-AGENOM-003 REQ-AGENOM-120
def test_TEST_AGENOM_123_empty_utr_is_rejected():
    from ai_genomics_scientist.validation import validate_parameters

    result = validate_parameters(
        "mirna-target-prediction", {"mirna": "UGAGGUAGUAGGUUGUAUAGUU", "utr": ""}
    )

    assert result["ok"] is False
    assert result["parameter"] == "utr"
    assert result["constraint"] == "must be non-empty"


# @id TEST-AGENOM-124
# @verifies REQ-AGENOM-003 REQ-AGENOM-120
def test_TEST_AGENOM_124_invalid_alphabet_utr_is_rejected():
    from ai_genomics_scientist.validation import validate_parameters

    result = validate_parameters(
        "mirna-target-prediction",
        {"mirna": "UGAGGUAGUAGGUUGUAUAGUU", "utr": "aaactacctcaaa"},
    )

    assert result["ok"] is False
    assert result["parameter"] == "utr"
    assert result["constraint"] == "must be uppercase over {A,C,G,T}"
