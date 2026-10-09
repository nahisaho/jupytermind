"""Tests for ai_genomics_scientist.crispr_pam_scan (DES-AGENOM-100)."""

from __future__ import annotations


# @id TEST-AGENOM-101
# @verifies REQ-AGENOM-100
def test_TEST_AGENOM_101_42char_sequence_finds_single_pam_site():
    from ai_genomics_scientist.crispr_pam_scan import run_crispr_pam_scan

    sequence = "ACGTAGGCATGGCTAGGCCAGGTTAGCATGCCGTACGATCGG"

    result = run_crispr_pam_scan(sequence)

    assert result == {
        "sites": [
            {
                "pam_index": 39,
                "pam": "CGG",
                "protospacer": "AGGTTAGCATGCCGTACGAT",
            }
        ]
    }


# @id TEST-AGENOM-102
# @verifies REQ-AGENOM-100
def test_TEST_AGENOM_102_short_sequence_yields_empty_sites():
    from ai_genomics_scientist.crispr_pam_scan import run_crispr_pam_scan

    result = run_crispr_pam_scan("ACGTAGGCAT")

    assert result == {"sites": []}


# @id TEST-AGENOM-103
# @verifies REQ-AGENOM-003 REQ-AGENOM-100
def test_TEST_AGENOM_103_empty_sequence_is_rejected():
    from ai_genomics_scientist.validation import validate_parameters

    result = validate_parameters("crispr-pam-scan", {"sequence": ""})

    assert result["ok"] is False
    assert result["parameter"] == "sequence"
    assert result["constraint"] == "must be non-empty"


# @id TEST-AGENOM-104
# @verifies REQ-AGENOM-003 REQ-AGENOM-100
def test_TEST_AGENOM_104_invalid_alphabet_sequence_is_rejected():
    from ai_genomics_scientist.validation import validate_parameters

    result = validate_parameters("crispr-pam-scan", {"sequence": "acgtAGGCATGGCTAGGCCAGGTTAGCATG"})

    assert result["ok"] is False
    assert result["parameter"] == "sequence"
    assert result["constraint"] == "must be uppercase over {A,C,G,T}"
