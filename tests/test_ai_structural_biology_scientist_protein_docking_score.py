"""Tests for ai_structural_biology_scientist.protein_docking_score."""

from __future__ import annotations

import numpy as np
import pytest
from types import MappingProxyType

import ai_structural_biology_scientist.protein_docking_score  # noqa: F401


# @id TEST-ASTRUCT-030
# @verifies REQ-ASTRUCT-030
def test_TEST_ASTRUCT_030_computes_reference_protein_docking_score_with_exact_limitation_label_key():
    from ai_structural_biology_scientist.protein_docking_score import (
        LIMITATION_LABEL_KEY,
        LIMITATION_LABEL_TEXT,
        run_protein_docking_score,
    )

    result = run_protein_docking_score(
        partner_a={"hydrophobic_count": 6, "charged_count": 2},
        partner_b={"hydrophobic_count": 4, "charged_count": 3},
        interface_area_A2=750.0,
    )

    assert result["size_term"] == pytest.approx(0.9375, abs=1e-9)
    assert result["hydrophobic_complementarity"] == pytest.approx(0.4, abs=1e-9)
    assert result["charge_complementarity"] == pytest.approx(0.4, abs=1e-9)
    assert result["score"] == pytest.approx(0.66875, abs=1e-9)
    assert result["limitation_label_key"] == LIMITATION_LABEL_KEY
    assert LIMITATION_LABEL_TEXT["en"] == (
        "Heuristic only: a fixed-formula geometric/compositional complementarity "
        "score, not a physically accurate protein-protein docking simulation (no "
        "3D structure, no energy function)."
    )
    assert LIMITATION_LABEL_TEXT["ja"] == (
        "ヒューリスティックのみ：固定式の幾何・組成補完性スコアであり、"
        "物理的に正確なタンパク質間ドッキングシミュレーションではない"
        "（3D 構造なし、エネルギー関数なし）。"
    )


# @id TEST-ASTRUCT-072
# @verifies REQ-ASTRUCT-030
def test_TEST_ASTRUCT_072_accepts_numpy_integer_partner_counts_and_uses_guarded_denominators():
    from ai_structural_biology_scientist.protein_docking_score import run_protein_docking_score

    result = run_protein_docking_score(
        partner_a={"hydrophobic_count": np.int64(0), "charged_count": np.int64(0)},
        partner_b={"hydrophobic_count": np.int64(0), "charged_count": np.int64(0)},
        interface_area_A2=800.0,
    )

    assert result["size_term"] == pytest.approx(1.0, abs=1e-9)
    assert result["hydrophobic_complementarity"] == pytest.approx(0.0, abs=1e-9)
    assert result["charge_complementarity"] == pytest.approx(0.0, abs=1e-9)
    assert result["score"] == pytest.approx(0.5, abs=1e-9)


# @id TEST-ASTRUCT-078
# @verifies REQ-ASTRUCT-030
def test_TEST_ASTRUCT_078_accepts_mapping_partner_records():
    from ai_structural_biology_scientist.protein_docking_score import run_protein_docking_score

    result = run_protein_docking_score(
        partner_a=MappingProxyType({"hydrophobic_count": 6, "charged_count": 2}),
        partner_b=MappingProxyType({"hydrophobic_count": 4, "charged_count": 3}),
        interface_area_A2=750.0,
    )

    assert result["score"] == pytest.approx(0.66875, abs=1e-9)
