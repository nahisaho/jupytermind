"""Molecular descriptor calculation module (DES-ACHEM-010 / REQ-ACHEM-010)."""

from __future__ import annotations

from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

from ai_chemistry_scientist.validation import (
    fail,
    ok,
    register_batch_item_validator,
    validate_batch_item,
)

_MODULE_NAME = "molecular-descriptors"

#: The 7 descriptors every molecule in this skill is characterized by
#: (REQ-ACHEM-010). Reused by the descriptor needs of DES-ACHEM-020/030.
DESCRIPTOR_NAMES = (
    "mol_wt",
    "mol_logp",
    "tpsa",
    "num_h_donors",
    "num_h_acceptors",
    "num_rotatable_bonds",
    "num_rings",
)


def parse_smiles(smiles: str):
    """Parse ``smiles`` with RDKit, returning ``None`` on failure."""
    if not isinstance(smiles, str) or not smiles:
        return None
    return Chem.MolFromSmiles(smiles)


def compute_descriptors(mol) -> dict:
    """Compute the 7 documented descriptors for an already-parsed ``mol``."""
    return {
        "mol_wt": float(Descriptors.MolWt(mol)),
        "mol_logp": float(Descriptors.MolLogP(mol)),
        "tpsa": float(Descriptors.TPSA(mol)),
        "num_h_donors": int(Descriptors.NumHDonors(mol)),
        "num_h_acceptors": int(Descriptors.NumHAcceptors(mol)),
        "num_rotatable_bonds": int(Descriptors.NumRotatableBonds(mol)),
        "num_rings": int(rdMolDescriptors.CalcNumRings(mol)),
    }


def _molecular_descriptors_batch_item_validator(item_params: dict) -> dict:
    """DES-ACHEM-002 registered per-item validator for this module."""
    if "smiles" not in item_params:
        return fail("smiles", "is required")
    smiles = item_params["smiles"]
    if parse_smiles(smiles) is None:
        return fail("smiles", "must parse to a valid RDKit molecule")
    return ok()


register_batch_item_validator(_MODULE_NAME, _molecular_descriptors_batch_item_validator)


# @id CODE-ACHEM-010
# @implements REQ-ACHEM-010 REQ-ACHEM-003
# @design DES-ACHEM-010
def run_molecular_descriptors(smiles_list: list[str]) -> list[dict]:
    """Parse and compute descriptors for each SMILES, in input order.

    An invalid item is reported as a per-item rejection (naming the
    ``smiles`` parameter and the violated constraint) without aborting
    computation of the rest of the batch (REQ-ACHEM-003's per-item
    granularity for this module).
    """
    if not smiles_list:
        return []
    results = []
    for smiles in smiles_list:
        validation = validate_batch_item(_MODULE_NAME, {"smiles": smiles})
        if not validation["ok"]:
            results.append(
                {
                    "smiles": smiles,
                    "ok": False,
                    "parameter": validation["parameter"],
                    "constraint": validation["constraint"],
                }
            )
            continue
        mol = parse_smiles(smiles)
        descriptors = compute_descriptors(mol)
        results.append({"smiles": smiles, **descriptors})
    return results
