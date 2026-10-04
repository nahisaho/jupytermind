"""Molecular formula and exact mass module (DES-ACHEM-080 / REQ-ACHEM-080)."""

from __future__ import annotations

from rdkit.Chem import Descriptors, rdMolDescriptors

from ai_chemistry_scientist.molecular_descriptors import parse_smiles
from ai_chemistry_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "molecular-formula-mass"


# @id CODE-ACHEM-919
# @implements REQ-ACHEM-003 REQ-ACHEM-080
# @design DES-ACHEM-002
def _molecular_formula_mass_validator(params: dict) -> dict:
    if "smiles" not in params:
        return fail("smiles", "is required")
    if parse_smiles(params["smiles"]) is None:
        return fail("smiles", "must parse to a valid RDKit molecule")
    return ok()


register_validator(_MODULE_NAME, _molecular_formula_mass_validator)


# @id CODE-ACHEM-080
# @implements REQ-ACHEM-080
# @design DES-ACHEM-080
def run_molecular_formula_mass(smiles: str) -> dict:
    """Compute the molecular formula and exact mass for ``smiles``."""
    mol = parse_smiles(smiles)
    if mol is None:
        raise ValueError("smiles must already be validated by the handler wrapper")
    molecular_formula = rdMolDescriptors.CalcMolFormula(mol)
    exact_mass = float(Descriptors.ExactMolWt(mol))
    return {
        "molecular_formula": molecular_formula,
        "exact_mass": exact_mass,
    }
