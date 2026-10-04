"""Structural alert screening module (DES-ACHEM-070 / REQ-ACHEM-070)."""

from __future__ import annotations

from rdkit import Chem

from ai_chemistry_scientist.molecular_descriptors import parse_smiles
from ai_chemistry_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "structural-alerts"
ALERT_SMARTS = (
    ("nitro_group", "[NX3](=O)=O"),
    ("aldehyde", "[CX3H1](=O)"),
    ("michael_acceptor_enone", "C=CC(=O)"),
    ("epoxide", "C1OC1"),
    ("free_thiol", "[SX2H]"),
)
# Pre-compiled once at import time (DES-ACHEM-070's fixed alert list never
# changes at runtime), rather than re-parsing every SMARTS pattern string on
# every call; this also fails fast at import if a pattern is ever malformed
# instead of silently returning a ``None`` query molecule at call time.
_ALERT_QUERIES = tuple((name, Chem.MolFromSmarts(smarts)) for name, smarts in ALERT_SMARTS)
LIMITATION_LABEL_KEY = "structural_alerts_heuristic_limitation"
LIMITATION_LABEL_TEXT = {
    "en": "Heuristic only: a small fixed illustrative SMARTS alert list, not the validated PAINS/Brenk filter catalog.",
    "ja": (
        "ヒューリスティックのみ: 固定の小規模な例示用SMARTSアラート一覧であり、"
        "検証済みのPAINS/Brenkフィルタ・カタログではない。"
    ),
}


# @id CODE-ACHEM-918
# @implements REQ-ACHEM-003 REQ-ACHEM-070
# @design DES-ACHEM-002
def _structural_alerts_validator(params: dict) -> dict:
    if "smiles" not in params:
        return fail("smiles", "is required")
    if parse_smiles(params["smiles"]) is None:
        return fail("smiles", "must parse to a valid RDKit molecule")
    return ok()


register_validator(_MODULE_NAME, _structural_alerts_validator)


# @id CODE-ACHEM-070
# @implements REQ-ACHEM-070
# @design DES-ACHEM-070
def run_structural_alerts(smiles: str) -> dict:
    """Match the fixed SMARTS alert list against ``smiles``."""
    mol = parse_smiles(smiles)
    if mol is None:
        raise ValueError("smiles must already be validated by the handler wrapper")
    alerts_matched = [name for name, query in _ALERT_QUERIES if mol.HasSubstructMatch(query)]
    return {
        "alerts_matched": alerts_matched,
        "alert_count": len(alerts_matched),
        "limitation_label_key": LIMITATION_LABEL_KEY,
    }
