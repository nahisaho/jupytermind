"""Sequence feature analysis module (DES-AGENOM-010 / REQ-AGENOM-010)."""

from __future__ import annotations

from ai_genomics_scientist.validation import (
    fail,
    ok,
    register_batch_item_validator,
    validate_batch_item,
)

_MODULE_NAME = "sequence-features"
_DNA_BASES = frozenset({"A", "C", "G", "T"})
_STOP_CODONS = frozenset({"TAA", "TAG", "TGA"})
_SEQUENCE_CONSTRAINT = "must be a non-empty uppercase DNA string over {A,C,G,T} with length >= 3"


def _is_valid_dna_sequence(sequence: str, *, min_length: int) -> bool:
    return (
        isinstance(sequence, str)
        and len(sequence) >= min_length
        and sequence.isupper()
        and set(sequence).issubset(_DNA_BASES)
    )


def _sequence_features_batch_item_validator(item_params: dict) -> dict:
    """DES-AGENOM-002 registered per-item validator for this module."""
    sequence = item_params.get("sequence")
    if not _is_valid_dna_sequence(sequence, min_length=3):
        return fail("sequence", _SEQUENCE_CONSTRAINT)
    return ok()


register_batch_item_validator(_MODULE_NAME, _sequence_features_batch_item_validator)


def _find_longest_orf(sequence: str) -> dict | None:
    best_orf: dict | None = None
    best_length = -1

    for frame in range(3):
        for start_index in range(frame, len(sequence) - 2, 3):
            if sequence[start_index : start_index + 3] != "ATG":
                continue
            for stop_index in range(start_index + 3, len(sequence) - 2, 3):
                codon = sequence[stop_index : stop_index + 3]
                if codon not in _STOP_CODONS:
                    continue
                orf_length = stop_index + 3 - start_index
                candidate = {
                    "frame": frame,
                    "start_index": start_index,
                    "length": orf_length,
                }
                if orf_length > best_length or (
                    orf_length == best_length
                    and best_orf is not None
                    and (frame, start_index) < (best_orf["frame"], best_orf["start_index"])
                ):
                    best_orf = candidate
                    best_length = orf_length
                break

    return best_orf


def _count_codons(sequence: str, longest_orf: dict | None) -> dict[str, int]:
    if longest_orf is None:
        return {}

    start = longest_orf["start_index"]
    stop = start + longest_orf["length"]
    counts: dict[str, int] = {}
    for index in range(start, stop, 3):
        codon = sequence[index : index + 3]
        counts[codon] = counts.get(codon, 0) + 1
    return counts


# @id CODE-AGENOM-010
# @implements REQ-AGENOM-010
# @design DES-AGENOM-010
def run_sequence_features(sequences: list[str]) -> list[dict]:
    """Compute fixed sequence features for each valid DNA string in ``sequences``."""
    results: list[dict] = []

    for sequence in sequences:
        validation = validate_batch_item(_MODULE_NAME, {"sequence": sequence})
        if not validation["ok"]:
            results.append(
                {
                    "sequence": sequence,
                    "ok": False,
                    "parameter": validation["parameter"],
                    "constraint": validation["constraint"],
                }
            )
            continue

        longest_orf = _find_longest_orf(sequence)
        results.append(
            {
                "length": len(sequence),
                "gc_content": (sequence.count("G") + sequence.count("C")) / len(sequence),
                "longest_orf": longest_orf,
                "codon_usage": _count_codons(sequence, longest_orf),
            }
        )

    return results
