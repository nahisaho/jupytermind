"""Molecular similarity search module (DES-ACHEM-040 / REQ-ACHEM-040)."""

from __future__ import annotations

import csv
from pathlib import Path

from rdkit import DataStructs
from rdkit.Chem import rdFingerprintGenerator

from ai_chemistry_scientist.molecular_descriptors import parse_smiles
from ai_chemistry_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "molecular-similarity"
_DATA_PATH = Path(__file__).resolve().parent / "data" / "sample_molecules.csv"
_MIN_K = 1
_MAX_K = 20
_MORGAN_GENERATOR = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)

_dataset_cache: list[dict] | None = None


def _load_dataset() -> list[dict]:
    """Load and cache the bundled 20-row dataset (module-level, read-only)."""
    global _dataset_cache
    if _dataset_cache is None:
        with _DATA_PATH.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        _dataset_cache = [
            {
                "name": row["name"],
                "smiles": row["smiles"],
                "fingerprint": _MORGAN_GENERATOR.GetFingerprint(parse_smiles(row["smiles"])),
            }
            for row in rows
        ]
    return _dataset_cache


def _molecular_similarity_validator(params: dict) -> dict:
    """DES-ACHEM-002 registered atomic validator for this module."""
    if "query_smiles" not in params:
        return fail("query_smiles", "is required")
    if "k" not in params:
        return fail("k", "is required")
    if parse_smiles(params["query_smiles"]) is None:
        return fail("smiles", "must parse to a valid RDKit molecule")
    k = params["k"]
    if not isinstance(k, int) or isinstance(k, bool) or not (_MIN_K <= k <= _MAX_K):
        return fail("k", "must be an integer in [1, 20]")
    return ok()


register_validator(_MODULE_NAME, _molecular_similarity_validator)


# @id CODE-ACHEM-040
# @implements REQ-ACHEM-040
# @design DES-ACHEM-040
def run_molecular_similarity(query_smiles: str, k: int = 5) -> dict:
    """Return the top-``k`` dataset entries by descending Tanimoto similarity.

    Receives ``query_smiles``/``k`` already validated atomically by its
    handler wrapper; performs no revalidation of its own.
    """
    query_mol = parse_smiles(query_smiles)
    query_fp = _MORGAN_GENERATOR.GetFingerprint(query_mol)

    scored = [
        {
            "name": entry["name"],
            "similarity": DataStructs.TanimotoSimilarity(query_fp, entry["fingerprint"]),
        }
        for entry in _load_dataset()
    ]
    scored.sort(key=lambda entry: (-entry["similarity"], entry["name"]))

    return {"query_smiles": query_smiles, "results": scored[:k]}
