"""Variant pathogenicity heuristic module (DES-AGENOM-070 / REQ-AGENOM-070)."""

from __future__ import annotations

from ai_genomics_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "variant-pathogenicity"

_AMINO_ACID_ORDER = [
    "A",
    "R",
    "N",
    "D",
    "C",
    "Q",
    "E",
    "G",
    "H",
    "I",
    "L",
    "K",
    "M",
    "F",
    "P",
    "S",
    "T",
    "W",
    "Y",
    "V",
]
_STANDARD_AMINO_ACIDS = frozenset(_AMINO_ACID_ORDER)

# Standard published BLOSUM62 substitution matrix (symmetric, 20x20),
# row/column order matching _AMINO_ACID_ORDER exactly, per ADR-0108.
_BLOSUM62_ROWS = [
    [4, -1, -2, -2, 0, -1, -1, 0, -2, -1, -1, -1, -1, -2, -1, 1, 0, -3, -2, 0],
    [-1, 5, 0, -2, -3, 1, 0, -2, 0, -3, -2, 2, -1, -3, -2, -1, -1, -3, -2, -3],
    [-2, 0, 6, 1, -3, 0, 0, 0, 1, -3, -3, 0, -2, -3, -2, 1, 0, -4, -2, -3],
    [-2, -2, 1, 6, -3, 0, 2, -1, -1, -3, -4, -1, -3, -3, -1, 0, -1, -4, -3, -3],
    [0, -3, -3, -3, 9, -3, -4, -3, -3, -1, -1, -3, -1, -2, -3, -1, -1, -2, -2, -1],
    [-1, 1, 0, 0, -3, 5, 2, -2, 0, -3, -2, 1, 0, -3, -1, 0, -1, -2, -1, -2],
    [-1, 0, 0, 2, -4, 2, 5, -2, 0, -3, -3, 1, -2, -3, -1, 0, -1, -3, -2, -2],
    [0, -2, 0, -1, -3, -2, -2, 6, -2, -4, -4, -2, -3, -3, -2, 0, -2, -2, -3, -3],
    [-2, 0, 1, -1, -3, 0, 0, -2, 8, -3, -3, -1, -2, -1, -2, -1, -2, -2, 2, -3],
    [-1, -3, -3, -3, -1, -3, -3, -4, -3, 4, 2, -3, 1, 0, -3, -2, -1, -3, -1, 3],
    [-1, -2, -3, -4, -1, -2, -3, -4, -3, 2, 4, -2, 2, 0, -3, -2, -1, -2, -1, 1],
    [-1, 2, 0, -1, -3, 1, 1, -2, -1, -3, -2, 5, -1, -3, -1, 0, -1, -3, -2, -2],
    [-1, -1, -2, -3, -1, 0, -2, -3, -2, 1, 2, -1, 5, 0, -2, -1, -1, -1, -1, 1],
    [-2, -3, -3, -3, -2, -3, -3, -3, -1, 0, 0, -3, 0, 6, -4, -2, -2, 1, 3, -1],
    [-1, -2, -2, -1, -3, -1, -1, -2, -2, -3, -3, -1, -2, -4, 7, -1, -1, -4, -3, -2],
    [1, -1, 1, 0, -1, 0, 0, 0, -1, -2, -2, 0, -1, -2, -1, 4, 1, -3, -2, -2],
    [0, -1, 0, -1, -1, -1, -1, -2, -2, -1, -1, -1, -1, -2, -1, 1, 5, -2, -2, 0],
    [-3, -3, -4, -4, -2, -2, -3, -2, -2, -3, -2, -3, -1, 1, -4, -3, -2, 11, 2, -3],
    [-2, -2, -2, -3, -2, -1, -2, -3, 2, -1, -1, -2, -1, 3, -3, -2, -2, 2, 7, -1],
    [0, -3, -3, -3, -1, -2, -2, -3, -3, 3, 1, -2, 1, -1, -2, -2, 0, -3, -1, 4],
]
_BLOSUM62 = {
    (row_aa, col_aa): _BLOSUM62_ROWS[row_index][col_index]
    for row_index, row_aa in enumerate(_AMINO_ACID_ORDER)
    for col_index, col_aa in enumerate(_AMINO_ACID_ORDER)
}

_TIER_THRESHOLDS = [
    (0.3, "benign"),
    (0.5, "likely_benign"),
    (0.7, "uncertain_significance"),
    (0.85, "likely_pathogenic"),
]


def _variant_pathogenicity_validator(params: dict) -> dict:
    """DES-AGENOM-002 registered atomic validator for this module."""
    ref_aa = params.get("ref_aa")
    alt_aa = params.get("alt_aa")
    conservation_score = params.get("conservation_score")
    in_functional_domain = params.get("in_functional_domain")

    if not isinstance(ref_aa, str) or ref_aa not in _STANDARD_AMINO_ACIDS:
        return fail("ref_aa", "must be one of the 20 standard single-letter amino acid codes")
    if not isinstance(alt_aa, str) or alt_aa not in _STANDARD_AMINO_ACIDS:
        return fail("alt_aa", "must be one of the 20 standard single-letter amino acid codes")
    if alt_aa == ref_aa:
        return fail("alt_aa", "alt_aa must differ from ref_aa")
    if (
        not isinstance(conservation_score, float)
        or isinstance(conservation_score, bool)
        or not (0 <= conservation_score <= 1)
    ):
        return fail("conservation_score", "must be a float in the closed interval [0, 1]")
    if not isinstance(in_functional_domain, bool):
        return fail("in_functional_domain", "must be a boolean")

    return ok()


register_validator(_MODULE_NAME, _variant_pathogenicity_validator)


def _classify(score: float) -> str:
    for threshold, tier in _TIER_THRESHOLDS:
        if score < threshold:
            return tier
    return "pathogenic"


# @id CODE-AGENOM-070
# @implements REQ-AGENOM-070
# @design DES-AGENOM-070
def run_variant_pathogenicity(
    ref_aa: str, alt_aa: str, conservation_score: float, in_functional_domain: bool
) -> dict:
    """Compute the fixed BLOSUM62 + weighted-sum pathogenicity heuristic score."""
    blosum_score = _BLOSUM62[(ref_aa, alt_aa)]
    dissimilarity = min(max((3 - blosum_score) / 7, 0.0), 1.0)
    domain_bonus = 0.15 if in_functional_domain else 0.0
    pathogenicity_score = min(
        max(0.5 * dissimilarity + 0.35 * conservation_score + domain_bonus, 0.0), 1.0
    )
    return {
        "ref_aa": ref_aa,
        "alt_aa": alt_aa,
        "blosum_score": blosum_score,
        "pathogenicity_score": pathogenicity_score,
        "classification": _classify(pathogenicity_score),
    }
