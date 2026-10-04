"""Tests for ai_genomics_scientist.variant_effect (DES-AGENOM-020)."""

from __future__ import annotations

import numpy as np


# @id TEST-AGENOM-020
# @verifies REQ-AGENOM-020
def test_TEST_AGENOM_020_classifies_fixture_codon_substitutions_and_rejections():
    from ai_genomics_scientist.validation import validate_parameters
    from ai_genomics_scientist.variant_effect import run_variant_effect

    assert run_variant_effect(ref_codon="TGG", position=0, alt_base="A") == {
        "ref_codon": "TGG",
        "alt_codon": "AGG",
        "ref_amino_acid": "W",
        "alt_amino_acid": "R",
        "effect": "missense",
    }
    assert run_variant_effect(ref_codon="TGG", position=2, alt_base="A") == {
        "ref_codon": "TGG",
        "alt_codon": "TGA",
        "ref_amino_acid": "W",
        "alt_amino_acid": "*",
        "effect": "nonsense",
    }
    assert run_variant_effect(ref_codon="CTT", position=2, alt_base="C") == {
        "ref_codon": "CTT",
        "alt_codon": "CTC",
        "ref_amino_acid": "L",
        "alt_amino_acid": "L",
        "effect": "synonymous",
    }
    assert run_variant_effect(ref_codon="TGA", position=2, alt_base="G") == {
        "ref_codon": "TGA",
        "alt_codon": "TGG",
        "ref_amino_acid": "*",
        "alt_amino_acid": "W",
        "effect": "readthrough",
    }
    assert validate_parameters(
        "variant-effect-annotation",
        {"ref_codon": "TGG", "position": 2, "alt_base": "G"},
    ) == {
        "ok": False,
        "parameter": "alt_base",
        "constraint": "alt_base must differ from the reference base at position",
    }
    assert validate_parameters(
        "variant-effect-annotation",
        {"ref_codon": "TAA", "position": 2, "alt_base": "G"},
    ) == {
        "ok": False,
        "parameter": "ref_codon",
        "constraint": "stop-reference codons must mutate to a non-stop codon",
    }


# @id TEST-AGENOM-066
# @verifies REQ-AGENOM-020
def test_TEST_AGENOM_066_accepts_numpy_integer_positions_within_the_documented_domain():
    from ai_genomics_scientist.validation import validate_parameters
    from ai_genomics_scientist.variant_effect import run_variant_effect

    params = {"ref_codon": "TGG", "position": np.int64(2), "alt_base": "A"}

    assert validate_parameters("variant-effect-annotation", params) == {"ok": True}
    assert run_variant_effect(**params) == {
        "ref_codon": "TGG",
        "alt_codon": "TGA",
        "ref_amino_acid": "W",
        "alt_amino_acid": "*",
        "effect": "nonsense",
    }
