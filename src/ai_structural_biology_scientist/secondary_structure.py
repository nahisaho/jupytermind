"""Secondary-structure heuristic module (DES-ASTRUCT-010 / REQ-ASTRUCT-010)."""

from __future__ import annotations

from ai_structural_biology_scientist.validation import (
    fail,
    register_validator,
    validate_uppercase_sequence,
)

_MODULE_NAME = "secondary-structure-heuristic"
_PROPENSITIES = {
    "A": (1.42, 0.83, 0.75),
    "R": (0.98, 0.93, 1.09),
    "N": (0.67, 0.89, 1.44),
    "D": (1.01, 0.54, 1.45),
    "C": (0.70, 1.19, 1.11),
    "Q": (1.11, 1.10, 0.79),
    "E": (1.51, 0.37, 1.12),
    "G": (0.57, 0.75, 1.68),
    "H": (1.00, 0.87, 1.13),
    "I": (1.08, 1.60, 0.32),
    "L": (1.21, 1.30, 0.49),
    "K": (1.16, 0.74, 1.10),
    "M": (1.45, 1.05, 0.50),
    "F": (1.13, 1.38, 0.49),
    "P": (0.57, 0.55, 1.88),
    "S": (0.77, 0.75, 1.48),
    "T": (0.83, 1.19, 0.98),
    "W": (1.08, 1.37, 0.55),
    "Y": (0.69, 1.47, 0.84),
    "V": (1.06, 1.70, 0.41),
}
_CLASS_ORDER = ("H", "E", "C")

LIMITATION_LABEL_KEY = "secondary_structure_heuristic_limitation"
LIMITATION_LABEL_TEXT = {
    "en": (
        "Heuristic only: a fixed illustrative per-residue propensity lookup, not a "
        "validated secondary-structure predictor (no windowing, no real Chou-Fasman "
        "statistics)."
    ),
    "ja": (
        "ヒューリスティックのみ：固定の説明用残基別 propensity lookup であり、"
        "検証済みの二次構造予測器ではない（windowing なし、実際の Chou-Fasman "
        "統計なし）。"
    ),
}


def _secondary_structure_validator(params: dict) -> dict:
    """DES-ASTRUCT-002 registered atomic validator for this module."""
    if "sequence" not in params:
        return fail("sequence", "is required")
    return validate_uppercase_sequence(params)


register_validator(_MODULE_NAME, _secondary_structure_validator)


# @id CODE-ASTRUCT-010
# @implements REQ-ASTRUCT-010
# @design DES-ASTRUCT-010
def run_secondary_structure(sequence: str) -> dict:
    """Compute the fixed-table structural assignment for ``sequence``."""
    sequence_validation = validate_uppercase_sequence({"sequence": sequence})
    if not sequence_validation["ok"]:
        raise ValueError("sequence must already be validated by the handler wrapper")

    residues = []
    classes = []
    for position, residue in enumerate(sequence):
        helix, sheet, coil = _PROPENSITIES[residue]
        propensity_by_class = {"H": helix, "E": sheet, "C": coil}
        # Documented fixed tie-break order H > E > C: ``_CLASS_ORDER`` is
        # iterated in that exact order and ``max`` keeps the first maximal
        # element on ties, so this is equivalent to, but clearer than, an
        # explicit negated-index secondary sort key.
        assigned_class = max(
            _CLASS_ORDER,
            key=lambda klass: propensity_by_class[klass],
        )
        residues.append({"position": position, "residue": residue, "class": assigned_class})
        classes.append(assigned_class)

    secondary_structure = "".join(classes)
    length = len(sequence)
    return {
        "residues": residues,
        "secondary_structure": secondary_structure,
        "helix_fraction": secondary_structure.count("H") / length,
        "sheet_fraction": secondary_structure.count("E") / length,
        "coil_fraction": secondary_structure.count("C") / length,
        "limitation_label_key": LIMITATION_LABEL_KEY,
    }
