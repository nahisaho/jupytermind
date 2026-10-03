"""Run evidence recorder (DES-ACHEM-003 / REQ-ACHEM-004)."""

from __future__ import annotations

import copy
from typing import Any

SCHEMA_VERSION = 1


# @id CODE-ACHEM-003
# @implements REQ-ACHEM-004
# @design DES-ACHEM-003
def record_run(
    module_name: str,
    params: dict[str, Any],
    result: Any,
    *,
    rdkit_version: str,
    scikit_learn_version: str | None = None,
) -> dict:
    """Build a RunRecord with exactly `metadata`, `parameters`, `result`.

    Every module's ``result`` is already JSON-safe (scalars, strings, lists,
    and nested dicts of these), so no ndarray codec is needed here (unlike
    `ai_materials_scientist.evidence`, ADR-0027). ``scikit_learn_version`` is
    included in `metadata` only when supplied (the QSAR module always
    supplies it; the other 4 modules omit it).
    """
    metadata: dict[str, Any] = {
        "module": module_name,
        "schema_version": SCHEMA_VERSION,
        "rdkit_version": rdkit_version,
    }
    if scikit_learn_version is not None:
        metadata["scikit_learn_version"] = scikit_learn_version
    return {
        "metadata": metadata,
        "parameters": dict(params),
        "result": copy.deepcopy(result),
    }
