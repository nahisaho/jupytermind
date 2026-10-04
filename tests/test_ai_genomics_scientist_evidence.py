"""Tests for ai_genomics_scientist.evidence (DES-AGENOM-003 / REQ-AGENOM-004)."""

from __future__ import annotations

import json

import numpy
import pytest
import scipy


def _assert_json_safe_equal(lhs, rhs):
    if isinstance(lhs, float) or isinstance(rhs, float):
        assert lhs == pytest.approx(rhs, abs=1e-9)
        return
    assert type(lhs) is type(rhs)
    if isinstance(lhs, dict):
        assert lhs.keys() == rhs.keys()
        for key in lhs:
            _assert_json_safe_equal(lhs[key], rhs[key])
        return
    if isinstance(lhs, list):
        assert len(lhs) == len(rhs)
        for left_item, right_item in zip(lhs, rhs, strict=True):
            _assert_json_safe_equal(left_item, right_item)
        return
    assert lhs == rhs


# @id TEST-AGENOM-004
# @verifies REQ-AGENOM-004
def test_TEST_AGENOM_004_record_run_wraps_all_module_results_with_numpy_and_scipy_versions():
    from ai_genomics_scientist.evidence import record_run
    from ai_genomics_scientist.gene_set_enrichment import run_gene_set_enrichment
    from ai_genomics_scientist.sequence_alignment import run_sequence_alignment
    from ai_genomics_scientist.sequence_features import run_sequence_features
    from ai_genomics_scientist.splice_site_scoring import run_splice_site_scoring
    from ai_genomics_scientist.variant_effect import run_variant_effect

    cases = [
        (
            "sequence-features",
            {"sequences": ["ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG"]},
            run_sequence_features(["ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG"]),
        ),
        (
            "variant-effect-annotation",
            {"ref_codon": "TGG", "position": 0, "alt_base": "A"},
            run_variant_effect("TGG", 0, "A"),
        ),
        (
            "splice-site-strength",
            {"window": "CAGGTAAGT"},
            run_splice_site_scoring("CAGGTAAGT"),
        ),
        (
            "gene-set-enrichment",
            {
                "query_genes": [
                    "GENE01",
                    "GENE02",
                    "GENE03",
                    "GENE04",
                    "GENE05",
                    "GENE06",
                    "GENE09",
                    "GENE14",
                ]
            },
            run_gene_set_enrichment(
                ["GENE01", "GENE02", "GENE03", "GENE04", "GENE05", "GENE06", "GENE09", "GENE14"]
            ),
        ),
        (
            "pairwise-sequence-alignment",
            {"seq1": "GATTACA", "seq2": "GCATGCA"},
            run_sequence_alignment("GATTACA", "GCATGCA"),
        ),
    ]

    for module_name, params, result in cases:
        record_a = record_run(
            module_name=module_name,
            params=params,
            result=result,
            numpy_version=numpy.__version__,
            scipy_version=scipy.__version__,
        )
        record_b = record_run(
            module_name=module_name,
            params=params,
            result=result,
            numpy_version=numpy.__version__,
            scipy_version=scipy.__version__,
        )

        assert set(record_a.keys()) == {"metadata", "parameters", "result"}
        assert record_a["metadata"]["module"] == module_name
        assert record_a["metadata"]["numpy_version"] == numpy.__version__
        assert record_a["metadata"]["scipy_version"] == scipy.__version__
        assert "schema_version" in record_a["metadata"]
        assert record_a["parameters"] == params
        _assert_json_safe_equal(record_a["result"], record_b["result"])


# @id TEST-AGENOM-070
# @verifies REQ-AGENOM-004
def test_TEST_AGENOM_070_record_run_normalizes_numpy_scalars_to_json_safe_values():
    from ai_genomics_scientist.evidence import record_run

    record = record_run(
        module_name="variant-effect-annotation",
        params={
            "ref_codon": "TGG",
            "position": numpy.int64(2),
            "alt_base": "A",
        },
        result={
            "effect": "nonsense",
            "support": {"position": numpy.int64(2), "score": numpy.float64(1.25)},
        },
        numpy_version=numpy.__version__,
        scipy_version=scipy.__version__,
    )

    assert json.loads(json.dumps(record)) == {
        "metadata": {
            "module": "variant-effect-annotation",
            "schema_version": 1,
            "numpy_version": numpy.__version__,
            "scipy_version": scipy.__version__,
        },
        "parameters": {"ref_codon": "TGG", "position": 2, "alt_base": "A"},
        "result": {
            "effect": "nonsense",
            "support": {"position": 2, "score": 1.25},
        },
    }
