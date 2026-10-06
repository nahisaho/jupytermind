"""Tests for ai_genomics_scientist.differential_expression (DES-AGENOM-060)."""

from __future__ import annotations

import math


def _assert_close(actual: dict, expected: dict) -> None:
    assert actual.keys() == expected.keys()
    for key, expected_value in expected.items():
        if isinstance(expected_value, float):
            assert math.isclose(actual[key], expected_value, abs_tol=1e-9), (key, actual[key])
        else:
            assert actual[key] == expected_value, (key, actual[key])


# @id TEST-AGENOM-073
# @verifies REQ-AGENOM-060
def test_TEST_AGENOM_073_computes_fixture_differential_expression_results():
    from ai_genomics_scientist.differential_expression import run_differential_expression

    counts = {"GENE_A": [10, 12, 100, 110], "GENE_B": [50, 55, 48, 52]}
    sample_groups = ["control", "control", "treatment", "treatment"]

    result = run_differential_expression(counts, sample_groups)

    from ai_genomics_scientist.differential_expression import _median_of_ratios_size_factors

    size_factors = _median_of_ratios_size_factors(list(counts.keys()), counts, len(sample_groups))
    expected_size_factors = [
        0.6359342493413829,
        0.7142788460915032,
        1.9440028115325023,
        2.1305883321868473,
    ]
    for actual, expected in zip(size_factors, expected_size_factors):
        assert math.isclose(actual, expected, abs_tol=1e-9)

    assert len(result) == 2
    _assert_close(
        result[0],
        {
            "gene_id": "GENE_B",
            "base_mean": 51.180736856269746,
            "log2_fold_change": -1.6251673847820147,
            "p_value": 0.0006799563861321073,
            "padj": 0.0013599127722642146,
        },
    )
    _assert_close(
        result[1],
        {
            "gene_id": "GENE_A",
            "base_mean": 33.898561102562525,
            "log2_fold_change": 1.6056239092809474,
            "p_value": 0.0174420473735381,
            "padj": 0.0174420473735381,
        },
    )


# @id TEST-AGENOM-074
# @verifies REQ-AGENOM-060
def test_TEST_AGENOM_074_handles_zero_variance_gene_with_p_value_one():
    from ai_genomics_scientist.differential_expression import run_differential_expression

    counts = {
        "GENE_A": [10, 12, 100, 110],
        "GENE_B": [50, 55, 48, 52],
        "GENE_C": [20, 20, 30, 30],
    }
    sample_groups = ["control", "control", "treatment", "treatment"]

    result = run_differential_expression(counts, sample_groups)

    from ai_genomics_scientist.differential_expression import _median_of_ratios_size_factors

    size_factors = _median_of_ratios_size_factors(list(counts.keys()), counts, len(sample_groups))
    expected_size_factors = [
        0.816496580927726,
        0.816496580927726,
        1.2247448713915892,
        1.2247448713915892,
    ]
    for actual, expected in zip(size_factors, expected_size_factors):
        assert math.isclose(actual, expected, abs_tol=1e-9)

    assert len(result) == 3
    by_gene = {item["gene_id"]: item for item in result}
    _assert_close(
        by_gene["GENE_A"],
        {
            "gene_id": "GENE_A",
            "base_mean": 49.60216729135935,
            "log2_fold_change": 2.583283111931442,
            "p_value": 0.00811857123396199,
            "padj": 0.02435571370188597,
        },
    )
    _assert_close(
        by_gene["GENE_B"],
        {
            "gene_id": "GENE_B",
            "base_mean": 52.56196739722236,
            "log2_fold_change": -0.642703591179965,
            "p_value": 0.019968711789402495,
            "padj": 0.029953067684103742,
        },
    )
    gene_c = by_gene["GENE_C"]
    assert gene_c.keys() == {"gene_id", "base_mean", "log2_fold_change", "p_value", "padj"}
    assert gene_c["gene_id"] == "GENE_C"
    assert math.isclose(gene_c["base_mean"], 24.494897427831777, abs_tol=1e-9)
    assert math.isclose(gene_c["log2_fold_change"], 0.0, abs_tol=1e-9)
    assert gene_c["p_value"] == 1.0
    assert gene_c["padj"] == 1.0
    assert result == sorted(result, key=lambda item: (item["padj"], item["gene_id"]))


