"""CRISPR guide-RNA PAM-site scan module (DES-AGENOM-100 / REQ-AGENOM-100)."""

from __future__ import annotations

from ai_genomics_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "crispr-pam-scan"
_DNA_BASES = frozenset({"A", "C", "G", "T"})
_PROTOSPACER_LENGTH = 20


def _is_dna_string(value: object) -> bool:
    return isinstance(value, str) and value.isupper() and value and set(value).issubset(_DNA_BASES)


def _crispr_pam_scan_validator(params: dict) -> dict:
    """DES-AGENOM-002 registered atomic validator for this module."""
    sequence = params.get("sequence")
    if not isinstance(sequence, str) or sequence == "":
        return fail("sequence", "must be non-empty")
    if not _is_dna_string(sequence):
        return fail("sequence", "must be uppercase over {A,C,G,T}")
    return ok()


register_validator(_MODULE_NAME, _crispr_pam_scan_validator)


# @id CODE-AGENOM-100
# @implements REQ-AGENOM-100
# @design DES-AGENOM-100
def run_crispr_pam_scan(sequence: str) -> dict:
    """Scan a validated DNA ``sequence`` for forward-strand canonical NGG PAM sites."""
    sites: list[dict] = []
    for index in range(len(sequence) - 2):
        if sequence[index + 1 : index + 3] != "GG":
            continue
        protospacer_start = index - _PROTOSPACER_LENGTH
        if protospacer_start < 0:
            continue
        sites.append(
            {
                "pam_index": index,
                "pam": sequence[index : index + 3],
                "protospacer": sequence[protospacer_start:index],
            }
        )
    return {"sites": sites}
