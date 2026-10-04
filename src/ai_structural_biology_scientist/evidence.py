"""Run evidence recorder (DES-ASTRUCT-003 / REQ-ASTRUCT-004)."""

from __future__ import annotations

from typing import Any

import numpy

SCHEMA_VERSION = 1


def _json_safe_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, numpy.generic):
        return _json_safe_value(value.item())
    if isinstance(value, dict):
        return {key: _json_safe_value(nested) for key, nested in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe_value(item) for item in value]
    raise TypeError(f"unsupported non-JSON-safe value: {type(value).__name__}")


# @id CODE-ASTRUCT-003
# @implements REQ-ASTRUCT-004
# @design DES-ASTRUCT-003
def record_run(
    module_name: str,
    params: dict[str, Any],
    result: Any,
    *,
    numpy_version: str,
) -> dict:
    """Build a RunRecord with exactly `metadata`, `parameters`, `result`."""
    return {
        "metadata": {
            "module": module_name,
            "schema_version": SCHEMA_VERSION,
            "numpy_version": numpy_version,
        },
        "parameters": _json_safe_value(params),
        "result": _json_safe_value(result),
    }
