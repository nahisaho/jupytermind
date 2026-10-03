"""Tests for ai_chemistry_scientist.admet_prediction (DES-ACHEM-020)."""

from __future__ import annotations

_ASPIRIN = "CC(=O)OC1=CC=CC=C1C(=O)O"
_CYCLOSPORINE = (
    "CCC1NC(=O)C(C(O)C(C)CC=CC)N(C)C(=O)C(C(C)C)N(C)C(=O)C(CC(C)C)N(C)C(=O)"
    "C(CC(C)C)N(C)C(=O)C(C)NC(=O)C(C)NC(=O)C(CC(C)C)N(C)C(=O)C(C(C)C)N(C)C(=O)"
    "C(CC(C)C)N(C)C1=O"
)


# @id TEST-ACHEM-020
# @verifies REQ-ACHEM-020
def test_TEST_ACHEM_020_aspirin_passes_both_lipinski_and_veber():
    from ai_chemistry_scientist.admet_prediction import run_admet_prediction

    result = run_admet_prediction(_ASPIRIN)

    assert result["lipinski_violations"] == []
    assert result["lipinski_pass"] is True
    assert result["veber_violations"] == []
    assert result["veber_pass"] is True
    assert result["limitation_label_key"] == "admet_heuristic_limitation"


# @id TEST-ACHEM-021
# @verifies REQ-ACHEM-020
def test_TEST_ACHEM_021_cyclosporine_fails_both_in_fixed_criterion_order():
    from ai_chemistry_scientist.admet_prediction import run_admet_prediction

    result = run_admet_prediction(_CYCLOSPORINE)

    assert result["lipinski_violations"] == ["MolWt", "NumHAcceptors"]
    assert result["lipinski_pass"] is False
    assert result["veber_violations"] == ["NumRotatableBonds", "TPSA"]
    assert result["veber_pass"] is False


# @id TEST-ACHEM-022
# @verifies REQ-ACHEM-003
def test_TEST_ACHEM_022_validator_rejects_malformed_smiles():
    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters("admet-prediction", {"smiles": "C1CC"})

    assert result["ok"] is False
    assert result["parameter"] == "smiles"
    assert result["constraint"] == "must parse to a valid RDKit molecule"


# @id TEST-ACHEM-023
# @verifies REQ-ACHEM-020
def test_TEST_ACHEM_023_limitation_label_text_is_bilingual_and_exact():
    from ai_chemistry_scientist.admet_prediction import LIMITATION_LABEL_TEXT

    assert LIMITATION_LABEL_TEXT["en"] == (
        "Heuristic only: not a physically or clinically validated ADMET prediction."
    )
    assert LIMITATION_LABEL_TEXT["ja"] == (
        "ヒューリスティックのみ: 物理的または臨床的に検証されたADMET予測ではありません。"
    )


# @id TEST-ACHEM-024
# @verifies REQ-ACHEM-003
def test_TEST_ACHEM_024_validator_rejects_missing_smiles_key():
    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters("admet-prediction", {})

    assert result["ok"] is False
    assert result["parameter"] == "smiles"
    assert result["constraint"] == "is required"


# @id TEST-ACHEM-025
# @verifies REQ-ACHEM-020
def test_TEST_ACHEM_025_run_admet_prediction_rejects_unvalidated_malformed_smiles():
    import pytest

    from ai_chemistry_scientist.admet_prediction import run_admet_prediction

    with pytest.raises(ValueError, match="must already be validated"):
        run_admet_prediction("C1CC")
