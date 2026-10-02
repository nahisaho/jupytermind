"""Run evidence recording and JSON-safe codec (DES-AIMS-003 / REQ-AIMS-004/005)."""

from __future__ import annotations

from typing import Any

import numpy as np

SCHEMA_VERSION = 1


# @id CODE-AIMS-003
# @implements REQ-AIMS-004 REQ-AIMS-005
# @design DES-AIMS-003
def record_run(
    module_name: str,
    unit_system: str,
    params: dict[str, Any],
    arrays: dict[str, np.ndarray],
    seed: int | None,
    *,
    allow_integer_arrays: frozenset[str] = frozenset(),
) -> dict:
    """Build a RunRecord with exactly `metadata`, `parameters`, `arrays`.

    ``seed`` is the explicit integer seed for a stochastic module, or
    ``None`` for a deterministic module (REQ-AIMS-004). Every array must be
    ``float64`` unless its name is listed in ``allow_integer_arrays`` (a
    module's own requirement explicitly stating an integer array).
    """
    for name, array in arrays.items():
        if name in allow_integer_arrays:
            continue
        if array.dtype != np.float64:
            raise ValueError(
                f"array '{name}' must be float64 unless explicitly declared integer "
                f"(REQ-AIMS-004), got dtype={array.dtype}"
            )
    return {
        "metadata": {
            "module": module_name,
            "unit_system": unit_system,
            "schema_version": SCHEMA_VERSION,
            "seed": seed,
        },
        "parameters": dict(params),
        "arrays": dict(arrays),
    }


# @id CODE-AIMS-903
# @implements REQ-AIMS-004
# @design DES-AIMS-003
def to_json(run_record: dict) -> dict:
    """Encode a RunRecord's `arrays` ndarrays as {dtype, shape, data}."""
    encoded_arrays = {}
    for name, array in run_record["arrays"].items():
        encoded_arrays[name] = {
            "dtype": str(array.dtype),
            "shape": list(array.shape),
            "data": array.tolist(),
        }
    return {
        "metadata": dict(run_record["metadata"]),
        "parameters": dict(run_record["parameters"]),
        "arrays": encoded_arrays,
    }


# @id CODE-AIMS-904
# @implements REQ-AIMS-004
# @design DES-AIMS-003
def from_json(json_safe_record: dict) -> dict:
    """Reconstruct a RunRecord from its JSON-safe encoding (inverse of to_json)."""
    decoded_arrays = {}
    for name, encoded in json_safe_record["arrays"].items():
        decoded_arrays[name] = np.array(encoded["data"], dtype=encoded["dtype"]).reshape(
            encoded["shape"]
        )
    return {
        "metadata": dict(json_safe_record["metadata"]),
        "parameters": dict(json_safe_record["parameters"]),
        "arrays": decoded_arrays,
    }
