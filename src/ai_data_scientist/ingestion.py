"""Data source ingestion.

Implements DES-AIDS-005: loads CSV/Excel/database/API sources into an
in-memory dataframe, enforcing a network allowlist and row-count limit for
remote sources before any data is loaded (REQ-AIDS-014, REQ-AIDS-032).
"""

from __future__ import annotations

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
    """
    if source_spec.kind == "csv":
        dataframe = pd.read_csv(source_spec.location)
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

    truncated = len(dataframe) > row_limit
    if truncated:
        dataframe = dataframe.iloc[:row_limit]

    return IngestionResult(
        dataframe=dataframe,
        row_count=len(dataframe),
        column_count=len(dataframe.columns),
        truncated=truncated,
    )
