"""Tests for ai_chemistry_scientist module routing by request content (DES-ACHEM-001)."""

from __future__ import annotations

import pytest

_ASPIRIN = "CC(=O)OC1=CC=CC=C1C(=O)O"


# @id TEST-ACHEM-002
# @verifies REQ-ACHEM-002
@pytest.mark.parametrize(
    ("request_text", "expected_module"),
    [
        ("I want to calculate molecular descriptors", "molecular-descriptors"),
        ("分子記述子を計算したい", "molecular-descriptors"),
        ("Run ADMET prediction for this compound", "admet-prediction"),
        ("ADMET予測を実行してください", "admet-prediction"),
        ("Fit a QSAR modeling regression", "qsar-modeling"),
        ("QSARモデリングを行いたい", "qsar-modeling"),
        ("Run a molecular similarity search", "molecular-similarity"),
        ("分子類似性を検索して", "molecular-similarity"),
        ("Compute the docking score for this ligand", "docking-score"),
        ("ドッキングスコアを計算して", "docking-score"),
        ("Fit the dose-response fitting curve for this compound", "dose-response-fitting"),
        ("用量反応曲線フィッティングをして", "dose-response-fitting"),
        (
            "Run a pharmacokinetic analysis on this concentration-time data",
            "pharmacokinetic-analysis",
        ),
        ("薬物動態解析を実行して", "pharmacokinetic-analysis"),
        ("Fit the enzyme kinetics for this substrate data", "enzyme-kinetics"),
        ("酵素反応速度論を解析して", "enzyme-kinetics"),
    ],
)
def test_TEST_ACHEM_002_dispatches_to_exactly_one_matched_module(request_text, expected_module):
    from ai_chemistry_scientist.dispatch import dispatch

    result = dispatch(request_text)

    assert result["outcome"] == "dispatch"
    assert result["module"] == expected_module
    assert "handler_result" in result


# @id TEST-ACHEM-922
# @verifies REQ-ACHEM-002
def test_TEST_ACHEM_922_two_matched_modules_yields_clarification_with_no_dispatch():
    from ai_chemistry_scientist.dispatch import dispatch

    result = dispatch("Should I use admet prediction or docking score here?")

    assert result["outcome"] == "clarification"
    assert set(result["candidates"]) == {"admet-prediction", "docking-score"}


# @id TEST-ACHEM-923
# @verifies REQ-ACHEM-002
def test_TEST_ACHEM_923_no_matched_module_yields_rejection_with_no_dispatch():
    from ai_chemistry_scientist.dispatch import dispatch

    result = dispatch("What is the weather today?")

    assert result["outcome"] == "rejected"


# @id TEST-ACHEM-924
# @verifies REQ-ACHEM-002
def test_TEST_ACHEM_924_rejects_non_string_request_text():
    from ai_chemistry_scientist.dispatch import dispatch

    with pytest.raises(ValueError, match="request_text"):
        dispatch(None)


# @id TEST-ACHEM-925
# @verifies REQ-ACHEM-002
def test_TEST_ACHEM_925_rejects_unsupported_explicit_language_override():
    from ai_chemistry_scientist.dispatch import dispatch

    with pytest.raises(ValueError, match="language"):
        dispatch("Run ADMET prediction", language="fr")


# @id TEST-ACHEM-926
# @verifies REQ-ACHEM-003 REQ-ACHEM-004
def test_TEST_ACHEM_926_end_to_end_dispatch_computes_and_records_run():
    from ai_chemistry_scientist.dispatch import dispatch

    request_text = 'Compute molecular descriptors {"smiles_list": ["CC(=O)OC1=CC=CC=C1C(=O)O"]}'

    result = dispatch(request_text)

    assert result["handler_result"]["ok"] is True
    run_record = result["handler_result"]["run_record"]
    assert set(run_record.keys()) == {"metadata", "parameters", "result"}
    [descriptor] = run_record["result"]
    assert descriptor["mol_wt"] == pytest.approx(180.159, abs=0.01)


# @id TEST-ACHEM-927
# @verifies REQ-ACHEM-003
def test_TEST_ACHEM_927_end_to_end_dispatch_validation_failure_is_localized():
    from ai_chemistry_scientist.dispatch import dispatch

    request_text = 'ADMET予測 {"smiles": "C1CC"}'

    result = dispatch(request_text)

    assert result["handler_result"]["ok"] is False
    assert result["handler_result"]["parameter"] == "smiles"
    assert result["handler_result"]["constraint"] == "must parse to a valid RDKit molecule"
    assert result["handler_result"]["language"] == "ja"


# @id TEST-ACHEM-928
# @verifies REQ-ACHEM-002
def test_TEST_ACHEM_928_missing_embedded_params_is_rejected_without_crashing():
    from ai_chemistry_scientist.dispatch import dispatch

    result = dispatch("I want to calculate molecular descriptors")

    assert result["outcome"] == "dispatch"
    assert result["handler_result"]["ok"] is False
    assert result["handler_result"]["parameter"] == "params"


