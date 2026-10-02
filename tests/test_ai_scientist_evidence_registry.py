"""Tests for ai_scientist evidence registry durability and concurrency."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_handle(tmp_path, monkeypatch, project_name: str = "evidence-study"):
    monkeypatch.setenv("AI_DATA_SCIENTIST_PROJECTS_ROOT", str(tmp_path / "projects"))
    from ai_scientist.project_handle import resolve_research_project

    return resolve_research_project(project_name)


# @id TEST-AISCI-033
# @verifies REQ-AISCI-020
def test_TEST_AISCI_033_serializes_concurrent_evidence_writes_without_losing_records(
    tmp_path, monkeypatch
):
    handle = _resolve_handle(tmp_path, monkeypatch)

    import ai_scientist.evidence_registry as evidence_registry

    original_read_records = evidence_registry._read_records

    def slow_read_records(project_handle):
        records = original_read_records(project_handle)
        time.sleep(0.05)
        return records

    monkeypatch.setattr(evidence_registry, "_read_records", slow_read_records)

    errors: list[Exception] = []

    def worker(phase: str, artifact_name: str) -> None:
        artifact = handle.root / artifact_name
        artifact.write_text(phase, encoding="utf-8")
        try:
            evidence_registry.record_evidence(
                handle,
                phase,
                artifact,
                "markdown",
                _timestamp(),
            )
        except Exception as exc:  # pragma: no cover - surfaced in assertion below
            errors.append(exc)

    threads = [
        threading.Thread(
            target=worker,
            args=("research-planning", "plan.md"),
        ),
        threading.Thread(
            target=worker,
            args=("literature-review", "review.md"),
        ),
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    records = evidence_registry.query_evidence(handle)
    assert len(records) == 2
    assert {record.phase for record in records} == {"research-planning", "literature-review"}
