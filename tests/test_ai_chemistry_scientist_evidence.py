"""Tests for ai_chemistry_scientist.evidence (DES-ACHEM-003 / REQ-ACHEM-004)."""

from __future__ import annotations


# @id TEST-ACHEM-004
# @verifies REQ-ACHEM-004
def test_TEST_ACHEM_004_record_run_has_exactly_three_top_level_keys():
    from ai_chemistry_scientist.evidence import record_run

    record = record_run(
        module_name="molecular-descriptors",
        params={"smiles_list": ["CCO"]},
        result=[{"smiles": "CCO", "mol_wt": 46.07}],
        rdkit_version="2026.03.6",
    )

    assert set(record.keys()) == {"metadata", "parameters", "result"}
    assert record["metadata"]["module"] == "molecular-descriptors"
    assert record["metadata"]["rdkit_version"] == "2026.03.6"
    assert "schema_version" in record["metadata"]
    assert "scikit_learn_version" not in record["metadata"]
    assert record["parameters"] == {"smiles_list": ["CCO"]}
    assert record["result"] == [{"smiles": "CCO", "mol_wt": 46.07}]


# @id TEST-ACHEM-920
# @verifies REQ-ACHEM-004
def test_TEST_ACHEM_920_qsar_record_includes_scikit_learn_version():
    from ai_chemistry_scientist.evidence import record_run

    record = record_run(
        module_name="qsar-modeling",
        params={},
        result={"coefficients": [1.0], "intercept": 0.0, "predictions": []},
        rdkit_version="2026.03.6",
        scikit_learn_version="1.5.0",
    )

    assert record["metadata"]["scikit_learn_version"] == "1.5.0"


# @id TEST-ACHEM-921
# @verifies REQ-ACHEM-004
def test_TEST_ACHEM_921_identical_params_reproduce_exactly_equal_result():
    from ai_chemistry_scientist.admet_prediction import run_admet_prediction
    from ai_chemistry_scientist.evidence import record_run

    aspirin = "CC(=O)OC1=CC=CC=C1C(=O)O"
    result_a = run_admet_prediction(aspirin)
    result_b = run_admet_prediction(aspirin)

    record_a = record_run(
        module_name="admet-prediction",
        params={"smiles": aspirin},
        result=result_a,
        rdkit_version="x",
    )
    record_b = record_run(
        module_name="admet-prediction",
        params={"smiles": aspirin},
        result=result_b,
        rdkit_version="x",
    )

    assert record_a["result"] == record_b["result"]
