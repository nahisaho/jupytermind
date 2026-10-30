"""Tests for Japanese NLP via GiNZA (REQ-AIDS-023)."""

import ast
import re
from importlib.metadata import version
from pathlib import Path

import spacy
from packaging.requirements import Requirement

from ai_data_scientist.japanese_nlp import JapaneseNLPResult, analyze_japanese_text

_REFERENCE_SENTENCE = "今日は良い天気です。"
_SCRIPTS = Path(__file__).resolve().parents[1] / ".github/skills/japanese-prose/scripts"


def _script_dependencies(script):
    source = (_SCRIPTS / script).read_text(encoding="utf-8")
    metadata = source.split("# /// script\n", 1)[1].split("# ///", 1)[0]
    metadata = "\n".join(line.removeprefix("# ") for line in metadata.splitlines())
    match = re.search(r"dependencies\s*=\s*(\[.*?\])", metadata, re.DOTALL)
    assert match is not None, f"{script} must declare inline dependencies"
    requirements = [Requirement(item) for item in ast.literal_eval(match.group(1))]
    return {item.name: item for item in requirements}


# @id TEST-AIDS-023
# @verifies REQ-AIDS-023
def test_TEST_AIDS_023():
    result = analyze_japanese_text(_REFERENCE_SENTENCE, operation="tokenize")

    nlp = spacy.load("ja_ginza")
    doc = nlp(_REFERENCE_SENTENCE)
    reference_tokens = [tok.text for tok in doc]
    reference_pos = [tok.pos_ for tok in doc]

    assert result.tokens == reference_tokens
    assert result.pos_tags == reference_pos


# @id TEST-GINZA53-002
# @verifies REQ-GINZA53-002
def test_TEST_GINZA53_002_standalone_scripts_require_ginza_53():
    for script in ("lint.py", "terms.py", "test_engine.py"):
        dependencies = _script_dependencies(script)
        for package in ("ginza", "ja-ginza"):
            specifier = dependencies[package].specifier
            assert "5.3.0" in specifier, (script, package)
            assert "5.2.0" not in specifier, (script, package)
            assert "5.4.0" not in specifier, (script, package)
        spacy_specifier = dependencies["spacy"].specifier
        assert "3.8.16" in spacy_specifier
        assert "3.8.15" not in spacy_specifier
        assert "4.0.0" not in spacy_specifier


# @id TEST-GINZA53-003
# @verifies REQ-GINZA53-003
def test_TEST_GINZA53_003_model_and_entrypoints_are_compatible():
    for script in ("lint.py", "terms.py", "test_engine.py"):
        dependencies = _script_dependencies(script)
        for package in ("ginza", "ja-ginza"):
            assert version(package).startswith("5.3.")
            assert version(package) in dependencies[package].specifier, (script, package)
            assert "5.2.0" not in dependencies[package].specifier

    result = analyze_japanese_text(_REFERENCE_SENTENCE)
    reference = spacy.load("ja_ginza")(_REFERENCE_SENTENCE)
    assert isinstance(result, JapaneseNLPResult)
    assert result.tokens == [token.text for token in reference]
    assert result.pos_tags == [token.pos_ for token in reference]
