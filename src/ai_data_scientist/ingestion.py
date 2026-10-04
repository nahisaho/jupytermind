"""Data source ingestion.

Implements DES-AIDS-005: loads CSV/Excel/database/API sources into an
in-memory dataframe. A network allowlist is enforced before any remote
call; a row-count limit is applied to the resulting dataframe after a
remote (database/API) fetch completes, bounding downstream processing —
not the fetch itself — and never applies to local CSV/Excel sources
(REQ-AIDS-014, REQ-AIDS-032; GitHub #57).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from urllib.parse import urlparse

import pandas as pd

DEFAULT_ROW_LIMIT = 100_000
_REMOTE_KINDS = ("api", "database")


class NetworkAllowlistError(ValueError):
    """Raised when a remote source host is not in the configured allowlist."""


@dataclass(frozen=True)
class SourceSpec:
    """Describes a single ingestion request."""

    kind: str  # "csv" | "excel" | "api" | "database"
    location: str


@dataclass(frozen=True)
class IngestionResult:
    dataframe: pd.DataFrame
    row_count: int
    column_count: int
    truncated: bool
    warnings: tuple[str, ...] = ()


# @id CODE-AIDS-088
# @implements REQ-AIDS-068
# @design DES-AIDS-056
def _sniff_csv_delimiter(path: str) -> tuple[str | None, bool]:
    """Return ``(delimiter, sniff_succeeded)`` for the CSV file at ``path``.

    Reads a bounded text sample and attempts ``csv.Sniffer().sniff`` over
    comma/tab/semicolon candidates (DES-AIDS-056); on ``csv.Error`` (an
    ambiguous sample), returns ``(None, False)`` so the caller falls back to
    the existing comma-default behavior.
    """
    with open(path, encoding="utf-8", errors="replace") as handle:
        sample = handle.read(8192)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
    except csv.Error:
        return None, False
    return dialect.delimiter, True


# @id CODE-AIDS-014
# @implements REQ-AIDS-014
# @design DES-AIDS-005
# @id CODE-AIDS-032
# @implements REQ-AIDS-032
# @design DES-AIDS-005
def ingest(
    source_spec: SourceSpec,
    fetcher=None,
    allowlist: tuple[str, ...] = (),
    row_limit: int = DEFAULT_ROW_LIMIT,
) -> IngestionResult:
    """Load ``source_spec`` into a dataframe, applying ingestion safety rules.

    For remote ``kind`` values ("api"/"database") the host is checked
    against ``allowlist`` *before* ``fetcher`` is invoked, and the resulting
    dataframe is truncated to ``row_limit`` rows if it exceeds that limit.
    Local ``kind`` values ("csv"/"excel") are never truncated by
    ``row_limit``: that limit is a remote-source safety control
    (REQ-AIDS-032), not a general ingestion cap, so a local file is always
    loaded in full (GitHub #57).
    """
    warnings: tuple[str, ...] = ()
    if source_spec.kind == "csv":
        delimiter, sniffed = _sniff_csv_delimiter(source_spec.location)
        dataframe = pd.read_csv(source_spec.location, sep=delimiter if sniffed else ",")
        if (
            not sniffed
            and len(dataframe.columns) == 1
            and ("\t" in dataframe.columns[0] or ";" in dataframe.columns[0])
        ):
            warnings = (
                f"CSV was parsed with the comma fallback as a single column named "
                f"{dataframe.columns[0]!r}; the file may actually use a tab or "
                "semicolon delimiter instead.",
            )
    elif source_spec.kind == "excel":
        dataframe = pd.read_excel(source_spec.location)
    elif source_spec.kind in _REMOTE_KINDS:
        host = urlparse(source_spec.location).hostname
        if host not in allowlist:
            raise NetworkAllowlistError(
                f"Host '{host}' is not in the configured allowlist "
                f"(許可されていない接続先ホストです): {source_spec.location}"
            )
        if fetcher is None:
            raise ValueError("A fetcher callable is required for remote ingestion sources.")
        dataframe = fetcher(source_spec.location)
    else:
        raise ValueError(f"Unsupported ingestion source kind: {source_spec.kind!r}")

    # GitHub #57: row_limit is a remote-source safety control (REQ-AIDS-032);
    # local csv/excel files must never be silently truncated by it.
    truncated = source_spec.kind in _REMOTE_KINDS and len(dataframe) > row_limit
    if truncated:
        dataframe = dataframe.iloc[:row_limit]

    return IngestionResult(
        dataframe=dataframe,
        row_count=len(dataframe),
        column_count=len(dataframe.columns),
        truncated=truncated,
        warnings=warnings,
    )
