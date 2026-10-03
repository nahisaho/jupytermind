"""Simplified docking-score heuristic module (DES-ACHEM-050 / REQ-ACHEM-050)."""

from __future__ import annotations

import math

from ai_chemistry_scientist.molecular_descriptors import parse_smiles
from ai_chemistry_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "docking-score"
_VOLUME_PER_HEAVY_ATOM_A3 = 15.0

#: The handler wrapper of DES-ACHEM-001 substitutes this key for the
#: `language`-specific text before `record_run` (REQ-ACHEM-050 Constraints).
LIMITATION_LABEL_KEY = "docking_heuristic_limitation"
LIMITATION_LABEL_TEXT = {
    "en": (
        "Heuristic only: not a physically accurate docking simulation (no 3D "
        "conformer generation, no energy function)."
    ),
    "ja": (
        "ヒューリスティックのみ: 物理的に正確なドッキングシミュレーションでは"
        "ありません（3D配座生成・エネルギー関数なし）。"
    ),
}


def _is_finite_non_negative_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _docking_score_validator(params: dict) -> dict:
    """DES-ACHEM-002 registered atomic validator for this module."""
    if "ligand_smiles" not in params:
        return fail("ligand_smiles", "is required")
    if "pocket_spec" not in params:
        return fail("pocket_spec", "is required")
    if parse_smiles(params["ligand_smiles"]) is None:
        return fail("smiles", "must parse to a valid RDKit molecule")
    pocket_spec = params["pocket_spec"]
    if not isinstance(pocket_spec, dict):
        return fail("pocket_spec", "must be a dict")
    for key in ("pocket_volume_A3", "pocket_hba_sites", "pocket_hbd_sites"):
        if key not in pocket_spec:
            return fail(key, "is required")
    pocket_volume_a3 = pocket_spec["pocket_volume_A3"]
    if (
        not isinstance(pocket_volume_a3, (int, float))
        or isinstance(pocket_volume_a3, bool)
        or not math.isfinite(pocket_volume_a3)
        or pocket_volume_a3 <= 0
    ):
        return fail("pocket_volume_A3", "must be a finite number > 0")
    if not _is_finite_non_negative_int(pocket_spec["pocket_hba_sites"]):
        return fail("pocket_hba_sites", "must be a finite non-negative integer")
    if not _is_finite_non_negative_int(pocket_spec["pocket_hbd_sites"]):
        return fail("pocket_hbd_sites", "must be a finite non-negative integer")
    return ok()


register_validator(_MODULE_NAME, _docking_score_validator)


# @id CODE-ACHEM-050
# @implements REQ-ACHEM-050
# @design DES-ACHEM-050
def run_docking_score(ligand_smiles: str, pocket_spec: dict) -> dict:
    """Compute the fixed-formula heuristic docking score for the ligand-pocket pair.

    Receives ``ligand_smiles``/``pocket_spec`` already validated atomically
    by its handler wrapper; performs no revalidation of its own.
    """
    from rdkit.Chem import Descriptors

    mol = parse_smiles(ligand_smiles)
    if mol is None:
        raise ValueError("ligand_smiles must already be validated by the handler wrapper")
    heavy_atom_count = mol.GetNumHeavyAtoms()
    ligand_hbd = int(Descriptors.NumHDonors(mol))
    ligand_hba = int(Descriptors.NumHAcceptors(mol))

    pocket_volume_a3 = pocket_spec["pocket_volume_A3"]
    pocket_hba_sites = pocket_spec["pocket_hba_sites"]
    pocket_hbd_sites = pocket_spec["pocket_hbd_sites"]

    ligand_volume = heavy_atom_count * _VOLUME_PER_HEAVY_ATOM_A3
    size_fit = min(1.0, max(0.0, 1 - abs(ligand_volume - pocket_volume_a3) / pocket_volume_a3))
    matched_pairs = min(ligand_hbd, pocket_hba_sites) + min(ligand_hba, pocket_hbd_sites)
    hbond_fit = matched_pairs / max(1, ligand_hbd + ligand_hba)
    score = 0.5 * size_fit + 0.5 * hbond_fit

    return {
        "score": score,
        "size_fit": size_fit,
        "hbond_fit": hbond_fit,
        "limitation_label_key": LIMITATION_LABEL_KEY,
    }
