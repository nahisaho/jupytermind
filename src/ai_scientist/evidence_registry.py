"""Durable evidence registry for ai_scientist phases."""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ai_scientist.project_handle import ResearchProjectHandle

DEFAULT_EVIDENCE_PATH = ".ai_scientist_evidence.json"
_REGISTRY_LOCKS: dict[Path, threading.Lock] = {}
_REGISTRY_LOCKS_GUARD = threading.Lock()


@dataclass(frozen=True)
class EvidenceRecord:
    """Recorded project evidence with phase attribution."""

    project: str
    phase: str
    artifact_path: str
    artifact_kind: str
    created_at: str
    metadata: dict[str, str] = field(default_factory=dict)


def _registry_path(handle: ResearchProjectHandle) -> Path:
    return handle.root / DEFAULT_EVIDENCE_PATH


def _lock_for(path: Path) -> threading.Lock:
    with _REGISTRY_LOCKS_GUARD:
        lock = _REGISTRY_LOCKS.get(path)
        if lock is None:
            lock = threading.Lock()
            _REGISTRY_LOCKS[path] = lock
        return lock


def _read_records(handle: ResearchProjectHandle) -> list[EvidenceRecord]:
    path = _registry_path(handle)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [EvidenceRecord(**item) for item in payload]


def _write_records(handle: ResearchProjectHandle, records: list[EvidenceRecord]) -> None:
    path = _registry_path(handle)
    temp_path = path.with_suffix(".tmp")
    temp_path.write_text(
        json.dumps([asdict(record) for record in records], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temp_path.replace(path)


# @id CODE-AISCI-020
# @implements REQ-AISCI-020
# @design DES-AISCI-016
def record_evidence(
    handle: ResearchProjectHandle,
    phase: str,
    artifact_path: Path | str,
    artifact_kind: str,
    timestamp: str,
    metadata: dict[str, str] | None = None,
) -> EvidenceRecord:
    """Append one evidence record atomically."""
    path = _registry_path(handle)
    with _lock_for(path):
        records = _read_records(handle)
        record = EvidenceRecord(
            project=handle.name,
            phase=phase,
            artifact_path=str(Path(artifact_path)),
            artifact_kind=artifact_kind,
            created_at=timestamp,
            metadata=metadata or {},
        )
        records.append(record)
        _write_records(handle, records)
        return record


def query_evidence(handle: ResearchProjectHandle, phase: str | None = None) -> list[EvidenceRecord]:
    """Return all evidence, optionally filtered to one phase."""
    records = _read_records(handle)
    if phase is None:
        return records
    return [record for record in records if record.phase == phase]


def latest_evidence(handle: ResearchProjectHandle, phase: str) -> EvidenceRecord | None:
    """Return the most recently recorded evidence for ``phase``."""
    records = query_evidence(handle, phase)
    return records[-1] if records else None
