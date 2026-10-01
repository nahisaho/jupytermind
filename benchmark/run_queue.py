#!/usr/bin/env python3
"""Keep the benchmark queue saturated with up to three experiment runners."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import deque
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
BENCHMARK = Path(__file__).resolve().parent
RUNNER = BENCHMARK / "run_benchmark.py"
STATUS = BENCHMARK / "runs" / "status.jsonl"


def completed_ids() -> set[int]:
    if not STATUS.exists():
        return set()
    completed: set[int] = set()
    for line in STATUS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("semantic_complete"):
            completed.add(int(row["id"]))
    return completed


def external_exp23_active() -> bool:
    for process_dir in Path("/proc").iterdir():
        if not process_dir.name.isdigit():
            continue
        try:
            command = (process_dir / "cmdline").read_bytes().replace(b"\0", b" ").decode()
        except (FileNotFoundError, PermissionError, ProcessLookupError, UnicodeDecodeError):
            continue
        if (
            "run_benchmark.py --from-id 21 --to-id 23" in command
            or "jupytermind-v020-exp23" in command
        ):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("experiment_ids", nargs="+", type=int)
    args = parser.parse_args()

    queue = deque(args.experiment_ids)
    running: dict[int, subprocess.Popen[str]] = {}
    failures: list[int] = []

    while queue or running:
        already_complete = completed_ids()
        while queue and queue[0] in already_complete:
            experiment_id = queue.popleft()
            print(f"SKIP {experiment_id:02d} complete", flush=True)

        external_slots = 1 if external_exp23_active() else 0
        capacity = max(0, args.jobs - external_slots - len(running))
        while queue and capacity > 0:
            experiment_id = queue.popleft()
            process = subprocess.Popen(
                [
                    str(REPOSITORY / ".venv" / "bin" / "python"),
                    str(RUNNER),
                    "--from-id",
                    str(experiment_id),
                    "--to-id",
                    str(experiment_id),
                    "--jobs",
                    "1",
                    "--timeout",
                    str(args.timeout),
                    "--resume-incomplete",
                ],
                cwd=REPOSITORY,
                text=True,
            )
            running[experiment_id] = process
            capacity -= 1
            print(f"QUEUE START {experiment_id:02d}", flush=True)

        for experiment_id, process in list(running.items()):
            code = process.poll()
            if code is None:
                continue
            del running[experiment_id]
            if code == 0:
                print(f"QUEUE DONE {experiment_id:02d}", flush=True)
            else:
                failures.append(experiment_id)
                print(f"QUEUE FAIL {experiment_id:02d} exit={code}", flush=True)

        if queue or running:
            time.sleep(5)

    print(
        f"QUEUE COMPLETE failures={','.join(f'{value:02d}' for value in failures) or 'none'}",
        flush=True,
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