# @id TEST-AGENOM-075
# @verifies REQ-AGENOM-060
def test_TEST_AGENOM_075_rejects_invalid_differential_expression_requests():
    from ai_genomics_scientist.validation import validate_parameters

    assert validate_parameters(
        "differential-expression",
        {
            "counts": {"GENE_A": [10, 12, 100, 110], "GENE_B": [50, 55, 48, 52]},
            "sample_groups": ["control", "treatment"],
        },
    ) == {
        "ok": False,
        "parameter": "sample_groups",
        "constraint": "each of the exactly 2 groups must have at least 2 replicate samples",
    }
    assert validate_parameters(
        "differential-expression",
        {
            "counts": {"GENE_A": [10, 12, 100, 110], "GENE_B": [50, 55, 48, 52]},
            "sample_groups": ["control", "control", "control", "control"],
        },
    ) == {
        "ok": False,
        "parameter": "sample_groups",
        "constraint": "must contain exactly 2 distinct group labels",
    }
    assert validate_parameters(
        "differential-expression",
        {
            "counts": {"GENE_A": [10, 12, 100]},
            "sample_groups": ["control", "control", "treatment", "treatment"],
        },
    ) == {
        "ok": False,
        "parameter": "counts",
        "constraint": "each gene's count list length must equal len(sample_groups)",
    }
    assert validate_parameters(
        "differential-expression",
        {
            "counts": {"GENE_A": [-1, 12, 100, 110]},
            "sample_groups": ["control", "control", "treatment", "treatment"],
        },
    ) == {
        "ok": False,
        "parameter": "counts",
        "constraint": 'must contain only non-negative integers (invalid gene(s): "GENE_A")',
    }
    assert validate_parameters(
        "differential-expression",
        {
            "counts": {"GENE_A": [0, 5, 6, 7], "GENE_B": [5, 0, 6, 7]},
            "sample_groups": ["control", "control", "treatment", "treatment"],
        },
    ) == {
        "ok": False,
        "parameter": "counts",
        "constraint": (
            "must contain at least one gene with positive counts in every sample "
            "to compute size factors"
        ),
    }
    assert validate_parameters(
        "differential-expression",
        {"counts": {}, "sample_groups": ["control", "control", "treatment", "treatment"]},
    ) == {
        "ok": False,
        "parameter": "counts",
        "constraint": "must be a non-empty dict of gene IDs to count lists",
    }
    assert validate_parameters(
        "differential-expression",
        {
            "counts": {"GENE_A": [10, 12.5, 100, 110], "GENE_B": [50, 55, 48, 52]},
            "sample_groups": ["control", "control", "treatment", "treatment"],
        },
    ) == {
        "ok": False,
        "parameter": "counts",
        "constraint": 'must contain only non-negative integers (invalid gene(s): "GENE_A")',
    }
    assert validate_parameters(
        "differential-expression",
        {
            "counts": {1: [10, 12, 100, 110], "GENE_B": [50, 55, 48, 52]},
            "sample_groups": ["control", "control", "treatment", "treatment"],
        },
    ) == {
        "ok": False,
        "parameter": "counts",
        "constraint": "must have gene-ID strings as keys",
    }
    assert validate_parameters(
        "differential-expression",
        {
            "counts": {"GENE_A": [10, 12, 100, 110], "GENE_B": [50, 55, 48, 52]},
            "sample_groups": ["control", "control", 3, 3],
        },
    ) == {
        "ok": False,
        "parameter": "sample_groups",
        "constraint": "must contain only string group labels",
    }
