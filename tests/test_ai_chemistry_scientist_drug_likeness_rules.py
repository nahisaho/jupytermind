"""Tests for ai_chemistry_scientist.drug_likeness_rules (DES-ACHEM-060)."""

from __future__ import annotations

import pytest

_ASPIRIN = "CC(=O)OC1=CC=CC=C1C(=O)O"
_ETHANOL = "CCO"


# @id TEST-ACHEM-939
# @verifies REQ-ACHEM-060
@pytest.mark.parametrize(
    (
        "smiles",
        "expected_aromatic_ring_count",
        "expected_mol_mr",
        "expected_heavy_atom_count",
        "expected_ghose_violations",
        "expected_ghose_pass",
        "expected_egan_violations",
        "expected_egan_pass",
    ),
    [
        (_ASPIRIN, 1, 44.71030000000002, 13, ["heavy_atom_count"], False, [], True),
        (
            _ETHANOL,
            0,
            12.759800000000002,
            3,
            ["MolWt", "MolMR", "heavy_atom_count"],
            False,
            [],
            True,
        ),
    ],
)
def test_TEST_ACHEM_939_drug_likeness_rule_fixtures_match_acceptance(
    smiles,
    expected_aromatic_ring_count,
    expected_mol_mr,
    expected_heavy_atom_count,
    expected_ghose_violations,
    expected_ghose_pass,
    expected_egan_violations,
    expected_egan_pass,
):
    from ai_chemistry_scientist.drug_likeness_rules import run_drug_likeness_rules

    result = run_drug_likeness_rules(smiles)

    assert result["aromatic_ring_count"] == expected_aromatic_ring_count
    assert result["mol_mr"] == pytest.approx(expected_mol_mr, abs=1e-4)
    assert result["heavy_atom_count"] == expected_heavy_atom_count
    assert result["ghose_violations"] == expected_ghose_violations
    assert result["ghose_pass"] is expected_ghose_pass
    assert result["egan_violations"] == expected_egan_violations
    assert result["egan_pass"] is expected_egan_pass


# @id TEST-ACHEM-940
# @verifies REQ-ACHEM-003 REQ-ACHEM-060
def test_TEST_ACHEM_940_validator_rejects_malformed_smiles():
    import ai_chemistry_scientist.drug_likeness_rules  # noqa: F401

    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters("drug-likeness-rules", {"smiles": "C1CC"})

    assert result["ok"] is False
    assert result["parameter"] == "smiles"
    assert result["constraint"] == "must parse to a valid RDKit molecule"


# @id TEST-ACHEM-941
# @verifies REQ-ACHEM-060
def test_TEST_ACHEM_941_run_drug_likeness_rules_rejects_unvalidated_malformed_smiles():
    import pytest

    from ai_chemistry_scientist.drug_likeness_rules import run_drug_likeness_rules

    with pytest.raises(ValueError, match="must already be validated"):
        run_drug_likeness_rules("C1CC")


# @id TEST-ACHEM-961
# @verifies REQ-ACHEM-060
def test_TEST_ACHEM_961_ghose_and_egan_exact_thresholds_are_inclusive(monkeypatch):
    import ai_chemistry_scientist.drug_likeness_rules as mod

    class _FakeMol:
        def GetNumHeavyAtoms(self):
            return 20

    monkeypatch.setattr(mod, "parse_smiles", lambda smiles: _FakeMol())
    monkeypatch.setattr(
        mod,
        "compute_descriptors",
        lambda mol: {"mol_wt": 160.0, "mol_logp": 5.6, "tpsa": 131.6},
    )
    monkeypatch.setattr(mod.Descriptors, "MolMR", lambda mol: 40.0)
    monkeypatch.setattr(mod.rdMolDescriptors, "CalcNumAromaticRings", lambda mol: 0)

    result = mod.run_drug_likeness_rules("threshold-fixture")

    assert result["ghose_violations"] == []
    assert result["ghose_pass"] is True
    assert result["egan_violations"] == []
    assert result["egan_pass"] is True


# @id TEST-ACHEM-965
# @verifies REQ-ACHEM-060
def test_TEST_ACHEM_965_validator_rejects_dummy_atom_smiles_as_chemically_undefined():
    import ai_chemistry_scientist.drug_likeness_rules  # noqa: F401

    from ai_chemistry_scientist.validation import validate_parameters

    assert validate_parameters("drug-likeness-rules", {"smiles": "*"}) == {
        "ok": False,
        "parameter": "smiles",
        "constraint": "must parse to a valid RDKit molecule",
    }
