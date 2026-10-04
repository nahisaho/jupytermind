"""Tests for ai_genomics_scientist.validation (DES-AGENOM-002 / REQ-AGENOM-003)."""

from __future__ import annotations

from types import MappingProxyType


# @id TEST-AGENOM-003
# @verifies REQ-AGENOM-003
def test_TEST_AGENOM_003_validation_registry_supports_atomic_and_per_item_checks():
    from ai_genomics_scientist.validation import (
        fail,
        ok,
        register_batch_item_validator,
        register_validator,
        validate_batch_item,
        validate_parameters,
    )

    def _fake_atomic_validator(params):
        if params["value"] <= 0:
            return fail("value", "must be > 0")
        return ok()

    def _fake_item_validator(params):
        if params["sequence"] == "ATBX":
            return fail(
                "sequence",
                "must be a non-empty uppercase DNA string over {A,C,G,T} with length >= 3",
            )
        return ok()

    register_validator("fake-atomic-module", _fake_atomic_validator)
    register_batch_item_validator("fake-batch-module", _fake_item_validator)

    assert ok() == {"ok": True}
    assert fail("window", "must be exactly 9 characters") == {
        "ok": False,
        "parameter": "window",
        "constraint": "must be exactly 9 characters",
    }
    assert validate_parameters("fake-atomic-module", {"value": 1}) == {"ok": True}
    assert validate_parameters("fake-atomic-module", {"value": 0}) == {
        "ok": False,
        "parameter": "value",
        "constraint": "must be > 0",
    }
    assert validate_batch_item("fake-batch-module", {"sequence": "ATG"}) == {"ok": True}
    assert validate_batch_item("fake-batch-module", {"sequence": "ATBX"}) == {
        "ok": False,
        "parameter": "sequence",
        "constraint": "must be a non-empty uppercase DNA string over {A,C,G,T} with length >= 3",
    }


# @id TEST-AGENOM-060
# @verifies REQ-AGENOM-003
def test_TEST_AGENOM_060_validate_batch_item_rejects_malformed_item_params():
    from ai_genomics_scientist.validation import register_batch_item_validator, validate_batch_item

    register_batch_item_validator("fake-batch-shape", lambda params: {"ok": True})

    assert validate_batch_item("fake-batch-shape", None) == {
        "ok": False,
        "parameter": "params",
        "constraint": "must be a dict",
    }


# @id TEST-AGENOM-063
# @verifies REQ-AGENOM-003
def test_TEST_AGENOM_063_validate_batch_item_accepts_read_only_mapping_inputs():
    from ai_genomics_scientist.validation import register_batch_item_validator, validate_batch_item

    register_batch_item_validator(
        "fake-batch-mapping", lambda params: {"ok": params["sequence"] == "ATG"}
    )

    assert validate_batch_item(
        "fake-batch-mapping",
        MappingProxyType({"sequence": "ATG"}),
    ) == {"ok": True}
