"""Tests for ai_chemistry_scientist.bioactivity_classification (DES-ACHEM-090)."""

from __future__ import annotations

import pytest

_DIAZEPAM = "CN1C(=O)CN=C(c2ccccc2)c2cc(Cl)ccc21"
_NILOTINIB = "CC1=C(C=C(C=C1)NC(=O)C2=CC(=CC(=C2)N3CCN(CC3)C)C(F)(F)F)NC4=NC=NC(=N4)C5=CN=CC=C5"
_ASPIRIN = "CC(=O)OC1=CC=CC=C1C(=O)O"


# @id TEST-ACHEM-949
# @verifies REQ-ACHEM-090
@pytest.mark.parametrize(
    (
        "smiles",
        "expected_label",
        "expected_tpsa",
        "expected_mol_logp",
        "expected_mol_wt",
        "expected_aromatic_ring_count",
    ),
    [
        (_DIAZEPAM, "CNS_like", 32.67, 3.1538000000000025, 284.74600000000004, 2),
        (
            _NILOTINIB,
            "kinase_inhibitor_like",
            99.17000000000002,
            5.0085200000000025,
            548.5730000000002,
            4,
        ),
        (_ASPIRIN, "other", 63.60000000000001, 1.3101, 180.15899999999996, 1),
    ],
)
def test_TEST_ACHEM_949_classification_fixtures_match_acceptance(
    smiles,
    expected_label,
    expected_tpsa,
    expected_mol_logp,
    expected_mol_wt,
    expected_aromatic_ring_count,
):
    from ai_chemistry_scientist.bioactivity_classification import (
        LIMITATION_LABEL_KEY,
        run_bioactivity_classification,
    )

    result = run_bioactivity_classification(smiles)

    assert result["label"] == expected_label
    assert result["tpsa"] == pytest.approx(expected_tpsa, abs=1e-4)
    assert result["mol_logp"] == pytest.approx(expected_mol_logp, abs=1e-4)
    assert result["mol_wt"] == pytest.approx(expected_mol_wt, abs=1e-9)
    assert result["aromatic_ring_count"] == expected_aromatic_ring_count
    assert result["limitation_label_key"] == LIMITATION_LABEL_KEY


# @id TEST-ACHEM-950
# @verifies REQ-ACHEM-003 REQ-ACHEM-090
def test_TEST_ACHEM_950_validator_rejects_malformed_smiles():
    import ai_chemistry_scientist.bioactivity_classification  # noqa: F401

    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters("bioactivity-classification", {"smiles": "C1CC"})

    assert result["ok"] is False
    assert result["parameter"] == "smiles"
    assert result["constraint"] == "must parse to a valid RDKit molecule"


# @id TEST-ACHEM-951
# @verifies REQ-ACHEM-090
def test_TEST_ACHEM_951_limitation_label_text_is_bilingual_and_exact():
    from ai_chemistry_scientist.bioactivity_classification import LIMITATION_LABEL_TEXT

    assert LIMITATION_LABEL_TEXT["en"] == (
        "Heuristic only: not a ChEMBL-trained or experimentally validated bioactivity classifier."
    )
    assert LIMITATION_LABEL_TEXT["ja"] == (
        "ヒューリスティックのみ: ChEMBLで学習済みでも実験的に検証済みでもない"
        "生物活性分類器ではない。"
    )


# @id TEST-ACHEM-952
# @verifies REQ-ACHEM-090
def test_TEST_ACHEM_952_run_bioactivity_classification_rejects_unvalidated_malformed_smiles():
    import pytest

    from ai_chemistry_scientist.bioactivity_classification import run_bioactivity_classification

    with pytest.raises(ValueError, match="must already be validated"):
        run_bioactivity_classification("C1CC")


# @id TEST-ACHEM-964
# @verifies REQ-ACHEM-090
def test_TEST_ACHEM_964_cns_like_branch_stays_first_and_tpsa_boundary_excludes_it(monkeypatch):
    import ai_chemistry_scientist.bioactivity_classification as mod

    sentinel_mol = object()

    monkeypatch.setattr(mod, "parse_smiles", lambda smiles: sentinel_mol)
    monkeypatch.setattr(mod.rdMolDescriptors, "CalcNumAromaticRings", lambda mol: 4)

    monkeypatch.setattr(
        mod,
        "compute_descriptors",
        lambda mol: {"tpsa": 50.0, "mol_logp": 3.0, "mol_wt": 450.0},
    )
    assert mod.run_bioactivity_classification("both-branches-true")["label"] == "CNS_like"

    monkeypatch.setattr(
        mod,
        "compute_descriptors",
        lambda mol: {"tpsa": 90.0, "mol_logp": 2.0, "mol_wt": 450.0},
    )
    assert mod.run_bioactivity_classification("tpsa-boundary")["label"] == "kinase_inhibitor_like"


# @id TEST-ACHEM-968
# @verifies REQ-ACHEM-090
def test_TEST_ACHEM_968_validator_rejects_dummy_atom_smiles_as_chemically_undefined():
    import ai_chemistry_scientist.bioactivity_classification  # noqa: F401

    from ai_chemistry_scientist.validation import validate_parameters

    assert validate_parameters("bioactivity-classification", {"smiles": "*"}) == {
        "ok": False,
        "parameter": "smiles",
        "constraint": "must parse to a valid RDKit molecule",
    }
