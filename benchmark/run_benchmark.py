#!/usr/bin/env python3
"""Run the 50-experiment Jupytermind benchmark with isolated MCP runtimes."""

from __future__ import annotations

import argparse
import concurrent.futures
import fcntl
import json
import os
import re
import shutil
import signal
import subprocess
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import nbformat

from ai_data_scientist.notebook_audit import audit_notebook

REPOSITORY = Path(__file__).resolve().parents[1]
BENCHMARK = Path(__file__).resolve().parent
BASE_PROMPTS = Path("/home/nahisaho/kaggle/experiments/benchmark-prompts.json")
EXTRA_PROMPTS = BENCHMARK / "extra-prompts.json"
PROMPTS_SNAPSHOT = BENCHMARK / "benchmark-prompts-v0.2.0.json"
RUNS = BENCHMARK / "runs"
PROJECTS = BENCHMARK / "projects"
STATUS = RUNS / "status.jsonl"
REPORT = BENCHMARK / "white-paper-v0.2.0.md"
FIGURES = BENCHMARK / "figures"
STATUS_LOCK = threading.Lock()
REPORT_LOCK = threading.Lock()
RESULTS_START = "<!-- EXPERIMENT_RESULTS_START -->"
RESULTS_END = "<!-- EXPERIMENT_RESULTS_END -->"
STATUS_LOCK_FILE = RUNS / ".status.lock"
REPORT_LOCK_FILE = RUNS / ".report.lock"


