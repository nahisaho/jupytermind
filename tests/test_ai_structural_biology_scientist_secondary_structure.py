"""Tests for ai_structural_biology_scientist.secondary_structure."""

from __future__ import annotations

import pytest

import ai_structural_biology_scientist.secondary_structure  # noqa: F401


# @id TEST-ASTRUCT-010
# @verifies REQ-ASTRUCT-010
def test_TEST_ASTRUCT_010_assigns_reference_secondary_structure_with_exact_limitation_label_key():
    from ai_structural_biology_scientist.secondary_structure import (
        LIMITATION_LABEL_KEY,
        LIMITATION_LABEL_TEXT,
        run_secondary_structure,
    )

    result = run_secondary_structure("MKVLAGPIW")

    assert result["residues"] == [
        {"position": 0, "residue": "M", "class": "H"},
        {"position": 1, "residue": "K", "class": "H"},
        {"position": 2, "residue": "V", "class": "E"},
        {"position": 3, "residue": "L", "class": "E"},
        {"position": 4, "residue": "A", "class": "H"},
        {"position": 5, "residue": "G", "class": "C"},
        {"position": 6, "residue": "P", "class": "C"},
        {"position": 7, "residue": "I", "class": "E"},
        {"position": 8, "residue": "W", "class": "E"},
    ]
    assert result["secondary_structure"] == "HHEEHCCEE"
    assert result["helix_fraction"] == pytest.approx(0.3333333333333333, abs=1e-9)
    assert result["sheet_fraction"] == pytest.approx(0.4444444444444444, abs=1e-9)
    assert result["coil_fraction"] == pytest.approx(0.2222222222222222, abs=1e-9)
    assert result["limitation_label_key"] == LIMITATION_LABEL_KEY
    assert LIMITATION_LABEL_TEXT["en"] == (
        "Heuristic only: a fixed illustrative per-residue propensity lookup, not a "
        "validated secondary-structure predictor (no windowing, no real Chou-Fasman "
        "statistics)."
    )
    assert LIMITATION_LABEL_TEXT["ja"] == (
        "ヒューリスティックのみ：固定の説明用残基別 propensity lookup であり、"
        "検証済みの二次構造予測器ではない（windowing なし、実際の Chou-Fasman "
        "統計なし）。"
    )


# @id TEST-ASTRUCT-074
# @verifies REQ-ASTRUCT-010
def test_TEST_ASTRUCT_074_breaks_exact_propensity_ties_in_documented_helix_sheet_coil_order(
    monkeypatch: pytest.MonkeyPatch,
):
    from ai_structural_biology_scientist import secondary_structure

    monkeypatch.setitem(secondary_structure._PROPENSITIES, "A", (1.0, 1.0, 1.0))
    assert secondary_structure.run_secondary_structure("A")["secondary_structure"] == "H"

    monkeypatch.setitem(secondary_structure._PROPENSITIES, "A", (0.5, 1.0, 1.0))
    assert secondary_structure.run_secondary_structure("A")["secondary_structure"] == "E"
