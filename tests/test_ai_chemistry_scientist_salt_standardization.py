"""Tests for ai_chemistry_scientist.salt_standardization (DES-ACHEM-100)."""

from __future__ import annotations

import pytest


# @id TEST-ACHEM-972
# @verifies REQ-ACHEM-100
def test_TEST_ACHEM_972_acetic_acid_ethylamine_mixture_keeps_larger_fragment():
    from ai_chemistry_scientist.salt_standardization import run_salt_removal

    result = run_salt_removal("CC(=O)O.CCN")

    assert result["standardized_smiles"] == "CC(=O)O"
    assert result["removed_fragments"] == ["CCN"]
    assert result["fragments_removed"] is True


# @id TEST-ACHEM-973
# @verifies REQ-ACHEM-100
def test_TEST_ACHEM_973_tied_heavy_atom_counts_broken_by_canonical_smiles():
    from ai_chemistry_scientist.salt_standardization import run_salt_removal

    result = run_salt_removal("[Na+].[Cl-]")

    assert result["standardized_smiles"] == "[Cl-]"
    assert result["removed_fragments"] == ["[Na+]"]
    assert result["fragments_removed"] is True


# @id TEST-ACHEM-974
# @verifies REQ-ACHEM-100
def test_TEST_ACHEM_974_single_fragment_is_not_marked_as_salt_removed():
    from ai_chemistry_scientist.salt_standardization import run_salt_removal

    result = run_salt_removal("CCO")

    assert result["standardized_smiles"] == "CCO"
    assert result["removed_fragments"] == []
    assert result["fragments_removed"] is False


# @id TEST-ACHEM-975
# @verifies REQ-ACHEM-100
def test_TEST_ACHEM_975_three_fragment_tie_keeps_larger_fragment_and_lists_both_duplicates():
    from ai_chemistry_scientist.salt_standardization import run_salt_removal

    result = run_salt_removal("O.CC(=O)O.O")

    assert result["standardized_smiles"] == "CC(=O)O"
    assert result["removed_fragments"] == ["O", "O"]
    assert result["fragments_removed"] is True


# @id TEST-ACHEM-976
# @verifies REQ-ACHEM-100
def test_TEST_ACHEM_976_result_carries_limitation_label_key():
    from ai_chemistry_scientist.salt_standardization import (
        LIMITATION_LABEL_KEY,
        run_salt_removal,
    )

    result = run_salt_removal("CCO")

    assert result["limitation_label_key"] == LIMITATION_LABEL_KEY


# @id TEST-ACHEM-977
# @verifies REQ-ACHEM-003 REQ-ACHEM-100
def test_TEST_ACHEM_977_validator_rejects_malformed_smiles():
    import ai_chemistry_scientist.salt_standardization  # noqa: F401
    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters("salt-removal", {"smiles": "C1CC"})

    assert result == {
        "ok": False,
        "parameter": "smiles",
        "constraint": "must parse to a valid RDKit molecule",
    }


# @id TEST-ACHEM-978
# @verifies REQ-ACHEM-003 REQ-ACHEM-100
def test_TEST_ACHEM_978_validator_rejects_empty_and_dummy_atom_smiles():
    import ai_chemistry_scientist.salt_standardization  # noqa: F401
    from ai_chemistry_scientist.validation import validate_parameters

    assert validate_parameters("salt-removal", {"smiles": ""}) == {
        "ok": False,
        "parameter": "smiles",
        "constraint": "must parse to a valid RDKit molecule",
    }
    assert validate_parameters("salt-removal", {"smiles": "*"}) == {
        "ok": False,
        "parameter": "smiles",
        "constraint": "must parse to a valid RDKit molecule",
    }


# @id TEST-ACHEM-979
# @verifies REQ-ACHEM-100
def test_TEST_ACHEM_979_run_salt_removal_rejects_unvalidated_malformed_smiles():
    from ai_chemistry_scientist.salt_standardization import run_salt_removal

    with pytest.raises(ValueError, match="must already be validated"):
        run_salt_removal("C1CC")