@contextmanager
def process_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def normalize_legacy_prompt(prompt: str) -> str:
    replacements = (
        (r"公開CSV[（(][^）)]*https?://[^）)]*[）)]", "公開データ"),
        (r"公開時系列[（(][^）)]*https?://[^）)]*[）)]", "公開時系列データ"),
        (r"[（(](?:CSVミラー|CSV|公開CSV)[^）)]*https?://[^）)]*[）)]", ""),
    )
    normalized = prompt
    for pattern, replacement in replacements:
        normalized = re.sub(pattern, replacement, normalized)
    normalized = re.sub(r"https?://\S+", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.replace("（、", "（").replace(" 、", "、")
    return normalized.strip()


def load_prompts() -> list[dict[str, Any]]:
    base = json.loads(BASE_PROMPTS.read_text(encoding="utf-8"))
    extra = json.loads(EXTRA_PROMPTS.read_text(encoding="utf-8"))
    for item in base:
        item["prompt"] = normalize_legacy_prompt(item["prompt"])
        item["fallback_csv"] = item.pop("mirror", None)
    prompts = sorted(base + extra, key=lambda item: item["id"])
    ids = [item["id"] for item in prompts]
    if ids != list(range(1, 51)):
        raise RuntimeError(f"Expected experiment IDs 1..50, got {ids}.")
    PROMPTS_SNAPSHOT.write_text(
        json.dumps(prompts, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return prompts


def write_status(status: dict[str, Any]) -> None:
    with STATUS_LOCK:
        with process_lock(STATUS_LOCK_FILE):
            existing: list[dict[str, Any]] = []
            if STATUS.exists():
                for line in STATUS.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    if row.get("id") != status["id"]:
                        existing.append(row)
            existing.append(status)
            existing.sort(key=lambda row: row["id"])
            STATUS.write_text(
                "".join(
                    json.dumps(row, ensure_ascii=False) + "\n"
                    for row in existing
                ),
                encoding="utf-8",
            )


def rebuild_report() -> None:
    report = REPORT.read_text(encoding="utf-8")
    if RESULTS_START not in report or RESULTS_END not in report:
        raise RuntimeError("White paper is missing experiment result markers.")
    sections: list[tuple[int, str]] = []
    for section_path in RUNS.glob("*/report-section.md"):
        status_path = section_path.parent / "status.json"
        if not status_path.exists():
            continue
        status = json.loads(status_path.read_text(encoding="utf-8"))
        sections.append((int(status["id"]), section_path.read_text(encoding="utf-8").strip()))
    sections.sort(key=lambda entry: entry[0])
    rendered = "\n\n".join(section for _, section in sections)
    before, remainder = report.split(RESULTS_START, 1)
    _, after = remainder.split(RESULTS_END, 1)
    REPORT.write_text(
        f"{before}{RESULTS_START}\n\n{rendered}\n\n{RESULTS_END}{after}",
        encoding="utf-8",
    )


def build_mcp_config(run_dir: Path) -> str:
    config = {
        "mcpServers": {
            "jupyter": {
                "type": "stdio",
                "command": str(REPOSITORY / ".venv" / "bin" / "python"),
                "args": [
                    str(BENCHMARK / "mcp_launcher.py"),
                    "--workspace",
                    str(REPOSITORY),
                    "--log",
                    str(run_dir / "jupyter.log"),
                ],
                "tools": ["*"],
            }
        }
    }
    return json.dumps(config)


def stop_process_group(process: subprocess.Popen[str], log: Any, reason: str) -> None:
    log.write(f"\n[runner] stopping process group: {reason}\n")
    log.flush()
    process_group_id = process.pid
    try:
        os.killpg(process_group_id, signal.SIGTERM)
    except ProcessLookupError:
        return
    if process.poll() is None:
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            pass
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            os.killpg(process_group_id, 0)
        except ProcessLookupError:
            return
        time.sleep(0.5)
    try:
        os.killpg(process_group_id, signal.SIGKILL)
    except ProcessLookupError:
        return
    else:
        log.write("[runner] process group ignored SIGTERM; sending SIGKILL\n")
        log.flush()


def run_command(
    command: list[str],
    log_path: Path,
    timeout_s: int,
    environment: dict[str, str],
    completion_path: Path | None = None,
    completion_stable_s: int = 30,
    completion_grace_s: int = 60,
) -> tuple[int, float, str]:
    started = time.monotonic()
    termination = "exited"
    last_artifact_state: tuple[int, int] | None = None
    artifact_stable_since: float | None = None
    artifact_complete_since: float | None = None
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command,
            cwd=REPOSITORY,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        deadline = started + timeout_s
        while process.poll() is None:
            now = time.monotonic()
            if completion_path is not None and completion_path.exists():
                stat = completion_path.stat()
                artifact_state = (stat.st_size, stat.st_mtime_ns)
                if artifact_state == last_artifact_state:
                    artifact_stable_since = artifact_stable_since or now
                else:
                    last_artifact_state = artifact_state
                    artifact_stable_since = None
                    artifact_complete_since = None

                if (
                    artifact_stable_since is not None
                    and now - artifact_stable_since >= completion_stable_s
                ):
                    completion = benchmark_completion(completion_path)
                    if completion.get("ready"):
                        artifact_complete_since = artifact_complete_since or now
                    else:
                        artifact_complete_since = None

                if (
                    artifact_complete_since is not None
                    and now - artifact_complete_since >= completion_grace_s
                ):
                    termination = "artifact_complete_cutoff"
                    stop_process_group(
                        process,
                        log,
                        "Notebook remained stable and passed semantic audit",
                    )
                    return 0, round(time.monotonic() - started, 1), termination

            if now >= deadline:
                termination = "timeout"
                stop_process_group(process, log, f"exceeded {timeout_s}s")
                return 124, round(time.monotonic() - started, 1), termination
            time.sleep(2)
        code = process.returncode
        stop_process_group(process, log, "Copilot CLI exited; cleaning descendant runtimes")
    return code, round(time.monotonic() - started, 1), termination


def wait_for_stable_artifact(path: Path, timeout_s: int = 60, stable_s: int = 5) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_s
    previous: tuple[int, int] | None = None
    stable_since: float | None = None
    while time.monotonic() < deadline:
        if not path.exists():
            time.sleep(1)
            continue
        stat = path.stat()
        current = (stat.st_size, stat.st_mtime_ns)
        if current == previous:
            stable_since = stable_since or time.monotonic()
            if time.monotonic() - stable_since >= stable_s:
                return {
                    "stable": True,
                    "size": stat.st_size,
                    "mtime": datetime.fromtimestamp(
                        stat.st_mtime, tz=timezone.utc
                    ).isoformat(),
                }
        else:
            previous = current
            stable_since = None
        time.sleep(1)
    return {"stable": False, "exists": path.exists()}


def audit_artifact(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "semantic_complete": False, "error": "notebook_missing"}
    try:
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
    except Exception as error:
        return {
            "exists": True,
            "semantic_complete": False,
            "error": f"nbformat_invalid: {error}",
        }

    report = audit_notebook(path, visual_audit=True)
    return {
        "exists": True,
        "semantic_complete": report.ok,
        "nbformat_valid": report.nbformat_valid,
        "code_cells": report.code_cell_count,
        "executed_code_cells": report.executed_code_cell_count,
        "unexecuted_cells": list(report.unexecuted_cell_indices),
        "error_cells": list(report.error_cell_indices),
        "chart_cells": list(report.chart_cell_indices),
        "insight_cells": report.insight_cell_count,
        "findings": [
            {
                "severity": finding.severity,
                "message": finding.message,
                "cell_index": finding.cell_index,
            }
            for finding in report.findings
        ],
        "visual_findings": [
            {
                "severity": finding.severity,
                "code": finding.code,
                "chart_cell_index": finding.chart_cell_index,
                "details": finding.details,
            }
            for finding in report.visual_findings
        ],
    }


def benchmark_completion(path: Path) -> dict[str, Any]:
    audit = audit_artifact(path)
    requirements = {
        "structural_audit_ok": bool(audit.get("semantic_complete")),
        "minimum_executed_code_cells": audit.get("executed_code_cells", 0) >= 5,
        "has_chart_output": bool(audit.get("chart_cells")),
        "has_evidence_backed_insight": audit.get("insight_cells", 0) >= 1,
        "has_iteration_history": False,
        "has_module_usage_record": False,
        "has_improvement_candidate_record": False,
        "has_notebook_audit_call": False,
    }
    if path.exists():
        notebook = nbformat.read(path, as_version=4)
        markdown = "\n".join(
            cell.get("source", "")
            for cell in notebook.cells
            if cell.get("cell_type") == "markdown"
        )
        code = "\n".join(
            cell.get("source", "")
            for cell in notebook.cells
            if cell.get("cell_type") == "code"
        )
        requirements.update(
            {
                "has_iteration_history": "反復依頼履歴" in markdown,
                "has_module_usage_record": "使用したJupytermindモジュール" in markdown,
                "has_improvement_candidate_record": "Jupytermind改善候補" in markdown,
                "has_notebook_audit_call": "audit_notebook" in code,
            }
        )
    return {
        "ready": all(requirements.values()),
        "requirements": requirements,
        "audit": audit,
    }


def build_initial_prompt(item: dict[str, Any], notebook: str, run_id: str) -> str:
    fallback_csv = item.get("fallback_csv")
    if fallback_csv:
        fallback_requirement = (
            "Kaggle APIで対応データを検索・取得できなかった場合に限り、"
            "`/home/nahisaho/kaggle/experiments/white-paper.md`に記載された旧実験の"
            f"公開CSV `{fallback_csv}` を取得して実験を継続してください。"
            "その場合はKaggle APIの失敗内容、フォールバックした理由、CSV URL、取得日時、"
            "SHA-256をNotebookに記録し、公開CSVとKaggle掲載版の完全な同一性は保証されない"
            "ことを明記してください。"
        )
    else:
        fallback_requirement = (
            "Kaggle APIで対応データを取得できない場合は、"
            "`/home/nahisaho/kaggle/experiments/white-paper.md`を確認してください。"
            "同じデータセットの公開CSVが同稿に明記されている場合だけ、そのURLへ"
            "フォールバックしてください。対応するCSVを確認できない場合は、別データを"
            "推測で選ばず、取得失敗として記録してください。"
        )
    common_requirement = (
        f"{item['prompt']} Kaggle参照先: {item['kaggle']}。"
        "インストール済みkaggle Python SDKを使い、NotebookのJupyter MCP実行セル内で"
        "`KaggleApi().authenticate()`、`dataset_list(search=...)`、"
        "`dataset_list_files(...)`、必要に応じて`dataset_download_file(...)`を"
        "呼び出し、Kaggle上の対応する公開データを検索・取得してください。"
        "owner/dataset slug、取得ファイル名、取得日、"
        "ファイルSHA-256をNotebookに記録してください。APIトークンをセル出力・"
        "Notebook・ログへ表示しないでください。分析・API取得コードの実行はJupyter "
        "MCPだけを使い、端末コマンド、subprocess、外部スクリプト起動、作業エージェント"
        "への委譲は行わないでください。"
    )
    execution_requirement = (
        f"保存先は {notebook} としてください。run_idは `{run_id}` です。長時間処理の"
        "開始前にlifecycle.register_runを呼び、実行・書込みフェーズを記録し、終了時に"
        "completedまたはfailedを記録してください。データ定義manifest、分析前提manifest、"
        "意味的な異常検査、妥当な範囲の感度分析を使い、適用できない機能は理由を記録して"
        "ください。図表はvisual_audit=Trueで監査してください。Notebookには"
        "「使用したJupytermindモジュール」節を設け、直接import・呼び出したモジュール名、"
        "関数名、使用目的を記録してください。間接利用は使用済みに含めないでください。"
        "Jupytermindの不具合または機能不足が疑われた場合は「Jupytermind改善候補」節を"
        "設け、分類、再現条件、期待する挙動、実際の挙動、影響、回避策、関係するセルと"
        "ログを記録してください。Copilot CLI、Kaggle API、ベンチマークランナーに固有の"
        "問題とは切り分け、候補がなければ「なし」と記録してください。"
        "初回分析後、自分で結果を読み直し、結論に実質的な影響を与える未解決点があれば"
        "自然言語の追加依頼文を作成し、Notebookの「反復依頼履歴」に原文のまま記録して"
        "実行してください。価値ある追加分析がなくなるまで最大3回繰り返し、各反復の"
        "選定理由・結果・証拠・残る限界を報告してください。最後に全コードセルを上から"
        "再実行し、notebook_auditとライフサイクル状態を記録してください。"
    )
    return common_requirement + fallback_requirement + execution_requirement


def build_followup_prompt(item: dict[str, Any], notebook: str, run_id: str) -> str:
    return (
        f"{item['dataset']}のNotebook `{notebook}` を確認してください。run_idは"
        f"`{run_id}`です。既存セルを保持し、初回分析とAI自身が生成した反復依頼が"
        "問いに答えているか、データ定義、分析前提、異常値、感度、可視化、証拠manifest"
        "の観点から再評価してください。結論に影響する未解決点がある場合だけ、新しい"
        "自然言語の追加依頼文を自分で作成・記録・実行し、合計最大3回までとしてください。"
        "Notebookの「使用したJupytermindモジュール」節も更新し、直接使用したモジュール名、"
        "関数名、使用目的を記録してください。"
        "「Jupytermind改善候補」節も再評価し、再現性、利用者への影響、期待する受け入れ条件を"
        "追記してください。外部ツール固有の問題はJupytermindの候補から除外してください。"
        "終了時に全コードセルを上から再実行し、visual_audit=Trueのnotebook_audit、"
        "Kaggle owner/slug・取得ファイル・SHA-256、lifecycleの完了状態を確認してください。"
    )


def build_report_prompt(
    item: dict[str, Any],
    notebook_relative: str,
    run_dir: Path,
) -> str:
    section_path = run_dir / "report-section.md"
    issue_path = run_dir / "issue-candidate.json"
    return (
        f"Jupytermind v0.2.0ベンチマークの実験{item['id']:02d} "
        f"（{item['dataset']}）の結果をQiita書式の日本語でまとめてください。"
        f"Notebookは `{notebook_relative}`、初回プロンプトは"
        f"`{run_dir / 'initial-prompt.md'}`、初回ログは`{run_dir / 'initial.log'}`、"
        f"追加確認ログは`{run_dir / 'followup.log'}`、監査状態は"
        f"`{run_dir / 'status.json'}`です。これらの実ファイルだけを証拠にし、"
        "未確認の数値や成功状態を推測しないでください。"
        "status.jsonの`documentation_complete`、`semantic_complete`、"
        "`report_exit_code`は、この節を生成する前の文書化状態を表すため、"
        "実験分析の見出し、結論、失敗判定には使用しないでください。分析完了は"
        "`analysis_complete`、`final_completion`、Notebook内容から判断してください。"
        " `/home/nahisaho/kaggle/experiments/white-paper2.md` の各実験節と同じ詳細度・"
        "書式で、課題、初回プロンプト全文、使用したJupytermindモジュール、初回指示、"
        "データ取得、初回結果、AIが生成した各追加依頼の原文・選定理由・結果、"
        "最終結論、監査・再現性、限界、失敗があれば失敗内容を記載してください。"
        "Skill名ではなく、Notebookで直接import・呼び出したJupytermindモジュール名、"
        "関数名、使用目的だけを記載してください。"
        "初回プロンプトは、データセットと問いおよび共通制約からAIが自動生成したもの"
        "であることを明記してください。人間が全文を個別作成したように記述しないでください。"
        "Notebook内のPNG図表を抽出し、英語のファイル名で"
        f"`{FIGURES}`へ保存してください。節内では`figures/<filename>`で参照し、"
        f"図番号は付けず、説明的なキャプションを付けてください。ファイル名は"
        f"`exp-{item['id']:02d}-`で始め、他実験と衝突させないでください。"
        "Jupytermindの改善候補は、外部ランナー、Copilot CLI、Kaggle APIの問題と"
        "切り分けてください。候補がある場合だけ、分類、再現手順、期待する挙動、"
        "実際の挙動、影響、証拠、受け入れ条件をJSONオブジェクトとして"
        f"`{issue_path}`に保存してください。候補がなければJSONのnullを保存してください。"
        f"完成した実験節だけを `{section_path}` に保存してください。"
        "white-paper-v0.2.0.md自体は編集しないでください。"
    )


def document_experiment(
    item: dict[str, Any],
    copilot: str,
    notebook_relative: str,
    run_dir: Path,
    environment: dict[str, str],
    status: dict[str, Any],
) -> dict[str, Any]:
    report_prompt = build_report_prompt(item, notebook_relative, run_dir)
    (run_dir / "report-prompt.md").write_text(report_prompt, encoding="utf-8")
    with REPORT_LOCK:
        with process_lock(REPORT_LOCK_FILE):
            FIGURES.mkdir(parents=True, exist_ok=True)
            report_code, report_seconds, report_termination = run_command(
                [
                    copilot,
                    "-C",
                    str(REPOSITORY),
                    "-p",
                    report_prompt,
                    "--allow-all-tools",
                    "--allow-all-paths",
                    "--allow-all-urls",
                    "--silent",
                    "--model",
                    "gpt-6.1-sol",
                    "--name",
                    f"jupytermind-v020-exp{item['id']:02d}-report",
                ],
                run_dir / "report.log",
                900,
                environment,
            )
            section_path = run_dir / "report-section.md"
            documentation_complete = bool(
                report_code == 0
                and section_path.exists()
                and section_path.stat().st_size > 0
            )
            if documentation_complete:
                rebuild_report()

    status.update(
        {
            "report_exit_code": report_code,
            "report_seconds": report_seconds,
            "report_termination": report_termination,
            "documentation_complete": documentation_complete,
            "semantic_complete": bool(
                status.get("analysis_complete") and documentation_complete
            ),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    (run_dir / "status.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_status(status)
    return status


def run_experiment(
    item: dict[str, Any],
    copilot: str,
    timeout_s: int,
) -> dict[str, Any]:
    experiment_id = item["id"]
    slug = f"kaggle-v020-{item['slug']}"
    notebook_relative = f"benchmark/projects/{slug}/notebooks/{slug}.ipynb"
    notebook_path = REPOSITORY / notebook_relative
    run_id = f"v020-exp-{experiment_id:02d}"
    run_dir = RUNS / f"{experiment_id:02d}-{item['slug']}"
    run_dir.mkdir(parents=True, exist_ok=True)
    mcp_config = build_mcp_config(run_dir)
    environment = {
        **os.environ,
        "AI_DATA_SCIENTIST_PROJECTS_ROOT": str(PROJECTS),
        "PATH": f"{REPOSITORY / '.venv' / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}",
    }
    initial_prompt = build_initial_prompt(item, notebook_relative, run_id)
    followup_prompt = build_followup_prompt(item, notebook_relative, f"{run_id}-followup")
    (run_dir / "initial-prompt.md").write_text(initial_prompt, encoding="utf-8")
    (run_dir / "followup-prompt.md").write_text(followup_prompt, encoding="utf-8")

    initial_code, initial_seconds, initial_termination = run_command(
        [
            copilot,
            "-C",
            str(REPOSITORY),
            "--additional-mcp-config",
            mcp_config,
            "-p",
            initial_prompt,
            "--allow-all-tools",
            "--allow-all-paths",
            "--allow-all-urls",
            "--silent",
            "--model",
            "gpt-6.1-sol",
            "--name",
            f"jupytermind-v020-exp{experiment_id:02d}",
        ],
        run_dir / "initial.log",
        timeout_s,
        environment,
        completion_path=notebook_path,
    )
    initial_stability = wait_for_stable_artifact(notebook_path)
    initial_audit = audit_artifact(notebook_path)

    followup_code: int | None = None
    followup_seconds: float | None = None
    followup_termination: str | None = None
    if initial_code == 0 and initial_audit.get("exists"):
        followup_code, followup_seconds, followup_termination = run_command(
            [
                copilot,
                "-C",
                str(REPOSITORY),
                "--additional-mcp-config",
                mcp_config,
                "-p",
                followup_prompt,
                "--allow-all-tools",
                "--allow-all-paths",
                "--allow-all-urls",
                "--silent",
                "--model",
                "gpt-6.1-sol",
                "--name",
                f"jupytermind-v020-exp{experiment_id:02d}-followup",
            ],
            run_dir / "followup.log",
            timeout_s,
            environment,
            completion_path=notebook_path,
        )

    final_stability = wait_for_stable_artifact(notebook_path)
    final_audit = audit_artifact(notebook_path)
    final_completion = benchmark_completion(notebook_path)
    analysis_complete = bool(
        initial_code == 0
        and followup_code == 0
        and final_stability.get("stable")
        and final_completion.get("ready")
    )
    status = {
        "id": experiment_id,
        "dataset": item["dataset"],
        "kaggle": item["kaggle"],
        "notebook": notebook_relative,
        "run_id": run_id,
        "initial_exit_code": initial_code,
        "initial_seconds": initial_seconds,
        "initial_termination": initial_termination,
        "initial_stability": initial_stability,
        "initial_audit": initial_audit,
        "followup_exit_code": followup_code,
        "followup_seconds": followup_seconds,
        "followup_termination": followup_termination,
        "final_stability": final_stability,
        "final_audit": final_audit,
        "final_completion": final_completion,
        "analysis_complete": analysis_complete,
        "documentation_complete": False,
        "semantic_complete": False,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    (run_dir / "status.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_status(status)

    return document_experiment(
        item,
        copilot,
        notebook_relative,
        run_dir,
        environment,
        status,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-id", type=int, default=1)
    parser.add_argument("--to-id", type=int, default=50)
    parser.add_argument("--jobs", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=1200)
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Generate or regenerate report sections from existing experiment artifacts.",
    )
    parser.add_argument(
        "--resume-incomplete",
        action="store_true",
        help="Skip semantically complete experiments and document analysis-complete runs.",
    )
    args = parser.parse_args()

    if args.jobs < 1:
        raise ValueError("--jobs must be at least 1.")
    copilot = shutil.which("copilot")
    if copilot is None:
        raise RuntimeError("Copilot CLI executable was not found on PATH.")

    RUNS.mkdir(parents=True, exist_ok=True)
    PROJECTS.mkdir(parents=True, exist_ok=True)
    prompts = [
        item
        for item in load_prompts()
        if args.from_id <= item["id"] <= args.to_id
    ]
    if not prompts:
        raise RuntimeError("No experiments matched the selected ID range.")

    if args.report_only:
        failures = 0
        environment = {
            **os.environ,
            "AI_DATA_SCIENTIST_PROJECTS_ROOT": str(PROJECTS),
            "PATH": f"{REPOSITORY / '.venv' / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}",
        }
        for item in prompts:
            run_dir = RUNS / f"{item['id']:02d}-{item['slug']}"
            status_path = run_dir / "status.json"
            if not status_path.exists():
                failures += 1
                print(f"ERROR {item['id']:02d}: status.json is missing", flush=True)
                continue
            status = json.loads(status_path.read_text(encoding="utf-8"))
            status.setdefault(
                "analysis_complete",
                bool(status.get("final_completion", {}).get("ready")),
            )
            status = document_experiment(
                item,
                copilot,
                status["notebook"],
                run_dir,
                environment,
                status,
            )
            failures += int(not status["documentation_complete"])
            print(
                f"{'DOCUMENTED' if status['documentation_complete'] else 'REPORT FAIL'} "
                f"{item['id']:02d} {item['dataset']}",
                flush=True,
            )
        return 1 if failures else 0

    if args.resume_incomplete:
        pending: list[dict[str, Any]] = []
        environment = {
            **os.environ,
            "AI_DATA_SCIENTIST_PROJECTS_ROOT": str(PROJECTS),
            "PATH": f"{REPOSITORY / '.venv' / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}",
        }
        for item in prompts:
            run_dir = RUNS / f"{item['id']:02d}-{item['slug']}"
            status_path = run_dir / "status.json"
            if not status_path.exists():
                pending.append(item)
                continue
            status = json.loads(status_path.read_text(encoding="utf-8"))
            if status.get("semantic_complete"):
                print(f"SKIP {item['id']:02d} {item['dataset']} complete", flush=True)
                continue
            if status.get("analysis_complete"):
                documented = document_experiment(
                    item,
                    copilot,
                    status["notebook"],
                    run_dir,
                    environment,
                    status,
                )
                if documented.get("semantic_complete"):
                    print(f"DOCUMENTED {item['id']:02d} {item['dataset']}", flush=True)
                    continue
            pending.append(item)
        prompts = pending
        if not prompts:
            print("BATCH COMPLETE: no incomplete experiments remain", flush=True)
            return 0

    failures = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = {
            executor.submit(run_experiment, item, copilot, args.timeout): item
            for item in prompts
        }
        for future in concurrent.futures.as_completed(futures):
            item = futures[future]
            try:
                status = future.result()
            except Exception as error:
                failures += 1
                print(f"ERROR {item['id']:02d} {item['dataset']}: {error}", flush=True)
                continue
            outcome = "DONE" if status["semantic_complete"] else "FAIL"
            failures += int(not status["semantic_complete"])
            print(
                f"{outcome} {item['id']:02d} {item['dataset']} "
                f"initial={status['initial_exit_code']} "
                f"followup={status['followup_exit_code']}",
                flush=True,
            )

    completed = len(prompts) - failures
    print(f"BATCH COMPLETE: {completed}/{len(prompts)} semantically complete", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
