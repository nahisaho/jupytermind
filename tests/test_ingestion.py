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
