"""Tests for ai_chemistry_scientist.structural_alerts (DES-ACHEM-070)."""

from __future__ import annotations

import importlib
import sys

from rdkit import Chem

_ALERT_RICH = "O=CC=CC(=O)C1OC1"
_ASPIRIN = "CC(=O)OC1=CC=CC=C1C(=O)O"


# @id TEST-ACHEM-959
# @verifies REQ-ACHEM-070
def test_TEST_ACHEM_959_smarts_compile_and_acceptance_fixtures_match():
    from ai_chemistry_scientist.structural_alerts import (
        ALERT_SMARTS,
        LIMITATION_LABEL_KEY,
        run_structural_alerts,
    )

    assert all(Chem.MolFromSmarts(smarts) is not None for _, smarts in ALERT_SMARTS)

    alert_rich_result = run_structural_alerts(_ALERT_RICH)
    aspirin_result = run_structural_alerts(_ASPIRIN)

    assert alert_rich_result["alerts_matched"] == [
        "aldehyde",
        "michael_acceptor_enone",
        "epoxide",
    ]
    assert alert_rich_result["alert_count"] == 3
    assert aspirin_result["alerts_matched"] == []
    assert aspirin_result["alert_count"] == 0
    assert alert_rich_result["limitation_label_key"] == LIMITATION_LABEL_KEY


# @id TEST-ACHEM-943
# @verifies REQ-ACHEM-003 REQ-ACHEM-070
def test_TEST_ACHEM_943_validator_rejects_malformed_smiles():
    import ai_chemistry_scientist.structural_alerts  # noqa: F401

    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters("structural-alerts", {"smiles": "C1CC"})

    assert result["ok"] is False
    assert result["parameter"] == "smiles"
    assert result["constraint"] == "must parse to a valid RDKit molecule"


# @id TEST-ACHEM-944
# @verifies REQ-ACHEM-070
def test_TEST_ACHEM_944_limitation_label_text_is_bilingual_and_exact():
    from ai_chemistry_scientist.structural_alerts import LIMITATION_LABEL_TEXT

    assert LIMITATION_LABEL_TEXT["en"] == (
        "Heuristic only: a small fixed illustrative SMARTS alert list, not the "
        "validated PAINS/Brenk filter catalog."
    )
    assert LIMITATION_LABEL_TEXT["ja"] == (
        "ヒューリスティックのみ: 固定の小規模な例示用SMARTSアラート一覧であり、"
        "検証済みのPAINS/Brenkフィルタ・カタログではない。"
    )


# @id TEST-ACHEM-945
# @verifies REQ-ACHEM-070
def test_TEST_ACHEM_945_run_structural_alerts_rejects_unvalidated_malformed_smiles():
    import pytest

    from ai_chemistry_scientist.structural_alerts import run_structural_alerts

    with pytest.raises(ValueError, match="must already be validated"):
        run_structural_alerts("C1CC")


# @id TEST-ACHEM-962
# @verifies REQ-ACHEM-070
def test_TEST_ACHEM_962_alerts_are_reported_in_definition_order_not_match_order(monkeypatch):
    import ai_chemistry_scientist.structural_alerts as mod

    class _FakeMol:
        def HasSubstructMatch(self, pattern):
            return pattern in {"[N+](=O)[O-]", "C1OC1", "[SX2H]"}

    monkeypatch.setattr(mod, "parse_smiles", lambda smiles: _FakeMol())
    # Alert queries are pre-compiled at import time (not re-compiled per
    # call), so the fixture patches the pre-compiled query table directly
    # using the original SMARTS strings as stand-in "compiled" queries.
    monkeypatch.setattr(
        mod, "_ALERT_QUERIES", tuple((name, smarts) for name, smarts in mod.ALERT_SMARTS)
    )

    result = mod.run_structural_alerts("order-fixture")

    assert result["alerts_matched"] == ["nitro_group", "epoxide", "free_thiol"]
    assert result["alert_count"] == 3


# @id TEST-ACHEM-966
# @verifies REQ-ACHEM-070
def test_TEST_ACHEM_966_validator_rejects_dummy_atom_smiles_as_chemically_undefined():
    import ai_chemistry_scientist.structural_alerts  # noqa: F401

    from ai_chemistry_scientist.validation import validate_parameters

    assert validate_parameters("structural-alerts", {"smiles": "*"}) == {
        "ok": False,
        "parameter": "smiles",
        "constraint": "must parse to a valid RDKit molecule",
    }


# @id TEST-ACHEM-969
# @verifies REQ-ACHEM-070
def test_TEST_ACHEM_969_structural_alert_queries_fail_fast_when_any_smarts_is_malformed(
    monkeypatch,
):
    import pytest

    module_name = "ai_chemistry_scientist.structural_alerts"
    original_module = sys.modules.pop(module_name, None)
    original_mol_from_smarts = Chem.MolFromSmarts

    def _fake_mol_from_smarts(smarts):
        if smarts == "[N+](=O)[O-]":
            return None
        return original_mol_from_smarts(smarts)

    monkeypatch.setattr(Chem, "MolFromSmarts", _fake_mol_from_smarts)

    try:
        with pytest.raises(ValueError, match="nitro_group"):
            importlib.import_module(module_name)
    finally:
        sys.modules.pop(module_name, None)
        if original_module is not None:
            sys.modules[module_name] = original_module


# @id TEST-ACHEM-970
# @verifies REQ-ACHEM-070
def test_TEST_ACHEM_970_each_named_alert_and_all_five_match_real_smiles():
    from ai_chemistry_scientist.structural_alerts import run_structural_alerts

    expected_examples = {
        "nitro_group": "C[N+](=O)[O-]",
        "aldehyde": "CC=O",
        "michael_acceptor_enone": "CC=CC(=O)C",
        "epoxide": "CC1OC1",
        "free_thiol": "CCS",
    }

    for expected_alert, smiles in expected_examples.items():
        result = run_structural_alerts(smiles)
        assert result["alerts_matched"] == [expected_alert]
        assert result["alert_count"] == 1

    all_alerts_result = run_structural_alerts("C[N+](=O)[O-].CC=O.CC=CC(=O)C.CC1OC1.CCS")

    assert all_alerts_result["alerts_matched"] == list(expected_examples)
    assert all_alerts_result["alert_count"] == len(expected_examples)
