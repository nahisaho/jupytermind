"""ACMG/AMP germline variant classification rule engine (DES-AGENOM-090 / REQ-AGENOM-090).

Pure function module: no network, database, or ML-model call.
"""

from __future__ import annotations

from ai_genomics_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "acmg-amp-classification"

_PVS = frozenset({"PVS1"})
_PS = frozenset({"PS1", "PS2", "PS3", "PS4"})
_PM = frozenset({"PM1", "PM2", "PM3", "PM4", "PM5", "PM6"})
_PP = frozenset({"PP1", "PP2", "PP3", "PP4", "PP5"})
_BA = frozenset({"BA1"})
_BS = frozenset({"BS1", "BS2", "BS3", "BS4"})
_BP = frozenset({"BP1", "BP2", "BP3", "BP4", "BP5", "BP6", "BP7"})

_ALL_CODES = _PVS | _PS | _PM | _PP | _BA | _BS | _BP


def _acmg_classification_validator(params: dict) -> dict:
    """DES-AGENOM-002 registered atomic validator for this module."""
    criteria = params.get("criteria")

    if not isinstance(criteria, list) or len(criteria) == 0:
        return fail("criteria", "must be a non-empty list")
    if not all(isinstance(code, str) for code in criteria):
        return fail("criteria", "each must be one of the 28 standard ACMG/AMP criterion codes")
    if any(code not in _ALL_CODES for code in criteria):
        return fail("criteria", "each must be one of the 28 standard ACMG/AMP criterion codes")
    if len(set(criteria)) != len(criteria):
        return fail("criteria", "must not contain duplicate codes")

    return ok()


register_validator(_MODULE_NAME, _acmg_classification_validator)


def _counts(criteria: list[str]) -> dict[str, int]:
    criteria_set = set(criteria)
    return {
        "n_pvs": len(criteria_set & _PVS),
        "n_ps": len(criteria_set & _PS),
        "n_pm": len(criteria_set & _PM),
        "n_pp": len(criteria_set & _PP),
        "n_ba": len(criteria_set & _BA),
        "n_bs": len(criteria_set & _BS),
        "n_bp": len(criteria_set & _BP),
    }


def _first_pathogenic_match(c: dict[str, int]) -> str | None:
    rules = [
        ("P1", c["n_pvs"] >= 1 and c["n_ps"] >= 1),
        ("P2", c["n_pvs"] >= 1 and c["n_pm"] >= 2),
        ("P3", c["n_pvs"] >= 1 and c["n_pm"] >= 1 and c["n_pp"] >= 1),
        ("P4", c["n_pvs"] >= 1 and c["n_pp"] >= 2),
        ("P5", c["n_ps"] >= 2),
        ("P6", c["n_ps"] >= 1 and c["n_pm"] >= 3),
        ("P7", c["n_ps"] >= 1 and c["n_pm"] >= 2 and c["n_pp"] >= 2),
        ("P8", c["n_ps"] >= 1 and c["n_pm"] >= 1 and c["n_pp"] >= 4),
    ]
    for rule_id, matched in rules:
        if matched:
            return rule_id
    return None


def _first_likely_pathogenic_match(c: dict[str, int]) -> str | None:
    rules = [
        ("LP1", c["n_pvs"] >= 1 and c["n_pm"] >= 1),
        ("LP2", c["n_ps"] >= 1 and 1 <= c["n_pm"] <= 2),
        ("LP3", c["n_ps"] >= 1 and c["n_pp"] >= 2),
        ("LP4", c["n_pm"] >= 3),
        ("LP5", c["n_pm"] >= 2 and c["n_pp"] >= 2),
        ("LP6", c["n_pm"] >= 1 and c["n_pp"] >= 4),
    ]
    for rule_id, matched in rules:
        if matched:
            return rule_id
    return None


def _first_benign_match(c: dict[str, int]) -> str | None:
    rules = [
        ("B1", c["n_ba"] >= 1),
        ("B2", c["n_bs"] >= 2),
    ]
    for rule_id, matched in rules:
        if matched:
            return rule_id
    return None


def _first_likely_benign_match(c: dict[str, int]) -> str | None:
    rules = [
        ("LB1", c["n_bs"] >= 1 and c["n_bp"] >= 1),
        ("LB2", c["n_bp"] >= 2),
    ]
    for rule_id, matched in rules:
        if matched:
            return rule_id
    return None


# @id CODE-AGENOM-090
# @implements REQ-AGENOM-090
# @design DES-AGENOM-090
def run_acmg_classification(criteria: list[str]) -> dict:
    """Apply the Richards et al. (2015) Table 5 ACMG/AMP combining rules.

    Computational aid only — not a clinical diagnosis or recommendation
    (REQ-AGENOM-090). Operates purely on caller-supplied evidence-code
    strings; it performs no variant annotation lookup of its own.
    """
    counts = _counts(criteria)

    pathogenic_side = _first_pathogenic_match(counts)
    if pathogenic_side is None:
        pathogenic_side = _first_likely_pathogenic_match(counts)

    benign_side = _first_benign_match(counts)
    if benign_side is None:
        benign_side = _first_likely_benign_match(counts)

    if pathogenic_side is not None and benign_side is not None:
        return {
            "criteria": criteria,
            "classification": "uncertain_significance",
            "matched_rule": "conflicting_criteria",
        }

    if pathogenic_side is not None:
        classification = "pathogenic" if pathogenic_side.startswith("P") else "likely_pathogenic"
        return {
            "criteria": criteria,
            "classification": classification,
            "matched_rule": pathogenic_side,
        }

    if benign_side is not None:
        classification = "benign" if benign_side in ("B1", "B2") else "likely_benign"
        return {
            "criteria": criteria,
            "classification": classification,
            "matched_rule": benign_side,
        }

    return {
        "criteria": criteria,
        "classification": "uncertain_significance",
        "matched_rule": None,
    }