# @id TEST-ACHEM-929
# @verifies REQ-ACHEM-020 REQ-ACHEM-050
def test_TEST_ACHEM_929_limitation_label_is_localized_by_dispatch():
    from ai_chemistry_scientist.dispatch import dispatch

    en_result = dispatch(f'ADMET prediction {{"smiles": "{_ASPIRIN}"}}')
    ja_result = dispatch(f'ADMET予測 {{"smiles": "{_ASPIRIN}"}}')

    en_label = en_result["handler_result"]["run_record"]["result"]["limitation_label"]
    ja_label = ja_result["handler_result"]["run_record"]["result"]["limitation_label"]

    assert en_label == "Heuristic only: not a physically or clinically validated ADMET prediction."
    assert ja_label.startswith("ヒューリスティックのみ")
    assert "limitation_label_key" not in en_result["handler_result"]["run_record"]["result"]


# @id TEST-ACHEM-936
# @verifies REQ-ACHEM-002
def test_TEST_ACHEM_936_matches_candidate_despite_extra_internal_whitespace():
    from ai_chemistry_scientist.dispatch import dispatch

    result = dispatch("I want to    calculate   molecular   descriptors")

    assert result["outcome"] == "dispatch"
    assert result["module"] == "molecular-descriptors"


# @id TEST-ACHEM-953
# @verifies REQ-ACHEM-002
@pytest.mark.parametrize(
    ("request_text", "expected_module"),
    [
        ("Run drug-likeness screening", "drug-likeness-rules"),
        ("薬物らしさルールスクリーニングを実行してください", "drug-likeness-rules"),
        ("Run structural alert screening", "structural-alerts"),
        ("構造アラートスクリーニングを実行してください", "structural-alerts"),
        ("Compute molecular formula and exact mass", "molecular-formula-mass"),
        ("分子式・正確質量を計算してください", "molecular-formula-mass"),
        ("Run bioactivity classification", "bioactivity-classification"),
        ("生物活性分類を実行してください", "bioactivity-classification"),
    ],
)
def test_TEST_ACHEM_953_dispatches_new_methods_to_exactly_one_matched_module(
    request_text, expected_module
):
    from ai_chemistry_scientist.dispatch import dispatch

    result = dispatch(request_text)

    assert result["outcome"] == "dispatch"
    assert result["module"] == expected_module
    assert "handler_result" in result


# @id TEST-ACHEM-954
# @verifies REQ-ACHEM-070
def test_TEST_ACHEM_954_structural_alert_limitation_label_is_localized_by_dispatch():
    from ai_chemistry_scientist.dispatch import dispatch

    en_result = dispatch(f'structural alert screening {{"smiles": "{_ASPIRIN}"}}')
    ja_result = dispatch(f'構造アラートスクリーニング {{"smiles": "{_ASPIRIN}"}}')

    en_label = en_result["handler_result"]["run_record"]["result"]["limitation_label"]
    ja_label = ja_result["handler_result"]["run_record"]["result"]["limitation_label"]

    assert en_label == (
        "Heuristic only: a small fixed illustrative SMARTS alert list, not the "
        "validated PAINS/Brenk filter catalog."
    )
    assert ja_label.startswith("ヒューリスティックのみ")
    assert "limitation_label_key" not in en_result["handler_result"]["run_record"]["result"]


# @id TEST-ACHEM-955
# @verifies REQ-ACHEM-080 REQ-ACHEM-004
def test_TEST_ACHEM_955_dispatch_wraps_formula_mass_result_in_run_record():
    from ai_chemistry_scientist.dispatch import dispatch

    result = dispatch(f'molecular formula and exact mass {{"smiles": "{_ASPIRIN}"}}')

    assert result["handler_result"]["ok"] is True
    run_record = result["handler_result"]["run_record"]
    assert set(run_record.keys()) == {"metadata", "parameters", "result"}
    assert run_record["result"] == {
        "molecular_formula": "C9H8O4",
        "exact_mass": pytest.approx(180.042258736, abs=1e-9),
    }


# @id TEST-ACHEM-956
# @verifies REQ-ACHEM-090
def test_TEST_ACHEM_956_bioactivity_limitation_label_is_localized_by_dispatch():
    from ai_chemistry_scientist.dispatch import dispatch

    en_result = dispatch(f'bioactivity classification {{"smiles": "{_ASPIRIN}"}}')
    ja_result = dispatch(f'生物活性分類 {{"smiles": "{_ASPIRIN}"}}')

    en_label = en_result["handler_result"]["run_record"]["result"]["limitation_label"]
    ja_label = ja_result["handler_result"]["run_record"]["result"]["limitation_label"]

    assert en_label == (
        "Heuristic only: not a ChEMBL-trained or experimentally validated bioactivity classifier."
    )
    assert ja_label.startswith("ヒューリスティックのみ")
    assert "limitation_label_key" not in en_result["handler_result"]["run_record"]["result"]


# @id TEST-ACHEM-960
# @verifies REQ-ACHEM-080 REQ-ACHEM-004
def test_TEST_ACHEM_960_handler_accepts_structured_kwargs_from_calling_context():
    from ai_chemistry_scientist.dispatch import handle_molecular_formula_mass

    result = handle_molecular_formula_mass(
        "request text without embedded JSON", "en", smiles=_ASPIRIN
    )

    assert result["ok"] is True
    assert result["run_record"]["parameters"] == {"smiles": _ASPIRIN}
    assert result["run_record"]["result"] == {
        "molecular_formula": "C9H8O4",
        "exact_mass": pytest.approx(180.042258736, abs=1e-9),
    }
