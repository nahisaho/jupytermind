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


# @id TEST-AIDS-203
# @verifies REQ-AIDS-032
def test_TEST_AIDS_203_local_csv_is_never_row_limit_truncated(tmp_path):
    """GitHub #57: row_limit is a remote-source safety control (REQ-AIDS-032
    only names "a database or API source"); a local CSV file larger than
    row_limit must still be loaded in full, not silently truncated."""
    path = tmp_path / "big.csv"
    path.write_text("a\n" + "\n".join(str(i) for i in range(150)))

    result = ingest(SourceSpec(kind="csv", location=str(path)), row_limit=100)

    assert result.row_count == 150
    assert result.truncated is False


# @id TEST-AIDS-204
# @verifies REQ-AIDS-032
def test_TEST_AIDS_204_local_excel_is_never_row_limit_truncated(tmp_path):
    """GitHub #57: same guarantee as TEST-AIDS-203, for "excel"."""
    path = tmp_path / "big.xlsx"
    pd.DataFrame({"a": range(150)}).to_excel(path, index=False)

    result = ingest(SourceSpec(kind="excel", location=str(path)), row_limit=100)

    assert result.row_count == 150
    assert result.truncated is False


# ---------------------------------------------------------------------------
# REQ-AIDS-099 / DES-AIDS-099 (GitHub #76): CSV ingestion falls back through
# utf-8 -> cp1252 -> latin-1 instead of raising UnicodeDecodeError.
# ---------------------------------------------------------------------------


# @id TEST-AIDS-346
# @verifies REQ-AIDS-099
def test_TEST_AIDS_346_utf8_csv_has_no_encoding_warning(tmp_path):
    """Scenario: a valid UTF-8 CSV with non-ASCII text loads via the first
    (utf-8) attempt; no encoding-fallback warning is added and behavior is
    unchanged from before REQ-AIDS-099 (no regression for the common case)."""
    path = tmp_path / "data.csv"
    path.write_text("name,note\nalice,caf\u00e9\n", encoding="utf-8")

    result = ingest(SourceSpec(kind="csv", location=str(path)))

    assert result.row_count == 1
    assert result.dataframe["note"].iloc[0] == "caf\u00e9"
    assert result.warnings == ()


# @id TEST-AIDS-347
# @verifies REQ-AIDS-099
def test_TEST_AIDS_347_windows_codepage_csv_falls_back_and_warns(tmp_path):
    """Scenario: a cp1252-encoded CSV containing byte 0x80 (Euro sign, not
    valid UTF-8) fails the utf-8 attempt and succeeds on the cp1252 retry;
    exactly one warning matching the cp1252 template is added, and the
    decoded cell contains the correct cp1252 character."""
    path = tmp_path / "data.csv"
    path.write_bytes(b"name,note\nalice,\x80\n")

    result = ingest(SourceSpec(kind="csv", location=str(path)))

    assert result.row_count == 1
    assert result.dataframe["note"].iloc[0] == "\u20ac"  # Euro sign
    assert result.warnings == (
        f"CSV at {str(path)!r} is not valid UTF-8; decoded using the "
        "'cp1252' fallback encoding instead.",
    )


# @id TEST-AIDS-348
# @verifies REQ-AIDS-099
def test_TEST_AIDS_348_latin1_csv_falls_back_and_warns(tmp_path):
    """Scenario: a file containing byte 0x81, which is undefined in cp1252
    (raises UnicodeDecodeError under it) but is a valid Latin-1 code point,
    fails both utf-8 and cp1252 and succeeds on the latin-1 last resort;
    exactly one warning matching the latin-1 template is added."""
    path = tmp_path / "data.csv"
    path.write_bytes(b"name,note\nalice,\x81\n")

    result = ingest(SourceSpec(kind="csv", location=str(path)))

    assert result.row_count == 1
    assert result.dataframe["note"].iloc[0] == "\x81"
    assert result.warnings == (
        f"CSV at {str(path)!r} is not valid UTF-8 or cp1252; decoded using "
        "the 'latin-1' last-resort fallback encoding instead.",
    )


# @id TEST-AIDS-349
# @verifies REQ-AIDS-099
def test_TEST_AIDS_349_delimiter_and_encoding_warnings_both_present_in_order(tmp_path):
    """Scenario: a file that both fails confident delimiter sniffing (a
    single ambiguous tab-containing header) and requires the cp1252
    encoding fallback must carry both warnings, with the pre-existing
    delimiter-sniff warning appearing first."""
    path = tmp_path / "data.csv"
    path.write_bytes(b"a\tb\n\x80\n")

    result = ingest(SourceSpec(kind="csv", location=str(path)))

    assert result.warnings == (
        "CSV was parsed with the comma fallback as a single column named "
        "'a\\tb'; the file may actually use a tab or semicolon delimiter "
        "instead.",
        f"CSV at {str(path)!r} is not valid UTF-8; decoded using the "
        "'cp1252' fallback encoding instead.",
    )


# @id TEST-AIDS-350
# @verifies REQ-AIDS-099
def test_TEST_AIDS_350_non_csv_kinds_unaffected(tmp_path):
    """Scenario: encoding-fallback handling is scoped to kind="csv"; excel
    and api sources are loaded exactly as before (sanity check that the fix
    did not touch the excel/api/database branches)."""
    path = _write_excel(tmp_path)

    excel_result = ingest(SourceSpec(kind="excel", location=str(path)))

    assert excel_result.warnings == ()
    assert excel_result.row_count == 3

    def fake_fetcher(location):
        return pd.DataFrame({"id": [1, 2], "value": ["a", "b"]})

    api_result = ingest(
        SourceSpec(kind="api", location="https://api.example.com/data"),
        fetcher=fake_fetcher,
        allowlist=("api.example.com",),
    )

    assert api_result.warnings == ()
    assert api_result.row_count == 2


# @id TEST-AIDS-351
# @verifies REQ-AIDS-099
def test_TEST_AIDS_351_missing_file_still_raises_file_not_found(tmp_path):
    """Scenario: a non-existent path still raises FileNotFoundError from the
    first (utf-8) attempt; the fallback chain does not mask or retry a
    non-UnicodeDecodeError failure."""
    missing = tmp_path / "does-not-exist.csv"

    with pytest.raises(FileNotFoundError):
        ingest(SourceSpec(kind="csv", location=str(missing)))
