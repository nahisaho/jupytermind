"""Chemical structure format conversion module (DES-ACHEM-110 / REQ-ACHEM-110)."""

from __future__ import annotations

from rdkit import Chem
from rdkit.Chem import inchi as rdkit_inchi

from ai_chemistry_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "structure-format-conversion"

INPUT_FORMATS = ("smiles", "inchi", "molblock")
OUTPUT_FORMATS = ("smiles", "inchi", "inchikey", "molblock")

_PARSERS = {
    "smiles": Chem.MolFromSmiles,
    "inchi": rdkit_inchi.MolFromInchi,
    "molblock": Chem.MolFromMolBlock,
}
_WRITERS = {
    "smiles": Chem.MolToSmiles,
    "inchi": rdkit_inchi.MolToInchi,
    "inchikey": rdkit_inchi.MolToInchiKey,
    "molblock": Chem.MolToMolBlock,
}


def _parse_structure(input_format: str, input_value):
    """Parse ``input_value`` with the ``input_format``-matching RDKit parser.

    Rejects a non-str, empty, or unparseable value; a value that parses to a
    zero-atom molecule (e.g. an empty SMILES or a ``0 0`` atom/bond-count
    Molblock, which RDKit parses without error); and (same chemical-validity
    domain as REQ-ACHEM-100 and every other module in this skill) any value
    that parses but contains a dummy/query atom (RDKit atomic number 0).
    """
    if not isinstance(input_value, str) or not input_value:
        return None
    mol = _PARSERS[input_format](input_value)
    if mol is None or mol.GetNumAtoms() == 0:
        return None
    if any(atom.GetAtomicNum() == 0 for atom in mol.GetAtoms()):
        return None
    return mol


# @id CODE-ACHEM-922
# @implements REQ-ACHEM-003 REQ-ACHEM-110
# @design DES-ACHEM-002
def _structure_format_conversion_validator(params: dict) -> dict:
    for name in ("input_format", "output_format", "input_value"):
        if name not in params:
            return fail(name, "is required")
    input_format = params["input_format"]
    output_format = params["output_format"]
    if input_format not in INPUT_FORMATS:
        return fail("input_format", "must be one of the supported formats")
    if output_format not in OUTPUT_FORMATS:
        return fail("output_format", "must be one of the supported formats")
    if _parse_structure(input_format, params["input_value"]) is None:
        return fail(
            "input_value",
            f"must parse with the {input_format}-matching RDKit parser",
        )
    return ok()


register_validator(_MODULE_NAME, _structure_format_conversion_validator)


# @id CODE-ACHEM-110
# @implements REQ-ACHEM-110
# @design DES-ACHEM-110
def run_structure_conversion(input_format: str, input_value: str, output_format: str) -> dict:
    """Parse ``input_value`` per ``input_format`` and render per ``output_format``."""
    mol = _parse_structure(input_format, input_value)
    if mol is None or mol.GetNumAtoms() == 0:
        raise ValueError("input_value must already be validated by the handler wrapper")

    output_value = _WRITERS[output_format](mol)
    return {
        "output_format": output_format,
        "output_value": output_value,
    }
