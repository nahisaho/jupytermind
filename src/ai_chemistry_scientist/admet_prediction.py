"""ADMET heuristic screening module (DES-ACHEM-020 / REQ-ACHEM-020)."""

from __future__ import annotations

from ai_chemistry_scientist.molecular_descriptors import compute_descriptors, parse_smiles
from ai_chemistry_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "admet-prediction"

#: Fixed-order Lipinski Rule-of-Five criteria (REQ-ACHEM-020 acceptance).
_LIPINSKI_CRITERIA = (
    ("MolWt", lambda d: d["mol_wt"] <= 500),
    ("MolLogP", lambda d: d["mol_logp"] <= 5),
    ("NumHDonors", lambda d: d["num_h_donors"] <= 5),
    ("NumHAcceptors", lambda d: d["num_h_acceptors"] <= 10),
)
#: Fixed-order Veber rule criteria (REQ-ACHEM-020 acceptance).
_VEBER_CRITERIA = (
    ("NumRotatableBonds", lambda d: d["num_rotatable_bonds"] <= 10),
    ("TPSA", lambda d: d["tpsa"] <= 140),
)

#: The handler wrapper of DES-ACHEM-001 substitutes this key for the
#: `language`-specific text before `record_run` (REQ-ACHEM-020 Constraints).
LIMITATION_LABEL_KEY = "admet_heuristic_limitation"
LIMITATION_LABEL_TEXT = {
    "en": "Heuristic only: not a physically or clinically validated ADMET prediction.",
    "ja": ("ヒューリスティックのみ: 物理的または臨床的に検証されたADMET予測ではありません。"),
}


def _admet_prediction_validator(params: dict) -> dict:
    """DES-ACHEM-002 registered atomic validator for this module."""
    if "smiles" not in params:
        return fail("smiles", "is required")
    if parse_smiles(params["smiles"]) is None:
        return fail("smiles", "must parse to a valid RDKit molecule")
    return ok()


register_validator(_MODULE_NAME, _admet_prediction_validator)


# @id CODE-ACHEM-020
# @implements REQ-ACHEM-020
# @design DES-ACHEM-020
def run_admet_prediction(smiles: str) -> dict:
    """Compute descriptors and the Lipinski/Veber heuristic flags.

    Receives ``smiles`` already validated atomically by its handler wrapper
    (DES-ACHEM-001); performs no revalidation of its own.
    """
    mol = parse_smiles(smiles)
    if mol is None:
        raise ValueError("smiles must already be validated by the handler wrapper")
    descriptors = compute_descriptors(mol)

    lipinski_violations = [name for name, check in _LIPINSKI_CRITERIA if not check(descriptors)]
    lipinski_pass = len(lipinski_violations) <= 1

    veber_violations = [name for name, check in _VEBER_CRITERIA if not check(descriptors)]
    veber_pass = len(veber_violations) == 0

    return {
        "descriptors": descriptors,
        "lipinski_violations": lipinski_violations,
        "lipinski_pass": lipinski_pass,
        "veber_violations": veber_violations,
        "veber_pass": veber_pass,
        "limitation_label_key": LIMITATION_LABEL_KEY,
    }
