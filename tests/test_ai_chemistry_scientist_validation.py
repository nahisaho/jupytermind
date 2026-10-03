"""Tests for ai_chemistry_scientist.validation (DES-ACHEM-002 / REQ-ACHEM-003)."""

from __future__ import annotations


# @id TEST-ACHEM-003
# @verifies REQ-ACHEM-003
def test_TEST_ACHEM_003_validate_parameters_dispatches_to_registered_module_validator():
    from ai_chemistry_scientist.validation import register_validator, validate_parameters

    def _fake_validator(params):
        if params.get("x", 0) < 0:
            return {"ok": False, "parameter": "x", "constraint": "x >= 0"}
        return {"ok": True}

    register_validator("fake-chem-module", _fake_validator)

    assert validate_parameters("fake-chem-module", {"x": 1})["ok"] is True
    failure = validate_parameters("fake-chem-module", {"x": -1})
    assert failure["ok"] is False
    assert failure["parameter"] == "x"


# @id TEST-ACHEM-916
# @verifies REQ-ACHEM-003
def test_TEST_ACHEM_916_validate_parameters_unknown_module_is_rejected():
    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters("no-such-chem-module", {})

    assert result["ok"] is False
    assert result["parameter"] == "module"


# @id TEST-ACHEM-917
# @verifies REQ-ACHEM-003
def test_TEST_ACHEM_917_validate_batch_item_dispatches_to_registered_per_item_validator():
    from ai_chemistry_scientist.validation import (
        register_batch_item_validator,
        validate_batch_item,
    )

    def _fake_item_validator(item_params):
        if not item_params.get("smiles"):
            return {"ok": False, "parameter": "smiles", "constraint": "must be non-empty"}
        return {"ok": True}

    register_batch_item_validator("fake-batch-module", _fake_item_validator)

    assert validate_batch_item("fake-batch-module", {"smiles": "CCO"})["ok"] is True
    failure = validate_batch_item("fake-batch-module", {"smiles": ""})
    assert failure["ok"] is False
    assert failure["parameter"] == "smiles"


# @id TEST-ACHEM-918
# @verifies REQ-ACHEM-003
def test_TEST_ACHEM_918_validate_batch_item_unknown_module_is_rejected():
    from ai_chemistry_scientist.validation import validate_batch_item

    result = validate_batch_item("no-such-batch-module", {})

    assert result["ok"] is False
    assert result["parameter"] == "module"


# @id TEST-ACHEM-919
# @verifies REQ-ACHEM-003
def test_TEST_ACHEM_919_ok_and_fail_helpers_build_exact_shapes():
    from ai_chemistry_scientist.validation import fail, ok

    assert ok() == {"ok": True}
    assert fail("smiles", "must parse") == {
        "ok": False,
        "parameter": "smiles",
        "constraint": "must parse",
    }


# @id TEST-ACHEM-935
# @verifies REQ-ACHEM-003
def test_TEST_ACHEM_935_validate_parameters_rejects_non_dict_params():
    from ai_chemistry_scientist.validation import register_validator, validate_parameters

    register_validator("fake-non-dict-module", lambda params: {"ok": True})

    result = validate_parameters("fake-non-dict-module", None)

    assert result["ok"] is False
    assert result["parameter"] == "params"
