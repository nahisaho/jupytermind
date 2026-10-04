"""Tests for ai_genomics_scientist.gene_set_enrichment (DES-AGENOM-040)."""

from __future__ import annotations

import pytest

_QUERY_GENES = ["GENE01", "GENE02", "GENE03", "GENE04", "GENE05", "GENE06", "GENE09", "GENE14"]


# @id TEST-AGENOM-040
# @verifies REQ-AGENOM-040
def test_TEST_AGENOM_040_scores_fixed_toy_pathways_and_rejects_invalid_queries():
    from ai_genomics_scientist.gene_set_enrichment import run_gene_set_enrichment
    from ai_genomics_scientist.validation import validate_parameters

    results = run_gene_set_enrichment(_QUERY_GENES)

    assert results == [
        {
            "pathway": "cell_cycle",
            "overlap": 6,
            "pathway_size": 8,
            "p_value": pytest.approx(4.553170441774879e-05, abs=1e-9),
        },
        {
            "pathway": "dna_repair",
            "overlap": 3,
            "pathway_size": 8,
            "p_value": pytest.approx(0.104567080475262, abs=1e-9),
        },
        {
            "pathway": "apoptosis",
            "overlap": 1,
            "pathway_size": 6,
            "p_value": pytest.approx(0.6698832650544029, abs=1e-9),
        },
        {
            "pathway": "immune_response",
            "overlap": 0,
            "pathway_size": 9,
            "p_value": pytest.approx(1.0, abs=1e-9),
        },
        {
            "pathway": "metabolism",
            "overlap": 0,
            "pathway_size": 10,
            "p_value": pytest.approx(1.0, abs=1e-9),
        },
    ]
    assert validate_parameters("gene-set-enrichment", {"query_genes": ["GENE01", "GENE01"]}) == {
        "ok": False,
        "parameter": "query_genes",
        "constraint": "must be deduplicated",
    }
    assert validate_parameters("gene-set-enrichment", {"query_genes": []}) == {
        "ok": False,
        "parameter": "query_genes",
        "constraint": "must be non-empty",
    }
    invalid = validate_parameters("gene-set-enrichment", {"query_genes": ["GENE01", "BADGENE"]})
    assert invalid["ok"] is False
    assert invalid["parameter"] == "query_genes"
    assert '"BADGENE"' in invalid["constraint"]


# @id TEST-AGENOM-071
# @verifies REQ-AGENOM-003 REQ-AGENOM-040
def test_TEST_AGENOM_071_validation_rejects_unhashable_non_string_gene_entries_without_crashing():
    from ai_genomics_scientist.validation import validate_parameters

    invalid = validate_parameters("gene-set-enrichment", {"query_genes": [["GENE01"]]})

    assert invalid == {
        "ok": False,
        "parameter": "query_genes",
        "constraint": "contains invalid gene(s): \"['GENE01']\"",
    }
