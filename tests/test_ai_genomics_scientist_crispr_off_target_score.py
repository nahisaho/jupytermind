"""Tests for ai_genomics_scientist.crispr_off_target_score (DES-AGENOM-101)."""

from __future__ import annotations


# @id TEST-AGENOM-105
# @verifies REQ-AGENOM-101
def test_TEST_AGENOM_105_identical_guide_candidate_yields_zero_mismatches():
    from ai_genomics_scientist.crispr_off_target_score import run_crispr_off_target_score

    guide = "A" * 20
    candidate = "A" * 20

    result = run_crispr_off_target_score(guide, candidate)

    assert result == {"mismatches": 0, "score": 1.0}


# @id TEST-AGENOM-106
# @verifies REQ-AGENOM-101
def test_TEST_AGENOM_106_single_mismatch_yields_half_score():
    from ai_genomics_scientist.crispr_off_target_score import run_crispr_off_target_score

    guide = "A" * 20
    candidate = "T" + "A" * 19

    result = run_crispr_off_target_score(guide, candidate)

    assert result == {"mismatches": 1, "score": 0.5}


# @id TEST-AGENOM-107
# @verifies REQ-AGENOM-101
def test_TEST_AGENOM_107_fifteen_of_twenty_mismatches_yields_low_score():
    from ai_genomics_scientist.crispr_off_target_score import run_crispr_off_target_score

    guide = "A" * 20
    candidate = "A" * 5 + "T" * 15

    result = run_crispr_off_target_score(guide, candidate)

    assert result == {"mismatches": 15, "score": 0.0625}


# @id TEST-AGENOM-108
# @verifies REQ-AGENOM-003 REQ-AGENOM-101
def test_TEST_AGENOM_108_unequal_length_is_rejected():
    from ai_genomics_scientist.validation import validate_parameters

    result = validate_parameters(
        "crispr-off-target-score", {"guide": "A" * 20, "candidate": "A" * 19}
    )

    assert result["ok"] is False
    assert result["parameter"] in ("guide", "candidate")
    assert result["constraint"] == "must be equal length"


# @id TEST-AGENOM-109
# @verifies REQ-AGENOM-003 REQ-AGENOM-101
def test_TEST_AGENOM_109_invalid_alphabet_candidate_is_rejected():
    from ai_genomics_scientist.validation import validate_parameters

    result = validate_parameters(
        "crispr-off-target-score", {"guide": "A" * 20, "candidate": "a" * 20}
    )

    assert result["ok"] is False
    assert result["parameter"] == "candidate"


# @id TEST-AGENOM-110
# @verifies REQ-AGENOM-003 REQ-AGENOM-101
def test_TEST_AGENOM_110_empty_guide_is_rejected():
    from ai_genomics_scientist.validation import validate_parameters

    result = validate_parameters("crispr-off-target-score", {"guide": "", "candidate": "A" * 20})

    assert result["ok"] is False
    assert result["parameter"] == "guide"
    assert result["constraint"] == "must be non-empty"


# @id TEST-AGENOM-111
# @verifies REQ-AGENOM-003 REQ-AGENOM-101
def test_TEST_AGENOM_111_empty_candidate_is_rejected():
    from ai_genomics_scientist.validation import validate_parameters

    result = validate_parameters("crispr-off-target-score", {"guide": "A" * 20, "candidate": ""})

    assert result["ok"] is False
    assert result["parameter"] == "candidate"
    assert result["constraint"] == "must be non-empty"
