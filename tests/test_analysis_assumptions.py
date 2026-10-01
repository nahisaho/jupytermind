"""Tests for the analysis-assumption manifest (REQ-AIDS-054)."""

from ai_data_scientist.analysis_assumptions import (
    AnalysisAssumptionManifest,
    Assumption,
    check_manifest,
)


# @id TEST-AIDS-087
# @verifies REQ-AIDS-054
def test_TEST_AIDS_087_descriptive_scope_needs_no_causal_identification():
    manifest = AnalysisAssumptionManifest(
        analysis_scope={"population": "NYC Taxi 2024-01"},
        assumptions=(),
        causal_scope="descriptive",
    )
    findings = check_manifest(manifest)
    assert not any(f.code == "missing_causal_identification" for f in findings)


# @id TEST-AIDS-088
# @verifies REQ-AIDS-054
def test_TEST_AIDS_088_causal_scope_without_identification_assumption_flagged():
    manifest = AnalysisAssumptionManifest(
        analysis_scope={"population": "health expenditure panel"},
        assumptions=(
            Assumption(
                id="A1", statement="pooled effect equals within-country effect", status="assumed"
            ),
        ),
        causal_scope="causal",
    )
    findings = check_manifest(manifest)
    assert any(f.code == "missing_causal_identification" for f in findings)


# @id TEST-AIDS-089
# @verifies REQ-AIDS-054
def test_TEST_AIDS_089_conclusion_critical_assumed_assumption_is_unresolved_risk():
    assumed = Assumption(
        id="A1",
        statement="row order represents observation sequence",
        status="assumed",
        conclusion_critical=True,
    )
    manifest = AnalysisAssumptionManifest(
        analysis_scope={"population": "Old Faithful eruptions"},
        assumptions=(assumed,),
        causal_scope="descriptive",
    )
    assert manifest.unresolved_risks() == (assumed,)
    findings = check_manifest(manifest)
    assert any(f.assumption_id == "A1" for f in findings)


# @id TEST-AIDS-090
# @verifies REQ-AIDS-054
def test_TEST_AIDS_090_sampled_model_without_seed_produces_finding():
    manifest = AnalysisAssumptionManifest(
        analysis_scope={"population": "NYC Taxi 2024-01"},
        assumptions=(),
        causal_scope="descriptive",
        sampling={"method": "fixed_random", "n": 500000},
    )
    findings = check_manifest(manifest)
    assert any(f.code == "incomplete_sampling_record" for f in findings)
