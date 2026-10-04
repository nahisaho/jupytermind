"""Variant effect heuristic annotation module (DES-AGENOM-020 / REQ-AGENOM-020)."""

from __future__ import annotations

from numbers import Integral

from ai_genomics_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "variant-effect-annotation"
_DNA_BASES = frozenset({"A", "C", "G", "T"})
_STOP_REFERENCE_CONSTRAINT = "stop-reference codons must mutate to a non-stop codon"

_STANDARD_GENETIC_CODE = {
    "TTT": "F",
    "TTC": "F",
    "TTA": "L",
    "TTG": "L",
    "TCT": "S",
    "TCC": "S",
    "TCA": "S",
    "TCG": "S",
    "TAT": "Y",
    "TAC": "Y",
    "TAA": "*",
    "TAG": "*",
    "TGT": "C",
    "TGC": "C",
    "TGA": "*",
    "TGG": "W",
    "CTT": "L",
    "CTC": "L",
    "CTA": "L",
    "CTG": "L",
    "CCT": "P",
    "CCC": "P",
    "CCA": "P",
    "CCG": "P",
    "CAT": "H",
    "CAC": "H",
    "CAA": "Q",
    "CAG": "Q",
    "CGT": "R",
    "CGC": "R",
    "CGA": "R",
    "CGG": "R",
    "ATT": "I",
    "ATC": "I",
    "ATA": "I",
    "ATG": "M",
    "ACT": "T",
    "ACC": "T",
    "ACA": "T",
    "ACG": "T",
    "AAT": "N",
    "AAC": "N",
    "AAA": "K",
    "AAG": "K",
    "AGT": "S",
    "AGC": "S",
    "AGA": "R",
    "AGG": "R",
    "GTT": "V",
    "GTC": "V",
    "GTA": "V",
    "GTG": "V",
    "GCT": "A",
    "GCC": "A",
    "GCA": "A",
    "GCG": "A",
    "GAT": "D",
    "GAC": "D",
    "GAA": "E",
    "GAG": "E",
    "GGT": "G",
    "GGC": "G",
    "GGA": "G",
    "GGG": "G",
}


def _is_dna_string(value: object, *, length: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == length
        and value.isupper()
        and set(value).issubset(_DNA_BASES)
    )


def _translate_codon(codon: str) -> str:
    return _STANDARD_GENETIC_CODE[codon]


def _variant_effect_validator(params: dict) -> dict:
    """DES-AGENOM-002 registered atomic validator for this module."""
    ref_codon = params.get("ref_codon")
    position = params.get("position")
    alt_base = params.get("alt_base")

    if not _is_dna_string(ref_codon, length=3):
        return fail("ref_codon", "must be exactly 3 uppercase DNA bases over {A,C,G,T}")
    if (
        not isinstance(position, Integral)
        or isinstance(position, bool)
        or position not in {0, 1, 2}
    ):
        return fail("position", "must be an integer in {0,1,2}")
    if not _is_dna_string(alt_base, length=1):
        return fail("alt_base", "must be exactly 1 uppercase DNA base over {A,C,G,T}")
    if alt_base == ref_codon[position]:
        return fail("alt_base", "alt_base must differ from the reference base at position")

    alt_codon = ref_codon[:position] + alt_base + ref_codon[position + 1 :]
    if _translate_codon(ref_codon) == "*" and _translate_codon(alt_codon) == "*":
        return fail("ref_codon", _STOP_REFERENCE_CONSTRAINT)

    return ok()


register_validator(_MODULE_NAME, _variant_effect_validator)


def _classify_effect(ref_amino_acid: str, alt_amino_acid: str) -> str:
    if ref_amino_acid == "*" and alt_amino_acid != "*":
        return "readthrough"
    if ref_amino_acid != "*" and alt_amino_acid == "*":
        return "nonsense"
    if ref_amino_acid == alt_amino_acid:
        return "synonymous"
    return "missense"


# @id CODE-AGENOM-020
# @implements REQ-AGENOM-020
# @design DES-AGENOM-020
def run_variant_effect(ref_codon: str, position: int, alt_base: str) -> dict:
    """Annotate a single-codon substitution under the standard genetic code."""
    alt_codon = ref_codon[:position] + alt_base + ref_codon[position + 1 :]
    ref_amino_acid = _translate_codon(ref_codon)
    alt_amino_acid = _translate_codon(alt_codon)
    return {
        "ref_codon": ref_codon,
        "alt_codon": alt_codon,
        "ref_amino_acid": ref_amino_acid,
        "alt_amino_acid": alt_amino_acid,
        "effect": _classify_effect(ref_amino_acid, alt_amino_acid),
    }
