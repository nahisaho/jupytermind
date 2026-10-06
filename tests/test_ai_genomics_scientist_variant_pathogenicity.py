"""Tests for ai_genomics_scientist.variant_pathogenicity (DES-AGENOM-070)."""

from __future__ import annotations

import math


def _assert_close(actual: dict, expected: dict) -> None:
    assert actual.keys() == expected.keys()
    for key, expected_value in expected.items():
        if isinstance(expected_value, float):
            assert math.isclose(actual[key], expected_value, abs_tol=1e-9), (key, actual[key])
        else:
            assert actual[key] == expected_value, (key, actual[key])


# @id TEST-AGENOM-076
# @verifies REQ-AGENOM-070
def test_TEST_AGENOM_076_computes_fixture_pathogenicity_scores():
    from ai_genomics_scientist.variant_pathogenicity import run_variant_pathogenicity

    _assert_close(
        run_variant_pathogenicity("D", "G", 0.9, True),
        {
            "ref_aa": "D",
            "alt_aa": "G",
            "blosum_score": -1,
            "pathogenicity_score": 0.7507142857142858,
            "classification": "likely_pathogenic",
        },
    )
    _assert_close(
        run_variant_pathogenicity("L", "I", 0.1, False),
        {
            "ref_aa": "L",
            "alt_aa": "I",
            "blosum_score": 2,
            "pathogenicity_score": 0.10642857142857143,
            "classification": "benign",
        },
    )
    _assert_close(
        run_variant_pathogenicity("W", "D", 0.5, False),
        {
            "ref_aa": "W",
            "alt_aa": "D",
            "blosum_score": -4,
            "pathogenicity_score": 0.675,
            "classification": "uncertain_significance",
        },
    )


# @id TEST-AGENOM-077
# @verifies REQ-AGENOM-070
def test_TEST_AGENOM_077_exercises_all_tiers_and_boundaries():
    from ai_genomics_scientist.variant_pathogenicity import run_variant_pathogenicity

    _assert_close(
        run_variant_pathogenicity("F", "Y", 6 / 7, False),
        {
            "ref_aa": "F",
            "alt_aa": "Y",
            "blosum_score": 3,
            "pathogenicity_score": 0.3,
            "classification": "likely_benign",
        },
    )
    _assert_close(
        run_variant_pathogenicity("F", "Y", 0.8, False),
        {
            "ref_aa": "F",
            "alt_aa": "Y",
            "blosum_score": 3,
            "pathogenicity_score": 0.27999999999999997,
            "classification": "benign",
        },
    )
    _assert_close(
        run_variant_pathogenicity("F", "Y", 1.0, True),
        {
            "ref_aa": "F",
            "alt_aa": "Y",
            "blosum_score": 3,
            "pathogenicity_score": 0.5,
            "classification": "uncertain_significance",
        },
    )
    _assert_close(
        run_variant_pathogenicity("F", "Y", 0.99, True),
        {
            "ref_aa": "F",
            "alt_aa": "Y",
            "blosum_score": 3,
            "pathogenicity_score": 0.49649999999999994,
            "classification": "likely_benign",
        },
    )
    _assert_close(
        run_variant_pathogenicity("W", "D", 4 / 7, False),
        {
            "ref_aa": "W",
            "alt_aa": "D",
            "blosum_score": -4,
            "pathogenicity_score": 0.7,
            "classification": "likely_pathogenic",
        },
    )
    _assert_close(
        run_variant_pathogenicity("W", "D", 0.57, False),
        {
            "ref_aa": "W",
            "alt_aa": "D",
            "blosum_score": -4,
            "pathogenicity_score": 0.6995,
            "classification": "uncertain_significance",
        },
    )
    _assert_close(
        run_variant_pathogenicity("W", "D", 1.0, False),
        {
            "ref_aa": "W",
            "alt_aa": "D",
            "blosum_score": -4,
            "pathogenicity_score": 0.85,
            "classification": "pathogenic",
        },
    )
    _assert_close(
        run_variant_pathogenicity("W", "D", 0.99, False),
        {
            "ref_aa": "W",
            "alt_aa": "D",
            "blosum_score": -4,
            "pathogenicity_score": 0.8465,
            "classification": "likely_pathogenic",
        },
    )


# @id TEST-AGENOM-078
# @verifies REQ-AGENOM-070
def test_TEST_AGENOM_078_rejects_invalid_variant_pathogenicity_requests():
    from ai_genomics_scientist.validation import validate_parameters

    assert validate_parameters(
        "variant-pathogenicity",
        {
            "ref_aa": "Z",
            "alt_aa": "G",
            "conservation_score": 0.5,
            "in_functional_domain": False,
        },
    ) == {
        "ok": False,
        "parameter": "ref_aa",
        "constraint": "must be one of the 20 standard single-letter amino acid codes",
    }
    assert validate_parameters(
        "variant-pathogenicity",
        {
            "ref_aa": "D",
            "alt_aa": "D",
            "conservation_score": 0.5,
            "in_functional_domain": False,
        },
    ) == {
        "ok": False,
        "parameter": "alt_aa",
        "constraint": "alt_aa must differ from ref_aa",
    }
    assert validate_parameters(
        "variant-pathogenicity",
        {
            "ref_aa": "D",
            "alt_aa": "G",
            "conservation_score": 1.5,
            "in_functional_domain": False,
        },
    ) == {
        "ok": False,
        "parameter": "conservation_score",
        "constraint": "must be a float in the closed interval [0, 1]",
    }
    assert validate_parameters(
        "variant-pathogenicity",
        {
            "ref_aa": "D",
            "alt_aa": "G",
            "conservation_score": 1,
            "in_functional_domain": False,
        },
    ) == {
        "ok": False,
        "parameter": "conservation_score",
        "constraint": "must be a float in the closed interval [0, 1]",
    }
    assert validate_parameters(
        "variant-pathogenicity",
        {
            "ref_aa": "D",
            "alt_aa": "G",
            "conservation_score": 0.5,
            "in_functional_domain": "yes",
        },
    ) == {
        "ok": False,
        "parameter": "in_functional_domain",
        "constraint": "must be a boolean",
    }
    assert validate_parameters(
        "variant-pathogenicity",
        {
            "ref_aa": "D",
            "alt_aa": "Z",
            "conservation_score": 0.5,
            "in_functional_domain": False,
        },
    ) == {
        "ok": False,
        "parameter": "alt_aa",
        "constraint": "must be one of the 20 standard single-letter amino acid codes",
    }
