"""Tests for ai_genomics_scientist.sequence_alignment (DES-AGENOM-050)."""

from __future__ import annotations

from types import MappingProxyType


# @id TEST-AGENOM-050
# @verifies REQ-AGENOM-050
def test_TEST_AGENOM_050_computes_fixture_alignment_and_rejects_invalid_sequence():
    from ai_genomics_scientist.sequence_alignment import run_sequence_alignment
    from ai_genomics_scientist.validation import validate_parameters

    assert run_sequence_alignment("GATTACA", "GCATGCA") == {
        "aligned_seq1": "GATTACA",
        "aligned_seq2": "GCATGCA",
        "score": 1,
        "identity": 0.5714285714285714,
    }
    assert validate_parameters(
        "pairwise-sequence-alignment", {"seq1": "GATTACA", "seq2": "GCXTGCA"}
    ) == {
        "ok": False,
        "parameter": "seq2",
        "constraint": "must be a non-empty uppercase DNA string over {A,C,G,T}",
    }


# @id TEST-AGENOM-069
# @verifies REQ-AGENOM-050
def test_TEST_AGENOM_069_validation_accepts_read_only_mapping_parameters_for_alignment_inputs():
    from ai_genomics_scientist.validation import validate_parameters

    assert validate_parameters(
        "pairwise-sequence-alignment",
        MappingProxyType({"seq1": "GATTACA", "seq2": "GCATGCA"}),
    ) == {"ok": True}
