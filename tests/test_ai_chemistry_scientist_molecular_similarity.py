"""Tests for ai_chemistry_scientist.molecular_similarity (DES-ACHEM-040)."""

from __future__ import annotations

import pytest

_ASPIRIN = "CC(=O)OC1=CC=CC=C1C(=O)O"
_IBUPROFEN = "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O"


# @id TEST-ACHEM-040
# @verifies REQ-ACHEM-040
def test_TEST_ACHEM_040_aspirin_query_returns_exact_top5_ranked_list():
    from ai_chemistry_scientist.molecular_similarity import run_molecular_similarity

    result = run_molecular_similarity(_ASPIRIN, k=5)
    names = [entry["name"] for entry in result["results"]]
    similarities = [entry["similarity"] for entry in result["results"]]

    assert names == ["aspirin", "warfarin", "paracetamol", "diclofenac", "naproxen"]
    assert similarities[0] == pytest.approx(1.0, abs=1e-5)
    assert similarities[1] == pytest.approx(0.244898, abs=1e-5)
    assert similarities[2] == pytest.approx(0.222222, abs=1e-5)
    assert similarities[3] == pytest.approx(0.195652, abs=1e-5)
    assert similarities[4] == pytest.approx(0.195652, abs=1e-5)


# @id TEST-ACHEM-041
# @verifies REQ-ACHEM-040
def test_TEST_ACHEM_041_ibuprofen_query_returns_exact_top5_ranked_list():
    from ai_chemistry_scientist.molecular_similarity import run_molecular_similarity

    result = run_molecular_similarity(_IBUPROFEN, k=5)
    names = [entry["name"] for entry in result["results"]]
    similarities = [entry["similarity"] for entry in result["results"]]

    assert names == ["ibuprofen", "naproxen", "warfarin", "cetirizine", "metoprolol"]
    assert similarities[1] == pytest.approx(0.4, abs=1e-5)
    assert similarities[2] == pytest.approx(0.215686, abs=1e-5)
    assert similarities[3] == pytest.approx(0.196429, abs=1e-5)
    assert similarities[4] == pytest.approx(0.196078, abs=1e-5)


# @id TEST-ACHEM-042
# @verifies REQ-ACHEM-040
def test_TEST_ACHEM_042_dataset_has_exactly_20_rows_in_documented_order():
    import csv
    from pathlib import Path

    import ai_chemistry_scientist.molecular_similarity as module

    with Path(module._DATA_PATH).open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 20
    assert rows[0]["name"] == "aspirin"
    assert rows[-1]["name"] == "sertraline"


# @id TEST-ACHEM-043
# @verifies REQ-ACHEM-003 REQ-ACHEM-040
@pytest.mark.parametrize("bad_k", [0, 21, 1.5, -1])
def test_TEST_ACHEM_043_k_outside_1_to_20_is_rejected(bad_k):
    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters("molecular-similarity", {"query_smiles": _ASPIRIN, "k": bad_k})

    assert result["ok"] is False
    assert result["parameter"] == "k"
    assert result["constraint"] == "must be an integer in [1, 20]"


# @id TEST-ACHEM-044
# @verifies REQ-ACHEM-003
def test_TEST_ACHEM_044_malformed_query_smiles_is_rejected():
    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters("molecular-similarity", {"query_smiles": "C1CC", "k": 5})

    assert result["ok"] is False
    assert result["parameter"] == "smiles"


# @id TEST-ACHEM-045
# @verifies REQ-ACHEM-003
def test_TEST_ACHEM_045_validator_rejects_missing_required_keys():
    from ai_chemistry_scientist.validation import validate_parameters

    missing_query = validate_parameters("molecular-similarity", {"k": 5})
    assert missing_query["ok"] is False
    assert missing_query["parameter"] == "query_smiles"

    missing_k = validate_parameters("molecular-similarity", {"query_smiles": _ASPIRIN})
    assert missing_k["ok"] is False
    assert missing_k["parameter"] == "k"
