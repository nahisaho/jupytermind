"""Tests for ai_genomics_scientist.dispatch (DES-AGENOM-001 / REQ-AGENOM-002)."""

from __future__ import annotations


# @id TEST-AGENOM-002
# @verifies REQ-AGENOM-002
def test_TEST_AGENOM_002_dispatches_registered_english_and_japanese_names_only():
    from ai_genomics_scientist.dispatch import dispatch

    fixture_requests = [
        ("I want to run sequence-features", "sequence-features"),
        ("配列特徴量解析を実行したい", "sequence-features"),
        ("I want to run variant-effect-annotation", "variant-effect-annotation"),
        ("バリアント効果注釈を実行したい", "variant-effect-annotation"),
        ("I want to run splice-site-strength", "splice-site-strength"),
        ("スプライス部位強度を実行したい", "splice-site-strength"),
        ("I want to run gene-set-enrichment", "gene-set-enrichment"),
        ("遺伝子セットエンリッチメントを実行したい", "gene-set-enrichment"),
        ("I want to run pairwise-sequence-alignment", "pairwise-sequence-alignment"),
        ("配列アラインメントを実行したい", "pairwise-sequence-alignment"),
        ("I want to run sequence-features / 配列特徴量解析", "sequence-features"),
    ]

    for request_text, expected_module in fixture_requests:
        result = dispatch(request_text)
        assert result["outcome"] == "dispatch"
        assert result["module"] == expected_module
        assert "handler_result" in result

    clarification = dispatch("I want sequence-features and splice-site-strength")
    assert clarification["outcome"] == "clarification"
    assert set(clarification["candidates"]) == {"sequence-features", "splice-site-strength"}

    rejected = dispatch("What is the weather today?")
    assert rejected["outcome"] == "rejected"


# @id TEST-AGENOM-022
# @verifies REQ-AGENOM-002
def test_TEST_AGENOM_022_dispatches_registered_english_and_japanese_names_only():
    from ai_genomics_scientist.dispatch import dispatch

    fixture_requests = [
        ("I want to run sequence-features", "sequence-features"),
        ("配列特徴量解析を実行したい", "sequence-features"),
        ("I want to run variant-effect-annotation", "variant-effect-annotation"),
        ("バリアント効果注釈を実行したい", "variant-effect-annotation"),
        ("I want to run splice-site-strength", "splice-site-strength"),
        ("スプライス部位強度を実行したい", "splice-site-strength"),
        ("I want to run gene-set-enrichment", "gene-set-enrichment"),
        ("遺伝子セットエンリッチメントを実行したい", "gene-set-enrichment"),
        ("I want to run pairwise-sequence-alignment", "pairwise-sequence-alignment"),
        ("配列アラインメントを実行したい", "pairwise-sequence-alignment"),
        ("I want to run sequence-features / 配列特徴量解析", "sequence-features"),
    ]

    for request_text, expected_module in fixture_requests:
        result = dispatch(request_text)
        assert result["outcome"] == "dispatch"
        assert result["module"] == expected_module
        assert "handler_result" in result

    clarification = dispatch("I want sequence-features and splice-site-strength")
    assert clarification["outcome"] == "clarification"
    assert set(clarification["candidates"]) == {"sequence-features", "splice-site-strength"}

    rejected = dispatch("What is the weather today?")
    assert rejected["outcome"] == "rejected"


# @id TEST-AGENOM-023
# @verifies REQ-AGENOM-002 REQ-AGENOM-010
def test_TEST_AGENOM_023_sequence_features_rejects_malformed_batch_shape():
    from ai_genomics_scientist.dispatch import dispatch

    missing_key = dispatch('sequence-features {"not_sequences": []}')
    assert missing_key["outcome"] == "dispatch"
    assert missing_key["handler_result"]["ok"] is False
    assert missing_key["handler_result"]["parameter"] == "sequences"
    assert missing_key["handler_result"]["constraint"] == "must be a list"

    non_list = dispatch('sequence-features {"sequences": "ATGCCCTAA"}')
    assert non_list["outcome"] == "dispatch"
    assert non_list["handler_result"]["ok"] is False
    assert non_list["handler_result"]["parameter"] == "sequences"
    assert non_list["handler_result"]["constraint"] == "must be a list"


# @id TEST-AGENOM-062
# @verifies REQ-AGENOM-002
def test_TEST_AGENOM_062_handler_accepts_structured_dict_input_from_calling_context():
    from ai_genomics_scientist.dispatch import handle_variant_effect_annotation

    result = handle_variant_effect_annotation(
        {"ref_codon": "TGG", "position": 0, "alt_base": "A"},
        "en",
    )

    assert result["ok"] is True
    assert result["run_record"]["parameters"] == {
        "ref_codon": "TGG",
        "position": 0,
        "alt_base": "A",
    }
    assert result["run_record"]["result"]["effect"] == "missense"
