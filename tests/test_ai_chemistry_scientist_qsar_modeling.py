"""Tests for ai_chemistry_scientist.qsar_modeling (DES-ACHEM-030)."""

from __future__ import annotations

import pytest

_TRAINING_SMILES = {
    "aspirin": "CC(=O)OC1=CC=CC=C1C(=O)O",
    "ibuprofen": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
    "caffeine": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
    "paracetamol": "CC(=O)NC1=CC=C(C=C1)O",
    "naproxen": "COC1=CC2=CC(=CC=C2C=C1)C(C)C(=O)O",
}
_DICLOFENAC_QUERY = "OC(=O)Cc1ccccc1Nc1c(Cl)cccc1Cl"


def _build_training_set():
    from ai_chemistry_scientist.molecular_descriptors import compute_descriptors, parse_smiles

    training_set = []
    for smiles in _TRAINING_SMILES.values():
        descriptors = compute_descriptors(parse_smiles(smiles))
        activity = 2.0 * descriptors["mol_wt"] - 50.0
        training_set.append({"smiles": smiles, "activity": activity})
    return training_set


# @id TEST-ACHEM-030
# @verifies REQ-ACHEM-030
def test_TEST_ACHEM_030_fits_known_linear_law_exactly():
    from ai_chemistry_scientist.qsar_modeling import run_qsar_modeling

    result = run_qsar_modeling(_build_training_set(), [_DICLOFENAC_QUERY])

    assert result["coefficients"][0] == pytest.approx(2.0, abs=1e-6)
    assert result["coefficients"][1] == pytest.approx(0.0, abs=1e-6)
    assert result["coefficients"][2] == pytest.approx(0.0, abs=1e-6)
    assert result["intercept"] == pytest.approx(-50.0, abs=1e-6)
    [prediction] = result["predictions"]
    assert prediction["smiles"] == _DICLOFENAC_QUERY
    assert prediction["predicted_activity"] == pytest.approx(542.306, abs=1e-3)


# @id TEST-ACHEM-031
# @verifies REQ-ACHEM-030
def test_TEST_ACHEM_031_predictions_and_coefficients_are_plain_python_floats():
    from ai_chemistry_scientist.qsar_modeling import run_qsar_modeling

    result = run_qsar_modeling(_build_training_set(), [_DICLOFENAC_QUERY])

    assert all(isinstance(c, float) for c in result["coefficients"])
    assert isinstance(result["intercept"], float)
    assert isinstance(result["predictions"][0]["predicted_activity"], float)


# @id TEST-ACHEM-032
# @verifies REQ-ACHEM-003 REQ-ACHEM-030
def test_TEST_ACHEM_032_fewer_than_five_compounds_is_rejected():
    from ai_chemistry_scientist.validation import validate_parameters

    four_compounds = _build_training_set()[:4]

    result = validate_parameters(
        "qsar-modeling",
        {"training_set": four_compounds, "query_smiles_list": [_DICLOFENAC_QUERY]},
    )

    assert result["ok"] is False
    assert result["parameter"] == "training_set"
    assert (
        result["constraint"]
        == "must contain at least 5 compounds with a full-rank descriptor matrix"
    )


# @id TEST-ACHEM-033
# @verifies REQ-ACHEM-003 REQ-ACHEM-030
def test_TEST_ACHEM_033_rank_deficient_training_set_is_rejected():
    from ai_chemistry_scientist.validation import validate_parameters

    identical_rows = [{"smiles": _TRAINING_SMILES["aspirin"], "activity": 1.0} for _ in range(5)]

    result = validate_parameters(
        "qsar-modeling",
        {"training_set": identical_rows, "query_smiles_list": [_DICLOFENAC_QUERY]},
    )

    assert result["ok"] is False
    assert result["parameter"] == "training_set"


# @id TEST-ACHEM-034
# @verifies REQ-ACHEM-003
def test_TEST_ACHEM_034_validator_rejects_missing_required_keys():
    from ai_chemistry_scientist.validation import validate_parameters

    missing_training = validate_parameters(
        "qsar-modeling", {"query_smiles_list": [_DICLOFENAC_QUERY]}
    )
    assert missing_training["ok"] is False
    assert missing_training["parameter"] == "training_set"

    missing_query = validate_parameters("qsar-modeling", {"training_set": _build_training_set()})
    assert missing_query["ok"] is False
    assert missing_query["parameter"] == "query_smiles_list"
