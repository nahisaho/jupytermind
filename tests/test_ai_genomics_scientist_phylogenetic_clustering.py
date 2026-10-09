"""Tests for ai_genomics_scientist.phylogenetic_clustering (DES-AGENOM-110)."""

from __future__ import annotations


# @id TEST-AGENOM-112
# @verifies REQ-AGENOM-110
def test_TEST_AGENOM_112_four_taxon_matrix_upgma_linkage():
    from ai_genomics_scientist.phylogenetic_clustering import run_phylogenetic_clustering

    distance_matrix = [
        [0, 2, 7, 9],
        [2, 0, 8, 10],
        [7, 8, 0, 3],
        [9, 10, 3, 0],
    ]

    result = run_phylogenetic_clustering(distance_matrix)

    assert result == {
        "linkage_matrix": [
            [0.0, 1.0, 2.0, 2.0],
            [2.0, 3.0, 3.0, 2.0],
            [4.0, 5.0, 8.5, 4.0],
        ]
    }


# @id TEST-AGENOM-113
# @verifies REQ-AGENOM-110
def test_TEST_AGENOM_113_tied_distance_matrix_resolves_lower_index_pair_first():
    from ai_genomics_scientist.phylogenetic_clustering import run_phylogenetic_clustering

    distance_matrix = [
        [0, 2, 9, 9],
        [2, 0, 9, 9],
        [9, 9, 0, 2],
        [9, 9, 2, 0],
    ]

    result = run_phylogenetic_clustering(distance_matrix)

    assert result == {
        "linkage_matrix": [
            [0.0, 1.0, 2.0, 2.0],
            [2.0, 3.0, 2.0, 2.0],
            [4.0, 5.0, 9.0, 4.0],
        ]
    }


# @id TEST-AGENOM-114
# @verifies REQ-AGENOM-003 REQ-AGENOM-110
def test_TEST_AGENOM_114_non_symmetric_matrix_is_rejected():
    from ai_genomics_scientist.validation import validate_parameters

    result = validate_parameters(
        "phylogenetic-clustering",
        {"distance_matrix": [[0, 2, 7], [3, 0, 8], [7, 8, 0]]},
    )

    assert result["ok"] is False
    assert result["parameter"] == "distance_matrix"
    assert result["constraint"] == "must be symmetric"


# @id TEST-AGENOM-115
# @verifies REQ-AGENOM-003 REQ-AGENOM-110
def test_TEST_AGENOM_115_non_zero_diagonal_matrix_is_rejected():
    from ai_genomics_scientist.validation import validate_parameters

    result = validate_parameters(
        "phylogenetic-clustering",
        {"distance_matrix": [[1, 2, 7], [2, 0, 8], [7, 8, 0]]},
    )

    assert result["ok"] is False
    assert result["parameter"] == "distance_matrix"
    assert result["constraint"] == "must be a non-negative finite zero-diagonal matrix"


# @id TEST-AGENOM-116
# @verifies REQ-AGENOM-003 REQ-AGENOM-110
def test_TEST_AGENOM_116_negative_value_matrix_is_rejected():
    from ai_genomics_scientist.validation import validate_parameters

    result = validate_parameters(
        "phylogenetic-clustering",
        {"distance_matrix": [[0, -2, 7], [-2, 0, 8], [7, 8, 0]]},
    )

    assert result["ok"] is False
    assert result["parameter"] == "distance_matrix"
    assert result["constraint"] == "must be a non-negative finite zero-diagonal matrix"


# @id TEST-AGENOM-117
# @verifies REQ-AGENOM-003 REQ-AGENOM-110
def test_TEST_AGENOM_117_ragged_matrix_is_rejected():
    from ai_genomics_scientist.validation import validate_parameters

    result = validate_parameters(
        "phylogenetic-clustering",
        {"distance_matrix": [[0, 2, 7], [2, 0], [7, 8, 0]]},
    )

    assert result["ok"] is False
    assert result["parameter"] == "distance_matrix"
    assert result["constraint"] == "must be square"


# @id TEST-AGENOM-118
# @verifies REQ-AGENOM-003 REQ-AGENOM-110
def test_TEST_AGENOM_118_fewer_than_two_taxa_is_rejected():
    from ai_genomics_scientist.validation import validate_parameters

    result = validate_parameters("phylogenetic-clustering", {"distance_matrix": [[0]]})

    assert result["ok"] is False
    assert result["parameter"] == "distance_matrix"
    assert result["constraint"] == "must contain at least 2 taxa"
