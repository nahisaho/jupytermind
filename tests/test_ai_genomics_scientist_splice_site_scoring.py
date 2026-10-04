"""Tests for ai_genomics_scientist.splice_site_scoring (DES-AGENOM-030)."""

from __future__ import annotations

from types import MappingProxyType

import pytest


# @id TEST-AGENOM-030
# @verifies REQ-AGENOM-030
def test_TEST_AGENOM_030_scores_fixture_window_and_rejects_noncanonical_gt():
    from ai_genomics_scientist.splice_site_scoring import run_splice_site_scoring
    from ai_genomics_scientist.validation import validate_parameters

    assert run_splice_site_scoring("CAGGTAAGT") == {
        "window": "CAGGTAAGT",
        "score_bits": pytest.approx(11.35314, abs=1e-6),
        "canonical_site": True,
    }
    assert validate_parameters("splice-site-strength", {"window": "CAGGCAAGT"}) == {
        "ok": False,
        "parameter": "window",
        "constraint": "position 0,+1 must be the canonical GT dinucleotide",
    }


# @id TEST-AGENOM-067
# @verifies REQ-AGENOM-030
def test_TEST_AGENOM_067_validation_accepts_read_only_mapping_parameters_for_splice_windows():
    from ai_genomics_scientist.validation import validate_parameters

    assert validate_parameters(
        "splice-site-strength",
        MappingProxyType({"window": "CAGGTAAGT"}),
    ) == {"ok": True}
