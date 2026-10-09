"""miRNA canonical-7mer-seed target-site prediction module (DES-AGENOM-120 / REQ-AGENOM-120)."""

from __future__ import annotations

from ai_genomics_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "mirna-target-prediction"
_RNA_BASES = frozenset({"A", "C", "G", "U"})
_DNA_BASES = frozenset({"A", "C", "G", "T"})
_DNA_COMPLEMENT = {"A": "T", "C": "G", "G": "C", "T": "A"}
_SEED_START = 1
_SEED_END = 8


def _is_rna_string(value: object) -> bool:
    return isinstance(value, str) and value.isupper() and value and set(value).issubset(_RNA_BASES)


def _is_dna_string(value: object) -> bool:
    return isinstance(value, str) and value.isupper() and value and set(value).issubset(_DNA_BASES)


def _mirna_target_prediction_validator(params: dict) -> dict:
    """DES-AGENOM-002 registered atomic validator for this module."""
    mirna = params.get("mirna")
    utr = params.get("utr")

    if not isinstance(mirna, str) or len(mirna) < 8:
        return fail("mirna", "must be at least 8 nucleotides")
    if not _is_rna_string(mirna):
        return fail("mirna", "must be uppercase over {A,C,G,U}")
    if not isinstance(utr, str) or utr == "":
        return fail("utr", "must be non-empty")
    if not _is_dna_string(utr):
        return fail("utr", "must be uppercase over {A,C,G,T}")
    return ok()


register_validator(_MODULE_NAME, _mirna_target_prediction_validator)


def _reverse_complement_dna(sequence: str) -> str:
    return "".join(_DNA_COMPLEMENT[base] for base in reversed(sequence))


# @id CODE-AGENOM-120
# @implements REQ-AGENOM-120
# @design DES-AGENOM-120
def run_mirna_target_prediction(mirna: str, utr: str) -> dict:
    """Derive the canonical 7mer seed and scan the 3-prime UTR for overlapping matches."""
    seed_rna = mirna[_SEED_START:_SEED_END]
    seed_dna = seed_rna.replace("U", "T")
    seed = _reverse_complement_dna(seed_dna)

    match_positions = [
        index for index in range(len(utr) - len(seed) + 1) if utr[index : index + len(seed)] == seed
    ]

    return {"seed": seed, "match_positions": match_positions}
