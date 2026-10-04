"""Tests for ai_structural_biology_scientist.dispatch."""

from __future__ import annotations


# @id TEST-ASTRUCT-002
# @verifies REQ-ASTRUCT-002
def test_TEST_ASTRUCT_002_dispatches_registered_english_and_japanese_requests_and_handles_ambiguous_or_unknown_input():
    from ai_structural_biology_scientist.dispatch import dispatch

    routed_cases = [
        (
            'I want to evaluate secondary structure {"sequence": "MKVLAGPIW"}',
            "secondary-structure-heuristic",
        ),
        (
            '残基ごとの疎水性・埋没度を評価したい {"sequence": "LLLKKKLLL", "window_size": 3, "burial_threshold": 1.5}',
            "hydrophobicity-burial-heuristic",
        ),
        (
            'Compute the protein docking score {"partner_a": {"hydrophobic_count": 6, "charged_count": 2}, "partner_b": {"hydrophobic_count": 4, "charged_count": 3}, "interface_area_A2": 750.0}',
            "protein-protein-docking-score",
        ),
        (
            '構造類似性RMSDを計算したい {"structure_a": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], "structure_b": [[5.0, 5.0, 5.0], [5.0, 6.0, 5.0], [4.0, 5.0, 5.0]]}',
            "structural-similarity-rmsd",
        ),
        (
            'Run a residue contact map {"coordinates": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [0.0, 0.0, 7.5], [2.0, 0.0, 7.0]], "distance_threshold_A": 8.0, "min_sequence_separation": 3}',
            "residue-contact-map",
        ),
    ]

    for request_text, expected_module in routed_cases:
        result = dispatch(request_text)
        assert result["outcome"] == "dispatch"
        assert result["module"] == expected_module
        assert result["handler_result"]["ok"] is True

    ambiguous = dispatch("Should I use secondary structure or residue contact map?")
    assert ambiguous["outcome"] == "clarification"
    assert set(ambiguous["candidates"]) == {
        "secondary-structure-heuristic",
        "residue-contact-map",
    }

    rejected = dispatch("What is the weather today?")
    assert rejected["outcome"] == "rejected"


# @id TEST-ASTRUCT-062
# @verifies REQ-ASTRUCT-002
def test_TEST_ASTRUCT_062_handler_accepts_already_structured_parameters_from_calling_context():
    from ai_structural_biology_scientist.dispatch import handle_secondary_structure

    result = handle_secondary_structure({"sequence": "MKVLAGPIW"}, "en")

    assert result["ok"] is True
    assert result["run_record"]["parameters"] == {"sequence": "MKVLAGPIW"}
    assert result["run_record"]["result"]["secondary_structure"] == "HHEEHCCEE"
    assert result["run_record"]["result"]["limitation_label"] == (
        "Heuristic only: a fixed illustrative per-residue propensity lookup, not a "
        "validated secondary-structure predictor (no windowing, no real Chou-Fasman "
        "statistics)."
    )
