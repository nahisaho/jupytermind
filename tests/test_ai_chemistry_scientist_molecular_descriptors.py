"""Tests for ai_chemistry_scientist.molecular_descriptors (DES-ACHEM-010)."""

from __future__ import annotations

import pytest

_ASPIRIN = "CC(=O)OC1=CC=CC=C1C(=O)O"
_MALFORMED = "C1CC"


# @id TEST-ACHEM-010
# @verifies REQ-ACHEM-010
def test_TEST_ACHEM_010_computes_seven_descriptors_for_aspirin():
    from ai_chemistry_scientist.molecular_descriptors import run_molecular_descriptors

    [result] = run_molecular_descriptors([_ASPIRIN])

    assert result["mol_wt"] == pytest.approx(180.159, abs=0.01)
    assert result["mol_logp"] == pytest.approx(1.3101, abs=0.001)
    assert result["tpsa"] == pytest.approx(63.60, abs=0.01)
    assert result["num_h_donors"] == 1
    assert result["num_h_acceptors"] == 3
    assert result["num_rotatable_bonds"] == 2
    assert result["num_rings"] == 1


# @id TEST-ACHEM-011
# @verifies REQ-ACHEM-010 REQ-ACHEM-003
def test_TEST_ACHEM_011_batch_continues_past_malformed_item():
    from ai_chemistry_scientist.molecular_descriptors import run_molecular_descriptors

    results = run_molecular_descriptors([_ASPIRIN, _MALFORMED])

    assert results[0]["mol_wt"] == pytest.approx(180.159, abs=0.01)
    assert results[1]["ok"] is False
    assert results[1]["parameter"] == "smiles"
    assert results[1]["constraint"] == "must parse to a valid RDKit molecule"


# @id TEST-ACHEM-012
# @verifies REQ-ACHEM-003
def test_TEST_ACHEM_012_batch_item_validator_rejects_malformed_smiles():
    from ai_chemistry_scientist.validation import validate_batch_item

    result = validate_batch_item("molecular-descriptors", {"smiles": _MALFORMED})

    assert result["ok"] is False
    assert result["parameter"] == "smiles"
    assert result["constraint"] == "must parse to a valid RDKit molecule"


# @id TEST-ACHEM-013
# @verifies REQ-ACHEM-010
def test_TEST_ACHEM_013_parse_smiles_returns_none_for_malformed_input():
    from ai_chemistry_scientist.molecular_descriptors import parse_smiles

    assert parse_smiles(_MALFORMED) is None
    assert parse_smiles(_ASPIRIN) is not None


# @id TEST-ACHEM-014
# @verifies REQ-ACHEM-003
def test_TEST_ACHEM_014_batch_item_validator_rejects_missing_smiles_key():
    from ai_chemistry_scientist.validation import validate_batch_item

    result = validate_batch_item("molecular-descriptors", {})

    assert result["ok"] is False
    assert result["parameter"] == "smiles"
    assert result["constraint"] == "is required"


# @id TEST-ACHEM-015
# @verifies REQ-ACHEM-010
def test_TEST_ACHEM_015_empty_smiles_list_returns_empty_results():
    from ai_chemistry_scientist.molecular_descriptors import run_molecular_descriptors

    assert run_molecular_descriptors([]) == []
