"""Bioactivity classification module (DES-ACHEM-090 / REQ-ACHEM-090)."""

from __future__ import annotations

from rdkit.Chem import rdMolDescriptors

from ai_chemistry_scientist.molecular_descriptors import compute_descriptors, parse_smiles
from ai_chemistry_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "bioactivity-classification"
# Named decision-threshold constants (DES-ACHEM-090) so the fixed,
# order-sensitive CNS-like/kinase-inhibitor-like boundaries are documented in
# one place instead of as inline magic numbers.
CNS_LIKE_TPSA_MAX = 90
CNS_LIKE_MOLLOGP_MIN, CNS_LIKE_MOLLOGP_MAX = 2.0, 5.0
KINASE_INHIBITOR_LIKE_MOLWT_MIN = 400
KINASE_INHIBITOR_LIKE_AROMATIC_RING_COUNT_MIN = 3
LIMITATION_LABEL_KEY = "bioactivity_classifier_heuristic_limitation"
LIMITATION_LABEL_TEXT = {
    "en": "Heuristic only: not a ChEMBL-trained or experimentally validated bioactivity classifier.",
    "ja": (
        "ヒューリスティックのみ: ChEMBLで学習済みでも実験的に検証済みでもない"
        "生物活性分類器ではない。"
    ),
}


# @id CODE-ACHEM-920
# @implements REQ-ACHEM-003 REQ-ACHEM-090
# @design DES-ACHEM-002
def _bioactivity_classification_validator(params: dict) -> dict:
    if "smiles" not in params:
        return fail("smiles", "is required")
    if parse_smiles(params["smiles"]) is None:
        return fail("smiles", "must parse to a valid RDKit molecule")
    return ok()


register_validator(_MODULE_NAME, _bioactivity_classification_validator)


# @id CODE-ACHEM-090
# @implements REQ-ACHEM-090
# @design DES-ACHEM-090
def run_bioactivity_classification(smiles: str) -> dict:
    """Assign the fixed-order heuristic label for ``smiles``."""
    mol = parse_smiles(smiles)
    if mol is None:
        raise ValueError("smiles must already be validated by the handler wrapper")
    descriptors = compute_descriptors(mol)
    aromatic_ring_count = int(rdMolDescriptors.CalcNumAromaticRings(mol))

    if (
        descriptors["tpsa"] < CNS_LIKE_TPSA_MAX
        and CNS_LIKE_MOLLOGP_MIN <= descriptors["mol_logp"] <= CNS_LIKE_MOLLOGP_MAX
    ):
        label = "CNS_like"
    elif (
        descriptors["mol_wt"] > KINASE_INHIBITOR_LIKE_MOLWT_MIN
        and aromatic_ring_count >= KINASE_INHIBITOR_LIKE_AROMATIC_RING_COUNT_MIN
    ):
        label = "kinase_inhibitor_like"
    else:
        label = "other"

    return {
        "label": label,
        "tpsa": descriptors["tpsa"],
        "mol_logp": descriptors["mol_logp"],
        "mol_wt": descriptors["mol_wt"],
        "aromatic_ring_count": aromatic_ring_count,
        "limitation_label_key": LIMITATION_LABEL_KEY,
    }
