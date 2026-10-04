"""Protein docking-score heuristic module (DES-ASTRUCT-030 / REQ-ASTRUCT-030)."""

from __future__ import annotations

from collections.abc import Mapping
from numbers import Integral

from ai_structural_biology_scientist.validation import fail, is_finite_real, register_validator

_MODULE_NAME = "protein-protein-docking-score"
_REFERENCE_INTERFACE_AREA_A2 = 800.0

LIMITATION_LABEL_KEY = "protein_docking_score_heuristic_limitation"
LIMITATION_LABEL_TEXT = {
    "en": (
        "Heuristic only: a fixed-formula geometric/compositional complementarity "
        "score, not a physically accurate protein-protein docking simulation (no "
        "3D structure, no energy function)."
    ),
    "ja": (
        "ヒューリスティックのみ：固定式の幾何・組成補完性スコアであり、"
        "物理的に正確なタンパク質間ドッキングシミュレーションではない"
        "（3D 構造なし、エネルギー関数なし）。"
    ),
}


def _is_non_negative_int(value) -> bool:
    return isinstance(value, Integral) and not isinstance(value, bool) and value >= 0


def _validate_partner(params: dict, name: str) -> dict:
    partner = params.get(name)
    if not isinstance(partner, Mapping):
        return fail(name, "must be a dict")
    for key in ("hydrophobic_count", "charged_count"):
        if key not in partner:
            return fail(f"{name}.{key}", "is required")
        if not _is_non_negative_int(partner[key]):
            return fail(f"{name}.{key}", "must be a finite non-negative integer")
    return {"ok": True}


def _protein_docking_score_validator(params: dict) -> dict:
    """DES-ASTRUCT-002 registered atomic validator for this module."""
    for name in ("partner_a", "partner_b"):
        if name not in params:
            return fail(name, "is required")
        partner_validation = _validate_partner(params, name)
        if not partner_validation["ok"]:
            return partner_validation

    interface_area_a2 = params.get("interface_area_A2")
    if not is_finite_real(interface_area_a2) or interface_area_a2 <= 0:
        return fail("interface_area_A2", "must be > 0")

    return {"ok": True}


register_validator(_MODULE_NAME, _protein_docking_score_validator)


# @id CODE-ASTRUCT-030
# @implements REQ-ASTRUCT-030
# @design DES-ASTRUCT-030
def run_protein_docking_score(
    partner_a: dict,
    partner_b: dict,
    interface_area_A2: float,
) -> dict:
    """Compute the fixed-formula protein docking-score heuristic."""
    validation = _protein_docking_score_validator(
        {
            "partner_a": partner_a,
            "partner_b": partner_b,
            "interface_area_A2": interface_area_A2,
        }
    )
    if not validation["ok"]:
        raise ValueError("parameters must already be validated by the handler wrapper")

    size_term = min(
        1.0,
        max(
            0.0,
            1.0
            - abs(interface_area_A2 - _REFERENCE_INTERFACE_AREA_A2) / _REFERENCE_INTERFACE_AREA_A2,
        ),
    )
    hydrophobic_complementarity = min(
        partner_a["hydrophobic_count"], partner_b["hydrophobic_count"]
    ) / max(1, partner_a["hydrophobic_count"] + partner_b["hydrophobic_count"])
    charge_complementarity = min(partner_a["charged_count"], partner_b["charged_count"]) / max(
        1, partner_a["charged_count"] + partner_b["charged_count"]
    )
    score = 0.5 * size_term + 0.25 * hydrophobic_complementarity + 0.25 * charge_complementarity

    return {
        "size_term": size_term,
        "hydrophobic_complementarity": hydrophobic_complementarity,
        "charge_complementarity": charge_complementarity,
        "score": score,
        "limitation_label_key": LIMITATION_LABEL_KEY,
    }
