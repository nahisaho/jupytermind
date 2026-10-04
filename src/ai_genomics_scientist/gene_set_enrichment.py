"""Gene-set enrichment heuristic module (DES-AGENOM-040 / REQ-AGENOM-040)."""

from __future__ import annotations

import csv
from pathlib import Path

from scipy.stats import hypergeom

from ai_genomics_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "gene-set-enrichment"
_REPO_DATA_PATH = Path(__file__).resolve().parent / "data" / "sample_gene_sets.csv"
_BACKGROUND_SIZE = 50
_GENE_UNIVERSE = {f"GENE{index:02d}" for index in range(1, _BACKGROUND_SIZE + 1)}


def _load_gene_sets() -> list[dict[str, object]]:
    with _REPO_DATA_PATH.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            {"pathway": row["pathway"], "genes": row["genes"].split(";")}
            for row in reader
            if row["pathway"] and row["genes"]
        ]


def _gene_set_enrichment_validator(params: dict) -> dict:
    """DES-AGENOM-002 registered atomic validator for this module."""
    query_genes = params.get("query_genes")
    if not isinstance(query_genes, list):
        return fail("query_genes", "must be a list")
    if not query_genes:
        return fail("query_genes", "must be non-empty")
    invalid_genes = [gene for gene in query_genes if not isinstance(gene, str)]
    if invalid_genes:
        listed = ", ".join(f'"{gene}"' for gene in invalid_genes)
        return fail("query_genes", f"contains invalid gene(s): {listed}")
    if len(set(query_genes)) != len(query_genes):
        return fail("query_genes", "must be deduplicated")

    invalid_genes = [gene for gene in query_genes if gene not in _GENE_UNIVERSE]
    if invalid_genes:
        listed = ", ".join(f'"{gene}"' for gene in invalid_genes)
        return fail("query_genes", f"contains invalid gene(s): {listed}")
    return ok()


register_validator(_MODULE_NAME, _gene_set_enrichment_validator)


# @id CODE-AGENOM-040
# @implements REQ-AGENOM-040
# @design DES-AGENOM-040
def run_gene_set_enrichment(query_genes: list[str]) -> list[dict]:
    """Compute hypergeometric toy-pathway enrichment for validated ``query_genes``."""
    query_gene_set = set(query_genes)
    query_size = len(query_genes)
    results = []

    for entry in _load_gene_sets():
        pathway = entry["pathway"]
        pathway_genes = set(entry["genes"])
        overlap = len(query_gene_set & pathway_genes)
        pathway_size = len(pathway_genes)
        p_value = float(hypergeom.sf(overlap - 1, _BACKGROUND_SIZE, pathway_size, query_size))
        results.append(
            {
                "pathway": pathway,
                "overlap": overlap,
                "pathway_size": pathway_size,
                "p_value": p_value,
            }
        )

    return sorted(results, key=lambda item: (item["p_value"], item["pathway"]))
