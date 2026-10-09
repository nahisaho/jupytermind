"""UPGMA phylogenetic clustering module via scipy.cluster.hierarchy.linkage
(DES-AGENOM-110 / REQ-AGENOM-110)."""

from __future__ import annotations

import math

from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform

from ai_genomics_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "phylogenetic-clustering"


def _phylogenetic_clustering_validator(params: dict) -> dict:
    """DES-AGENOM-002 registered atomic validator for this module."""
    distance_matrix = params.get("distance_matrix")

    if not isinstance(distance_matrix, list) or len(distance_matrix) == 0:
        return fail("distance_matrix", "must be square")
    row_count = len(distance_matrix)
    for row in distance_matrix:
        if not isinstance(row, list) or len(row) != row_count:
            return fail("distance_matrix", "must be square")

    if row_count < 2:
        return fail("distance_matrix", "must contain at least 2 taxa")

    for row_index, row in enumerate(distance_matrix):
        for col_index, value in enumerate(row):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return fail("distance_matrix", "must be a non-negative finite zero-diagonal matrix")
            if not math.isfinite(value) or value < 0:
                return fail("distance_matrix", "must be a non-negative finite zero-diagonal matrix")
            if row_index == col_index and value != 0:
                return fail("distance_matrix", "must be a non-negative finite zero-diagonal matrix")

    for row_index in range(row_count):
        for col_index in range(row_count):
            if distance_matrix[row_index][col_index] != distance_matrix[col_index][row_index]:
                return fail("distance_matrix", "must be symmetric")

    return ok()


register_validator(_MODULE_NAME, _phylogenetic_clustering_validator)


# @id CODE-AGENOM-110
# @implements REQ-AGENOM-110
# @design DES-AGENOM-110
def run_phylogenetic_clustering(distance_matrix: list[list[float]]) -> dict:
    """Compute the UPGMA (average-linkage) merge rows for a validated distance matrix."""
    condensed = squareform(distance_matrix)
    merge_rows = linkage(condensed, method="average")
    return {"linkage_matrix": [list(row) for row in merge_rows.tolist()]}
