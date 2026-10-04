"""Splice-site strength heuristic module (DES-AGENOM-030 / REQ-AGENOM-030)."""

from __future__ import annotations

import math

from ai_genomics_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "splice-site-strength"
_DNA_BASES = frozenset({"A", "C", "G", "T"})

LIMITATION_LABEL_TEXT = {
    "en": (
        "Heuristic only: a fixed illustrative position-weight scoring scheme, not a "
        "validated splice-site predictor (not SpliceAI, not based on real "
        "splice-site frequency data)."
    ),
    "ja": (
        "ヒューリスティックのみ：これは固定された例示用の"
        " position-weight スコアリング方式であり、検証済みのスプライス"
        "部位予測器ではない（SpliceAI ではなく、実際のスプライス部位"
        "頻度データにも基づかない）。"
    ),
}

_PFM = (
    {"A": 0.30, "C": 0.20, "G": 0.25, "T": 0.25},
    {"A": 0.60, "C": 0.15, "G": 0.15, "T": 0.10},
    {"A": 0.15, "C": 0.15, "G": 0.60, "T": 0.10},
    {"A": 0.00, "C": 0.00, "G": 1.00, "T": 0.00},
    {"A": 0.00, "C": 0.00, "G": 0.00, "T": 1.00},
    {"A": 0.55, "C": 0.05, "G": 0.35, "T": 0.05},
    {"A": 0.70, "C": 0.10, "G": 0.10, "T": 0.10},
    {"A": 0.08, "C": 0.05, "G": 0.80, "T": 0.07},
    {"A": 0.15, "C": 0.20, "G": 0.20, "T": 0.45},
)


def _is_dna_string(value: object) -> bool:
    return isinstance(value, str) and value.isupper() and value and set(value).issubset(_DNA_BASES)


def _splice_site_validator(params: dict) -> dict:
    """DES-AGENOM-002 registered atomic validator for this module."""
    window = params.get("window")
    if not _is_dna_string(window):
        return fail("window", "must be a non-empty uppercase DNA string over {A,C,G,T}")
    if len(window) != 9:
        return fail("window", "must be exactly 9 characters")
    if window[3:5] != "GT":
        return fail("window", "position 0,+1 must be the canonical GT dinucleotide")
    return ok()


register_validator(_MODULE_NAME, _splice_site_validator)


# @id CODE-AGENOM-030
# @implements REQ-AGENOM-030
# @design DES-AGENOM-030
def run_splice_site_scoring(window: str) -> dict:
    """Score a validated 9-base donor-site window with the fixed illustrative PFM."""
    score_bits = 0.0
    for index, base in enumerate(window):
        score_bits += math.log2(_PFM[index][base] / 0.25)
    return {"window": window, "score_bits": score_bits, "canonical_site": True}
