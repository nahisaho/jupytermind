"""CRISPR guide off-target Hamming-distance heuristic module (DES-AGENOM-101 / REQ-AGENOM-101)."""

from __future__ import annotations

from ai_genomics_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "crispr-off-target-score"
_DNA_BASES = frozenset({"A", "C", "G", "T"})


def _is_dna_alphabet(value: object) -> bool:
    return isinstance(value, str) and value.isupper() and value and set(value).issubset(_DNA_BASES)


def _crispr_off_target_score_validator(params: dict) -> dict:
    """DES-AGENOM-002 registered atomic validator for this module."""
    guide = params.get("guide")
    candidate = params.get("candidate")

    if not isinstance(guide, str) or guide == "":
        return fail("guide", "must be non-empty")
    if not isinstance(candidate, str) or candidate == "":
        return fail("candidate", "must be non-empty")
    if not _is_dna_alphabet(guide):
        return fail("guide", "must be uppercase over {A,C,G,T}")
    if not _is_dna_alphabet(candidate):
        return fail("candidate", "must be uppercase over {A,C,G,T}")
    if len(guide) != len(candidate):
        return fail("guide", "must be equal length")
    return ok()


register_validator(_MODULE_NAME, _crispr_off_target_score_validator)


# @id CODE-AGENOM-101
# @implements REQ-AGENOM-101
# @design DES-AGENOM-101
def run_crispr_off_target_score(guide: str, candidate: str) -> dict:
    """Compute the Hamming-distance-based off-target mismatch heuristic score."""
    mismatches = sum(1 for base_a, base_b in zip(guide, candidate, strict=True) if base_a != base_b)
    score = 1 / (1 + mismatches)
    return {"mismatches": mismatches, "score": score}
