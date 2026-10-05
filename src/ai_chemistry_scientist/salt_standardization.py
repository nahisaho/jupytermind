"""SMILES salt removal / structure standardization module (DES-ACHEM-100 / REQ-ACHEM-100)."""

from __future__ import annotations

from rdkit import Chem

from ai_chemistry_scientist.molecular_descriptors import parse_smiles
from ai_chemistry_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "salt-removal"

LIMITATION_LABEL_KEY = "salt_removal_heuristic_limitation"
LIMITATION_LABEL_TEXT = {
    "en": (
        "Heuristic only: treats every disconnected fragment except the one "
        "with the greatest heavy-atom count as removable salt/solvent; not "
        "always chemically correct (e.g. for a genuine covalent "
        "multi-component cocrystal)."
    ),
    "ja": (
        "ヒューリスティックのみ: 最大重原子数を持つフラグメント以外のすべての"
        "分離フラグメントを除去可能な塩・溶媒として扱うが、常に化学的に"
        "正しいとは限らない（例: 真の共有結合性多成分共結晶の場合）。"
    ),
}


# @id CODE-ACHEM-921
# @implements REQ-ACHEM-003 REQ-ACHEM-100
# @design DES-ACHEM-002
def _salt_removal_validator(params: dict) -> dict:
    """Reject a missing/unparseable/dummy-atom ``smiles`` via `parse_smiles`.

    Unlike `structure_format_conversion._parse_structure`'s Molblock parser,
    `parse_smiles` never needs an explicit zero-atom-molecule guard: RDKit's
    SMILES parser rejects the only syntactically valid empty input (the
    empty string) before reaching `Chem.MolFromSmiles` (the leading
    not-`smiles` check), so every string it accepts yields at least one atom.

    The required-key check runs first so a missing ``smiles`` parameter is
    reported as a missing-parameter error rather than a parse failure.
    """
    if "smiles" not in params:
        return fail("smiles", "is required")
    if parse_smiles(params["smiles"]) is None:
        return fail("smiles", "must parse to a valid RDKit molecule")
    return ok()


register_validator(_MODULE_NAME, _salt_removal_validator)


def _fragment_sort_key(fragment) -> tuple[int, str]:
    """`(-heavy_atom_count, canonical_smiles)` ascending (REQ-ACHEM-100/ADR-0105)."""
    return (-fragment.GetNumHeavyAtoms(), Chem.MolToSmiles(fragment))


# @id CODE-ACHEM-100
# @implements REQ-ACHEM-100
# @design DES-ACHEM-100
def run_salt_removal(smiles: str) -> dict:
    """Select the dominant fragment of ``smiles`` and report the rest as removed.

    Fragment selection follows the fixed sort key
    ``(-heavy_atom_count, canonical_smiles)`` (ADR-0105), not RDKit's
    built-in ``rdMolStandardize.LargestFragmentChooser`` heuristic.
    """
    mol = parse_smiles(smiles)
    if mol is None:
        raise ValueError("smiles must already be validated by the handler wrapper")

    fragments = Chem.GetMolFrags(mol, asMols=True, sanitizeFrags=False)
    ranked = sorted(fragments, key=_fragment_sort_key)
    ranked_smiles = [Chem.MolToSmiles(fragment) for fragment in ranked]

    return {
        "standardized_smiles": ranked_smiles[0],
        "removed_fragments": ranked_smiles[1:],
        "fragments_removed": len(ranked_smiles) > 1,
        "limitation_label_key": LIMITATION_LABEL_KEY,
    }
