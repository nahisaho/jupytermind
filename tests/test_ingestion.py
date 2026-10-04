"""Tests for data ingestion (REQ-AIDS-014/032)."""

import pandas as pd
import pytest

from ai_data_scientist.ingestion import IngestionResult, NetworkAllowlistError, SourceSpec, ingest


def _write_csv(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("a,b,c\n1,2,3\n4,5,6\n")
    return path


def _write_excel(tmp_path):
    path = tmp_path / "data.xlsx"
    pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]}).to_excel(path, index=False)
    return path


# @id TEST-AIDS-014
# @verifies REQ-AIDS-014
def test_TEST_AIDS_014(tmp_path):
    csv_path = _write_csv(tmp_path)
    csv_result = ingest(SourceSpec(kind="csv", location=str(csv_path)))
    assert isinstance(csv_result, IngestionResult)
    assert csv_result.row_count == 2
    assert csv_result.column_count == 3

    excel_path = _write_excel(tmp_path)
    excel_result = ingest(SourceSpec(kind="excel", location=str(excel_path)))
    assert excel_result.row_count == 3
    assert excel_result.column_count == 2

    def fake_fetcher(location):
        return pd.DataFrame({"id": [1, 2], "value": ["a", "b"]})

    api_result = ingest(
        SourceSpec(kind="api", location="https://api.example.com/data"),
        fetcher=fake_fetcher,
        allowlist=("api.example.com",),
    )
    assert api_result.row_count == 2
    assert api_result.column_count == 2


# @id TEST-AIDS-032
# @verifies REQ-AIDS-032
def test_TEST_AIDS_032():
    calls = []

    def recording_fetcher(location):
        calls.append(location)
        return pd.DataFrame({"a": [1]})

    with pytest.raises(NetworkAllowlistError):
        ingest(
            SourceSpec(kind="api", location="https://evil.example.com/data"),
            fetcher=recording_fetcher,
            allowlist=("api.example.com",),
        )
    assert calls == []

    def big_fetcher(location):
        return pd.DataFrame({"a": range(1000)})

    result = ingest(
        SourceSpec(kind="api", location="https://api.example.com/data"),
        fetcher=big_fetcher,
        allowlist=("api.example.com",),
        row_limit=10,
    )
    assert result.row_count == 10
    assert result.truncated is True


# @id TEST-AIDS-133
# @verifies REQ-AIDS-068
def test_TEST_AIDS_133_tab_delimited_csv_is_sniffed_and_split(tmp_path):
    """GitHub #42: a tab-delimited ".csv" file must not collapse into one
    concatenated column."""
    path = tmp_path / "data.csv"
    path.write_text("a\tb\tc\n1\t2\t3\n4\t5\t6\n")

    result = ingest(SourceSpec(kind="csv", location=str(path)))

    assert list(result.dataframe.columns) == ["a", "b", "c"]
    assert result.row_count == 2
    assert result.column_count == 3
    assert result.warnings == ()


# @id TEST-AIDS-134
# @verifies REQ-AIDS-068
def test_TEST_AIDS_134_semicolon_delimited_csv_is_sniffed_and_split(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("a;b;c\n1;2;3\n4;5;6\n")

    result = ingest(SourceSpec(kind="csv", location=str(path)))

    assert list(result.dataframe.columns) == ["a", "b", "c"]
    assert result.column_count == 3
    assert result.warnings == ()


# @id TEST-AIDS-135
# @verifies REQ-AIDS-068
def test_TEST_AIDS_135_comma_delimited_csv_behavior_unchanged(tmp_path):
    path = _write_csv(tmp_path)

    result = ingest(SourceSpec(kind="csv", location=str(path)))

    assert list(result.dataframe.columns) == ["a", "b", "c"]
    assert result.row_count == 2
    assert result.column_count == 3
    assert result.warnings == ()


# @id TEST-AIDS-136
# @verifies REQ-AIDS-068
def test_TEST_AIDS_136_ambiguous_single_column_tab_header_warns(tmp_path):
    """A pathological single-row-single-column-looking file whose header
    still contains a literal tab must warn about a likely delimiter
    mismatch when sniffing cannot confidently resolve a delimiter."""
    path = tmp_path / "data.csv"
    path.write_text("a\tb\n1\n")

    result = ingest(SourceSpec(kind="csv", location=str(path)))

    assert result.column_count == 1
    assert len(result.warnings) == 1
    assert "delimiter" in result.warnings[0].lower()
