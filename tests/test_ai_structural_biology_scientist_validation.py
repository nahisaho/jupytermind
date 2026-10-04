"""Tests for ai_structural_biology_scientist.validation."""

from __future__ import annotations

from types import MappingProxyType

import numpy as np


# @id TEST-ASTRUCT-003
# @verifies REQ-ASTRUCT-003
def test_TEST_ASTRUCT_003_validate_parameters_enforces_module_domains_before_computation():
    import ai_structural_biology_scientist.contact_map
    import ai_structural_biology_scientist.hydrophobicity
    import ai_structural_biology_scientist.protein_docking_score
    import ai_structural_biology_scientist.secondary_structure
    import ai_structural_biology_scientist.structural_similarity  # noqa: F401
    from ai_structural_biology_scientist.validation import fail, ok, validate_parameters

    assert ok() == {"ok": True}
    assert fail("sequence", "must be uppercase") == {
        "ok": False,
        "parameter": "sequence",
        "constraint": "must be uppercase",
    }

    invalid_sequence = validate_parameters("secondary-structure-heuristic", {"sequence": "MKXB"})
    assert invalid_sequence == {
        "ok": False,
        "parameter": "sequence",
        "constraint": (
            "must contain only uppercase residues from ACDEFGHIKLMNPQRSTVWY; "
            "first invalid character 'X' at index 2"
        ),
    }

    bad_window = validate_parameters(
        "hydrophobicity-burial-heuristic",
        {"sequence": "LLLKKKLLL", "window_size": 4, "burial_threshold": 1.5},
    )
    assert bad_window == {
        "ok": False,
        "parameter": "window_size",
        "constraint": "must be a positive odd integer",
    }

    bad_threshold = validate_parameters(
        "hydrophobicity-burial-heuristic",
        {"sequence": "LLLKKKLLL", "window_size": 3, "burial_threshold": float("nan")},
    )
    assert bad_threshold == {
        "ok": False,
        "parameter": "burial_threshold",
        "constraint": "must be a finite number",
    }

    bad_interface_area = validate_parameters(
        "protein-protein-docking-score",
        {
            "partner_a": {"hydrophobic_count": 6, "charged_count": 2},
            "partner_b": {"hydrophobic_count": 4, "charged_count": 3},
            "interface_area_A2": -10.0,
        },
    )
    assert bad_interface_area == {
        "ok": False,
        "parameter": "interface_area_A2",
        "constraint": "must be > 0",
    }

    bad_coordinate_type = validate_parameters(
        "structural-similarity-rmsd",
        {
            "structure_a": [np.array([0.0, 0.0, 0.0]), [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            "structure_b": [[5.0, 5.0, 5.0], [5.0, 6.0, 5.0], [4.0, 5.0, 5.0]],
        },
    )
    assert bad_coordinate_type == {
        "ok": False,
        "parameter": "structure_a[0]",
        "constraint": "must be a list/tuple of exactly 3 finite real numbers",
    }

    too_few_coordinates = validate_parameters(
        "residue-contact-map",
        {
            "coordinates": [[0.0, 0.0, 0.0]],
            "distance_threshold_A": 8.0,
            "min_sequence_separation": 3,
        },
    )
    assert too_few_coordinates == {
        "ok": False,
        "parameter": "coordinates",
        "constraint": "must contain at least 2 coordinates",
    }


# @id TEST-ASTRUCT-061
# @verifies REQ-ASTRUCT-050
def test_TEST_ASTRUCT_061_contact_map_invalid_coordinate_uses_documented_constraint_name():
    import ai_structural_biology_scientist.contact_map  # noqa: F401
    from ai_structural_biology_scientist.validation import validate_parameters

    invalid_coordinate = validate_parameters(
        "residue-contact-map",
        {
            "coordinates": [[0.0, 0.0, 0.0], [1.0, 2.0]],
            "distance_threshold_A": 8.0,
            "min_sequence_separation": 3,
        },
    )

    assert invalid_coordinate == {
        "ok": False,
        "parameter": "coordinates[1]",
        "constraint": "must be a finite numeric 3-element sequence",
    }


# @id TEST-ASTRUCT-075
# @verifies REQ-ASTRUCT-003
def test_TEST_ASTRUCT_075_validate_parameters_accepts_mapping_inputs_and_numpy_integral_sequence_separation():
    from ai_structural_biology_scientist.validation import validate_parameters

    valid = validate_parameters(
        "residue-contact-map",
        MappingProxyType(
            {
                "coordinates": [
                    [0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [2.0, 0.0, 0.0],
                    [0.0, 0.0, 7.5],
                    [2.0, 0.0, 7.0],
                ],
                "distance_threshold_A": 8.0,
                "min_sequence_separation": np.int64(3),
            }
        ),
    )

    assert valid == {"ok": True}
