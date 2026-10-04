"""Tests for ai_genomics_scientist.sequence_features (DES-AGENOM-010)."""

from __future__ import annotations

import pytest

_REFERENCE_SEQUENCE = "ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG"


# @id TEST-AGENOM-010
# @verifies REQ-AGENOM-010
def test_TEST_AGENOM_010_computes_reference_sequence_and_rejects_only_invalid_batch_item():
    from ai_genomics_scientist.sequence_features import run_sequence_features

    results = run_sequence_features([_REFERENCE_SEQUENCE, "ATBX"])

    assert len(results) == 2
    assert results[0] == {
        "length": 39,
        "gc_content": pytest.approx(0.5641025641025641, abs=1e-12),
        "longest_orf": {"frame": 0, "start_index": 0, "length": 24},
        "codon_usage": {
            "ATG": 2,
            "ATT": 1,
            "CGC": 1,
            "GCC": 1,
            "GGC": 1,
            "GTA": 1,
            "TGA": 1,
        },
    }
    assert results[1] == {
        "sequence": "ATBX",
        "ok": False,
        "parameter": "sequence",
        "constraint": "must be a non-empty uppercase DNA string over {A,C,G,T} with length >= 3",
    }
