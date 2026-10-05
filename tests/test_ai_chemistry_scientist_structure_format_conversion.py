"""Tests for ai_chemistry_scientist.structure_format_conversion (DES-ACHEM-110)."""

from __future__ import annotations

import pytest

_ASPIRIN_SMILES = "CC(=O)OC1=CC=CC=C1C(=O)O"
_ASPIRIN_INCHI = "InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)"
_ASPIRIN_INCHIKEY = "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"
_ASPIRIN_CANONICAL = "CC(=O)Oc1ccccc1C(=O)O"
_ETHANOL_MOLBLOCK = (
    "\n     RDKit          2D\n\n"
    "  3  2  0  0  0  0  0  0  0  0999 V2000\n"
    "    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0\n"
    "    1.2990    0.7500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0\n"
    "    2.5981   -0.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0\n"
    "  1  2  1  0\n"
    "  2  3  1  0\n"
    "M  END\n"
)


# @id TEST-ACHEM-980
# @verifies REQ-ACHEM-110
def test_TEST_ACHEM_980_aspirin_smiles_to_smiles_inchi_inchikey():
    from ai_chemistry_scientist.structure_format_conversion import run_structure_conversion

    smiles_result = run_structure_conversion("smiles", _ASPIRIN_SMILES, "smiles")
    inchi_result = run_structure_conversion("smiles", _ASPIRIN_SMILES, "inchi")
    inchikey_result = run_structure_conversion("smiles", _ASPIRIN_SMILES, "inchikey")

    assert smiles_result == {"output_format": "smiles", "output_value": _ASPIRIN_CANONICAL}
    assert inchi_result == {"output_format": "inchi", "output_value": _ASPIRIN_INCHI}
    assert inchikey_result == {"output_format": "inchikey", "output_value": _ASPIRIN_INCHIKEY}


# @id TEST-ACHEM-981
# @verifies REQ-ACHEM-110
def test_TEST_ACHEM_981_inchi_back_to_smiles_round_trips_to_same_canonical_smiles():
    from ai_chemistry_scientist.structure_format_conversion import run_structure_conversion

    result = run_structure_conversion("inchi", _ASPIRIN_INCHI, "smiles")

    assert result == {"output_format": "smiles", "output_value": _ASPIRIN_CANONICAL}


# @id TEST-ACHEM-982
# @verifies REQ-ACHEM-110
def test_TEST_ACHEM_982_ethanol_molblock_to_smiles():
    from ai_chemistry_scientist.structure_format_conversion import run_structure_conversion

    result = run_structure_conversion("molblock", _ETHANOL_MOLBLOCK, "smiles")

    assert result == {"output_format": "smiles", "output_value": "CCO"}


# @id TEST-ACHEM-983
# @verifies REQ-ACHEM-003 REQ-ACHEM-110
def test_TEST_ACHEM_983_validator_rejects_unsupported_input_and_output_formats():
    import ai_chemistry_scientist.structure_format_conversion  # noqa: F401
    from ai_chemistry_scientist.validation import validate_parameters

    bad_input_format = validate_parameters(
        "structure-format-conversion",
        {"input_format": "inchikey", "input_value": _ASPIRIN_INCHIKEY, "output_format": "smiles"},
    )
    bad_output_format = validate_parameters(
        "structure-format-conversion",
        {"input_format": "smiles", "input_value": _ASPIRIN_SMILES, "output_format": "cml"},
    )

    assert bad_input_format == {
        "ok": False,
        "parameter": "input_format",
        "constraint": "must be one of the supported formats",
    }
    assert bad_output_format == {
        "ok": False,
        "parameter": "output_format",
        "constraint": "must be one of the supported formats",
    }


# @id TEST-ACHEM-984
# @verifies REQ-ACHEM-003 REQ-ACHEM-110
def test_TEST_ACHEM_984_validator_rejects_unparseable_empty_and_dummy_atom_input_value():
    import ai_chemistry_scientist.structure_format_conversion  # noqa: F401
    from ai_chemistry_scientist.validation import validate_parameters

    for input_value in ("", "*", "not a smiles"):
        result = validate_parameters(
            "structure-format-conversion",
            {"input_format": "smiles", "input_value": input_value, "output_format": "smiles"},
        )
        assert result == {
            "ok": False,
            "parameter": "input_value",
            "constraint": "must parse with the smiles-matching RDKit parser",
        }


# @id TEST-ACHEM-985
# @verifies REQ-ACHEM-110
def test_TEST_ACHEM_985_run_structure_conversion_rejects_unvalidated_malformed_input():
    from ai_chemistry_scientist.structure_format_conversion import run_structure_conversion

    with pytest.raises(ValueError, match="must already be validated"):
        run_structure_conversion("smiles", "not a smiles", "smiles")


_ZERO_ATOM_MOLBLOCK = (
    "\n     RDKit          2D\n\n  0  0  0  0  0  0  0  0  0  0999 V2000\nM  END\n"
)


# @id TEST-ACHEM-986
# @verifies REQ-ACHEM-003 REQ-ACHEM-110
def test_TEST_ACHEM_986_validator_rejects_zero_atom_molblock():
    import ai_chemistry_scientist.structure_format_conversion  # noqa: F401
    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters(
        "structure-format-conversion",
        {"input_format": "molblock", "input_value": _ZERO_ATOM_MOLBLOCK, "output_format": "smiles"},
    )
    assert result == {
        "ok": False,
        "parameter": "input_value",
        "constraint": "must parse with the molblock-matching RDKit parser",
    }
