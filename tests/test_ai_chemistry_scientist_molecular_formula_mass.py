"""Tests for ai_chemistry_scientist.molecular_formula_mass (DES-ACHEM-080)."""

from __future__ import annotations

import pytest

_ASPIRIN = "CC(=O)OC1=CC=CC=C1C(=O)O"


# @id TEST-ACHEM-946
# @verifies REQ-ACHEM-080
def test_TEST_ACHEM_946_aspirin_formula_and_exact_mass_match_acceptance():
    from ai_chemistry_scientist.molecular_formula_mass import run_molecular_formula_mass

    result = run_molecular_formula_mass(_ASPIRIN)

    assert result["molecular_formula"] == "C9H8O4"
    assert result["exact_mass"] == pytest.approx(180.042258736, abs=1e-4)


# @id TEST-ACHEM-947
# @verifies REQ-ACHEM-003 REQ-ACHEM-080
def test_TEST_ACHEM_947_validator_rejects_malformed_smiles():
    import ai_chemistry_scientist.molecular_formula_mass  # noqa: F401

    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters("molecular-formula-mass", {"smiles": "C1CC"})

    assert result["ok"] is False
    assert result["parameter"] == "smiles"
    assert result["constraint"] == "must parse to a valid RDKit molecule"


# @id TEST-ACHEM-948
# @verifies REQ-ACHEM-080
def test_TEST_ACHEM_948_run_molecular_formula_mass_rejects_unvalidated_malformed_smiles():
    import pytest

    from ai_chemistry_scientist.molecular_formula_mass import run_molecular_formula_mass

    with pytest.raises(ValueError, match="must already be validated"):
        run_molecular_formula_mass("C1CC")


# @id TEST-ACHEM-963
# @verifies REQ-ACHEM-080
def test_TEST_ACHEM_963_run_molecular_formula_mass_uses_exact_mass_api(monkeypatch):
    import ai_chemistry_scientist.molecular_formula_mass as mod

    sentinel_mol = object()

    def _unexpected_average_mass(_mol):
        raise AssertionError("average molecular weight API must not be used")

    monkeypatch.setattr(mod, "parse_smiles", lambda smiles: sentinel_mol)
    monkeypatch.setattr(mod.rdMolDescriptors, "CalcMolFormula", lambda mol: "SENTINEL")
    monkeypatch.setattr(mod.Descriptors, "MolWt", _unexpected_average_mass)
    monkeypatch.setattr(mod.Descriptors, "ExactMolWt", lambda mol: 123.456789)

    result = mod.run_molecular_formula_mass("api-fixture")

    assert result == {"molecular_formula": "SENTINEL", "exact_mass": 123.456789}


# @id TEST-ACHEM-967
# @verifies REQ-ACHEM-080
def test_TEST_ACHEM_967_validator_rejects_dummy_atom_smiles_as_chemically_undefined():
    import ai_chemistry_scientist.molecular_formula_mass  # noqa: F401

    from ai_chemistry_scientist.validation import validate_parameters

    assert validate_parameters("molecular-formula-mass", {"smiles": "*"}) == {
        "ok": False,
        "parameter": "smiles",
        "constraint": "must parse to a valid RDKit molecule",
    }
