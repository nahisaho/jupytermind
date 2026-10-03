"""Tests for ai_chemistry_scientist.docking_score (DES-ACHEM-050)."""

from __future__ import annotations

import pytest

# Imported at module level (not inside each test body) so that the
# "docking-score" validator and handler register with the dispatch/validation
# registries of ai_chemistry_scientist at collection time. This keeps every test in
# this file runnable in isolation (e.g. via `pytest -k <node id>`), since
# otherwise registration would depend on another test importing this module
# first within the same pytest session.
import ai_chemistry_scientist.docking_score  # noqa: F401

_ASPIRIN = "CC(=O)OC1=CC=CC=C1C(=O)O"
_POCKET_SPEC = {"pocket_volume_A3": 200.0, "pocket_hba_sites": 2, "pocket_hbd_sites": 1}


# @id TEST-ACHEM-050
# @verifies REQ-ACHEM-050
def test_TEST_ACHEM_050_aspirin_pocket_score_matches_fixed_formula_exactly():
    from ai_chemistry_scientist.docking_score import run_docking_score

    result = run_docking_score(_ASPIRIN, _POCKET_SPEC)

    assert result["size_fit"] == pytest.approx(0.975, abs=1e-9)
    assert result["hbond_fit"] == pytest.approx(0.5, abs=1e-9)
    assert result["score"] == pytest.approx(0.7375, abs=1e-9)
    assert result["limitation_label_key"] == "docking_heuristic_limitation"


# @id TEST-ACHEM-051
# @verifies REQ-ACHEM-003 REQ-ACHEM-050
def test_TEST_ACHEM_051_non_positive_pocket_volume_is_rejected():
    from ai_chemistry_scientist.validation import validate_parameters

    for bad_volume in (0, -1.0):
        result = validate_parameters(
            "docking-score",
            {
                "ligand_smiles": _ASPIRIN,
                "pocket_spec": {**_POCKET_SPEC, "pocket_volume_A3": bad_volume},
            },
        )
        assert result["ok"] is False
        assert result["parameter"] == "pocket_volume_A3"
        assert result["constraint"] == "must be a finite number > 0"


# @id TEST-ACHEM-052
# @verifies REQ-ACHEM-003
def test_TEST_ACHEM_052_malformed_ligand_smiles_is_rejected():
    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters(
        "docking-score", {"ligand_smiles": "C1CC", "pocket_spec": _POCKET_SPEC}
    )

    assert result["ok"] is False
    assert result["parameter"] == "smiles"


# @id TEST-ACHEM-053
# @verifies REQ-ACHEM-050
def test_TEST_ACHEM_053_limitation_label_text_is_bilingual_and_exact():
    from ai_chemistry_scientist.docking_score import LIMITATION_LABEL_TEXT

    assert LIMITATION_LABEL_TEXT["en"] == (
        "Heuristic only: not a physically accurate docking simulation (no 3D "
        "conformer generation, no energy function)."
    )
    assert LIMITATION_LABEL_TEXT["ja"] == (
        "ヒューリスティックのみ: 物理的に正確なドッキングシミュレーションでは"
        "ありません（3D配座生成・エネルギー関数なし）。"
    )


# @id TEST-ACHEM-054
# @verifies REQ-ACHEM-003
def test_TEST_ACHEM_054_validator_rejects_missing_required_keys():
    from ai_chemistry_scientist.validation import validate_parameters

    missing_ligand = validate_parameters("docking-score", {"pocket_spec": _POCKET_SPEC})
    assert missing_ligand["ok"] is False
    assert missing_ligand["parameter"] == "ligand_smiles"

    missing_pocket = validate_parameters("docking-score", {"ligand_smiles": _ASPIRIN})
    assert missing_pocket["ok"] is False
    assert missing_pocket["parameter"] == "pocket_spec"

    missing_site = validate_parameters(
        "docking-score",
        {"ligand_smiles": _ASPIRIN, "pocket_spec": {"pocket_volume_A3": 200.0}},
    )
    assert missing_site["ok"] is False
    assert missing_site["parameter"] == "pocket_hba_sites"


# @id TEST-ACHEM-055
# @verifies REQ-ACHEM-050
def test_TEST_ACHEM_055_run_docking_score_rejects_unvalidated_malformed_smiles():
    import pytest

    from ai_chemistry_scientist.docking_score import run_docking_score

    with pytest.raises(ValueError, match="must already be validated"):
        run_docking_score("C1CC", _POCKET_SPEC)


# @id TEST-ACHEM-937
# @verifies REQ-ACHEM-003
def test_TEST_ACHEM_937_validator_rejects_non_dict_pocket_spec():
    from ai_chemistry_scientist.validation import validate_parameters

    for bad_pocket_spec in (None, 4, "x", [1, 2]):
        result = validate_parameters(
            "docking-score", {"ligand_smiles": _ASPIRIN, "pocket_spec": bad_pocket_spec}
        )
        assert result["ok"] is False
        assert result["parameter"] == "pocket_spec"


# @id TEST-ACHEM-938
# @verifies REQ-ACHEM-050
def test_TEST_ACHEM_938_validator_rejects_non_finite_pocket_volume():
    from ai_chemistry_scientist.validation import validate_parameters

    for bad_volume in (float("nan"), float("inf"), float("-inf")):
        pocket_spec = {**_POCKET_SPEC, "pocket_volume_A3": bad_volume}
        result = validate_parameters(
            "docking-score", {"ligand_smiles": _ASPIRIN, "pocket_spec": pocket_spec}
        )
        assert result["ok"] is False
        assert result["parameter"] == "pocket_volume_A3"
