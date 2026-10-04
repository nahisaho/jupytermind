"""Pairwise sequence alignment module (DES-AGENOM-050 / REQ-AGENOM-050)."""

from __future__ import annotations

from ai_genomics_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "pairwise-sequence-alignment"
_DNA_BASES = frozenset({"A", "C", "G", "T"})
_MATCH_SCORE = 1
_MISMATCH_SCORE = -1
_GAP_SCORE = -2


def _is_dna_string(value: object) -> bool:
    return isinstance(value, str) and value.isupper() and value and set(value).issubset(_DNA_BASES)


def _sequence_alignment_validator(params: dict) -> dict:
    """DES-AGENOM-002 registered atomic validator for this module."""
    seq1 = params.get("seq1")
    seq2 = params.get("seq2")
    if not _is_dna_string(seq1):
        return fail("seq1", "must be a non-empty uppercase DNA string over {A,C,G,T}")
    if not _is_dna_string(seq2):
        return fail("seq2", "must be a non-empty uppercase DNA string over {A,C,G,T}")
    return ok()


register_validator(_MODULE_NAME, _sequence_alignment_validator)


# @id CODE-AGENOM-050
# @implements REQ-AGENOM-050
# @design DES-AGENOM-050
def run_sequence_alignment(seq1: str, seq2: str) -> dict:
    """Compute the fixed-score Needleman-Wunsch global alignment."""
    rows = len(seq1) + 1
    cols = len(seq2) + 1
    scores = [[0] * cols for _ in range(rows)]
    traceback = [[""] * cols for _ in range(rows)]

    for row in range(1, rows):
        scores[row][0] = row * _GAP_SCORE
        traceback[row][0] = "up"
    for col in range(1, cols):
        scores[0][col] = col * _GAP_SCORE
        traceback[0][col] = "left"

    for row in range(1, rows):
        for col in range(1, cols):
            match_score = _MATCH_SCORE if seq1[row - 1] == seq2[col - 1] else _MISMATCH_SCORE
            diagonal = scores[row - 1][col - 1] + match_score
            up = scores[row - 1][col] + _GAP_SCORE
            left = scores[row][col - 1] + _GAP_SCORE
            best = max(diagonal, up, left)
            scores[row][col] = best
            if diagonal == best:
                traceback[row][col] = "diag"
            elif up == best:
                traceback[row][col] = "up"
            else:
                traceback[row][col] = "left"

    aligned_seq1: list[str] = []
    aligned_seq2: list[str] = []
    row = len(seq1)
    col = len(seq2)
    while row > 0 or col > 0:
        move = traceback[row][col]
        if move == "diag":
            aligned_seq1.append(seq1[row - 1])
            aligned_seq2.append(seq2[col - 1])
            row -= 1
            col -= 1
        elif move == "up":
            aligned_seq1.append(seq1[row - 1])
            aligned_seq2.append("-")
            row -= 1
        else:
            aligned_seq1.append("-")
            aligned_seq2.append(seq2[col - 1])
            col -= 1

    aligned1 = "".join(reversed(aligned_seq1))
    aligned2 = "".join(reversed(aligned_seq2))
    matches = sum(
        1
        for base1, base2 in zip(aligned1, aligned2, strict=True)
        if base1 == base2 and base1 != "-" and base2 != "-"
    )
    identity = matches / len(aligned1) if aligned1 else 0.0
    return {
        "aligned_seq1": aligned1,
        "aligned_seq2": aligned2,
        "score": scores[-1][-1],
        "identity": identity,
    }
