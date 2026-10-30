"""Verify provenance and readiness without changing native SDD evidence."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path


class RecoveryValidationError(ValueError):
    """A recovery document does not satisfy its required schema."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _object(value: object) -> dict:
    if not isinstance(value, dict):
        raise RecoveryValidationError("Expected a JSON object")
    return value


def _array(value: object) -> list:
    if not isinstance(value, list):
        raise RecoveryValidationError("Expected a JSON array")
    return value


def _git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, check=False, timeout=30)
    if result.returncode:
        raise ValueError(f"Git operation failed: {result.stderr.decode().strip()}")
    return result.stdout


def _file_state(data: bytes | None) -> dict:
    return {"exists": data is not None, "sha256": None if data is None else _sha(data)}


def _relative_file(root: Path, name: str) -> Path:
    path = Path(name)
    if not name or path.is_absolute() or ".." in path.parts or "\0" in name:
        raise ValueError(f"Unsafe path: {name}")
    current = root
    for part in path.parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f"Unsafe symlink path: {name}")
    if not current.is_relative_to(root) or (current.exists() and not current.is_file()):
        raise ValueError(f"Not a regular file path: {name}")
    return current


# @id CODE-GATE-RECOVERY-001
# @implements REQ-GATE-RECOVERY-001
# @design DES-GATE-RECOVERY-001
def audit_replay_sources(root: Path | str, revision: str, paths: list[str]) -> dict:
    root = Path(root).resolve(strict=True)
    commit = (
        _git(root, "rev-parse", "--verify", "--end-of-options", revision + "^{commit}")
        .decode()
        .strip()
    )
    head = _git(root, "rev-parse", "HEAD").decode().strip()
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, head],
        cwd=root,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if commit == head or ancestry.returncode == 1:
        raise ValueError("Revision must be a strict ancestor of HEAD")
    if ancestry.returncode:
        raise ValueError(f"Could not verify ancestor: {ancestry.stderr.decode().strip()}")
    if not paths or len(paths) != len(set(paths)):
        raise ValueError("Source paths must be nonempty and unique")
    files = {}
    for name in paths:
        path = _relative_file(root, name)
        parts = Path(name).parts
        allowed = parts[0] in {"src", "scripts", "bin"} or name == "package.json"
        allowed |= (
            len(parts) == 4
            and parts[:2] == (".github", "skills")
            and parts[-1] in {"SKILL.md", "manifest.json"}
        )
        if not allowed:
            raise ValueError(f"Path is not a replay implementation: {name}")
        tree = _git(root, "ls-tree", "-z", commit, "--", name)
        if tree:
            if not tree.startswith((b"100644 blob ", b"100755 blob ")):
                raise ValueError(f"Past path is not a regular Git blob: {name}")
            past = _git(root, "show", f"{commit}:{name}")
        else:
            past = None
        files[name] = {
            "past": _file_state(past),
            "current": _file_state(path.read_bytes() if path.exists() else None),
        }
    if all(row["past"] == row["current"] for row in files.values()):
        raise ValueError("Replay has no source difference")
    return {"root": str(root), "revision": commit, "head": head, "files": files}


def _changes_preserved(before: list, after: list) -> bool:
    if len(after) < len(before):
        return False
    for original, current in zip(before, after):
        original, current = _object(original), _object(current)
        for key, value in original.items():
            if key == "phases":
                for phase, payload in _object(value).items():
                    if _object(current.get("phases")).get(phase) == payload:
                        continue
                    if phase != "quality" or payload not in _array(current.get("qualityHistory")):
                        return False
            elif key == "qualityHistory":
                if _array(current.get(key))[: len(value)] != value:
                    return False
            elif current.get(key) != value:
                return False
    return True


def _head(records: list) -> dict:
    if not records:
        return {"head": None, "sequence": 0}
    last = _object(records[-1])
    if not isinstance(last.get("sequence"), int) or not isinstance(last.get("recordSha256"), str):
        raise RecoveryValidationError("Malformed native sequence or chain head")
    return {"head": last["recordSha256"], "sequence": last["sequence"]}


# @id CODE-GATE-RECOVERY-005
# @implements REQ-GATE-RECOVERY-001
# @design DES-GATE-RECOVERY-001
def validate_replay_artifacts(base: Path | str, incoming: Path | str) -> dict:
    sides = []
    for root in [base, incoming]:
        documents = {}
        for name in ["order", "tdd", "changes"]:
            path = Path(root) / ".musubix/evidence" / f"{name}.json"
            document = _object(json.loads(path.read_bytes()))
            expected_schema = 2 if name == "changes" else 1
            schema = document.get("schemaVersion")
            if type(schema) is not int or schema != expected_schema:
                raise ValueError("Unsupported native evidence schema")
            documents[name] = document
        sides.append(documents)
    before, after = sides
    for name, key in [("order", "records"), ("tdd", "cycles"), ("tdd", "chain")]:
        original, current = _array(before[name].get(key)), _array(after[name].get(key))
        if current[: len(original)] != original:
            raise ValueError(f"Original {name}/{key} prefix was not preserved")
    if not _changes_preserved(
        _array(before["changes"].get("changes")), _array(after["changes"].get("changes"))
    ):
        raise ValueError("Original change phase payloads were not preserved")
    return {
        "prefixVerified": True,
        **{
            label: {"order": _head(side["order"]["records"]), "tdd": _head(side["tdd"]["chain"])}
            for label, side in zip(["before", "after"], sides)
        },
    }


# @id CODE-GATE-RECOVERY-006
# @implements REQ-GATE-RECOVERY-001
# @design DES-GATE-RECOVERY-001
def build_replay_provenance(red: dict, green: dict) -> dict:
    audit = _object(red.get("audit"))
    revision, root = audit.get("revision"), audit.get("root")
    if (
        green.get("audit") != audit
        or not isinstance(revision, str)
        or not re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", revision)
        or not isinstance(root, str)
        or not root
    ):
        raise ValueError("Replay revision audit mismatch")
    files = _object(audit.get("files"))
    if not files:
        raise ValueError("Replay audit has no source files")
    if not Path(root).is_dir():
        raise ValueError("Replay audit root does not exist")
    if audit_replay_sources(root, revision, list(files)) != audit:
        raise ValueError("Replay Git ancestry or source audit changed")
    for key in ["testId", "testSha256", "command", "environmentSha256"]:
        if not isinstance(red.get(key), str) or not red[key] or red[key] != green.get(key):
            raise ValueError(f"Red/Green {key} mismatch")
    for phase, expected_status, side in [(red, "failed", "past"), (green, "passed", "current")]:
        if phase.get("selected") != 1 or phase.get("testStatus") != expected_status:
            raise ValueError("Replay did not observe exactly the selected test")
        exit_code = phase.get("exitCode")
        if type(exit_code) is not int or (exit_code == 0) != (expected_status == "passed"):
            raise ValueError("Replay exit status mismatch")
        expected = {name: _object(row)[side] for name, row in _object(audit.get("files")).items()}
        if phase.get("sources") != expected:
            raise ValueError("Replay source hash or absence mismatch")
        for key in ["record", "report"]:
            artifact = _object(phase.get(key))
            path = artifact.get("path")
            if not isinstance(path, str) or not path or not Path(path).is_file():
                raise ValueError(f"Replay {key} path is missing or invalid")
            if _sha(Path(path).read_bytes()) != artifact.get("sha256"):
                raise ValueError(f"Replay {key} hash mismatch")
    return {
        "valid": True,
        "revision": revision,
        "commandSha256": _sha(red["command"].encode()),
        "red": red,
        "green": green,
    }


def _historical_waiver_scopes() -> set[tuple]:
    scopes = {
        (f"CHANGE-{number:03d}", "CHANGE_RECORD_MISSING", None, None)
        for number in [22, 23, 24, 25, 27, 28]
    }
    for number in [20, 26]:
        scopes.update(
            (f"CHANGE-{number:03d}", "CHANGE_PHASE_MISSING", None, f"phase:{phase}")
            for phase in ["red", "implementation", "green", "quality"]
        )
    requirements = {
        1: ["REQ-AISCI-004", "REQ-AISCI-017", "REQ-AISCI-024"],
        19: ["REQ-AISCI-004", "REQ-AISCI-017", "REQ-AISCI-024"],
        11: ["REQ-AIDS-082"],
        14: ["REQ-AIDS-056"],
        15: ["REQ-AIDS-021", "REQ-AIDS-082"],
        21: ["REQ-ACHEM-100"],
        39: ["REQ-AIDS-110"],
        40: ["REQ-AIDS-110"],
    }
    for number, ids in requirements.items():
        scopes.update(
            (f"CHANGE-{number:03d}", code, requirement, None)
            for requirement in ids
            for code in ["CHANGE_RED_UNPROVEN", "CHANGE_GREEN_UNPROVEN", "CHANGE_COMPLETENESS_TDD"]
        )
    scopes.update(
        ("CHANGE-003", "CHANGE_COMPLETENESS_TDD", f"REQ-AIMS-{number:03d}", None)
        for number in [2, 3, 4, 10, 40]
    )
    scopes.update(
        {
            ("CHANGE-020", "CHANGE_COMPLETENESS_TDD", "REQ-AISCI-023", None),
            ("CHANGE-026", "CHANGE_COMPLETENESS_TDD", "REQ-AIDS-044", None),
            ("CHANGE-021", "CHANGE_ORDER_MIGRATION_REQUIRED", None, "requirement:REQ-ACHEM-100"),
        }
    )
    return scopes


_HISTORICAL_WAIVER_SCOPES = _historical_waiver_scopes()
_RECORDING_EXCEPTION = (
    "CHANGE-045",
    "CHANGE_TEST_CHANGED_AFTER_RED",
    None,
    "REQ-GATE-RECOVERY-002,REQ-GATE-RECOVERY-003",
)
_RECORDING_OLD = (
    b'    for name in manual:\n        (root / name).write_bytes(b"new " + manual[name])\n'
)
_RECORDING_NEW = (
    b'    for name, value in manual.items():\n        (root / name).write_bytes(b"new " + value)\n'
)


def _validate_recording_exception(context: dict) -> dict:
    context = _object(context)
    if set(context) != {"root", "proof", "expected_sha256", "native_module"}:
        raise RecoveryValidationError(
            "Recording exception requires actual files and pinned identity"
        )
    root = _recovery_root(context["root"])
    proof_path = Path(context["proof"])
    if proof_path.resolve().is_relative_to(root / ".musubix/evidence"):
        raise RecoveryValidationError("Recording proof must be outside protected evidence")
    proof = _verified_document({"path": str(proof_path), "sha256": context["expected_sha256"]})
    if (
        type(proof.get("schemaVersion")) is not int
        or proof.get("schemaVersion") != 1
        or proof.get("changeId") != "CHANGE-045"
        or set(_object(proof.get("phases"))) != {"red", "green"}
    ):
        raise RecoveryValidationError("Malformed recording exception proof")
    files = {}
    for phase in ["red", "green"]:
        artifact = _object(proof["phases"][phase])
        path = Path(artifact.get("path", ""))
        if (
            not path.is_file()
            or path.is_symlink()
            or path.resolve().is_relative_to(root / ".musubix/evidence")
            or _recovery_hash(path) != artifact.get("sha256")
        ):
            raise RecoveryValidationError(f"Reconstructed {phase} artifact hash mismatch")
        files[phase] = path.read_bytes()
    if files["red"].count(_RECORDING_OLD) != 1 or (
        files["red"].replace(_RECORDING_OLD, _RECORDING_NEW, 1) != files["green"]
    ):
        raise RecoveryValidationError(
            "Recording proof is not the exact permitted lint-only byte diff"
        )
    tests = {}
    for phase, data in files.items():
        try:
            tree = ast.parse(data)
        except SyntaxError as error:
            raise RecoveryValidationError(
                f"Invalid reconstructed {phase} Python: {error}"
            ) from error
        tests[phase] = [
            (node.name, ast.dump(node, include_attributes=False))
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
        ]
    if not tests["red"] or tests["red"] != tests["green"]:
        raise RecoveryValidationError("Reconstructed test function ASTs differ")
    module = _object(context["native_module"])
    if set(module) != {"packagePath", "entry", "version", "sha256"} or not all(
        isinstance(value, str) and value for value in module.values()
    ):
        raise RecoveryValidationError("Missing independently pinned native module identity")
    script = r"""
import {createRequire} from 'node:module';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const [root, serialized, moduleJSON] = process.argv.slice(1);
const proof = JSON.parse(serialized), module = JSON.parse(moduleJSON);
const assert = (condition, message) => {if (!condition) throw new Error(message);};
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const require = createRequire(module.packagePath);
const entry = require.resolve('musubix3/analysis');
const info = JSON.parse(await readFile(module.packagePath, 'utf8'));
assert(entry === module.entry && info.version === module.version, 'Native module identity mismatch');
assert(sha(await readFile(entry)) === module.sha256, 'Native module hash mismatch before import');
const api = await import(entry);
assert(sha(await readFile(entry)) === module.sha256, 'Native module hash mismatch after import');
const trace = await api.buildTrace(root, false);
const paths = [...new Set(trace.nodes.filter(n => n.kind === 'test').map(n => n.path))].sort();
assert(paths.includes('tests/test_gate_recovery.py'), 'Missing authoritative test path');
const current = await api.snapshot(root, paths);
const changes = JSON.parse(await readFile(root+'/.musubix/evidence/changes.json','utf8')).changes;
const matches = changes.filter(c => c.changeId === 'CHANGE-045');
assert(matches.length === 1, 'Missing unique original CHANGE-045');
for (const phase of ['red','green']) {
    const row = proof.phases[phase];
    const digest = sha(await readFile(row.path));
    assert(digest === row.sha256, 'Reconstructed file hash changed');
    const fingerprint = sha(JSON.stringify({...current, 'tests/test_gate_recovery.py':digest}));
    assert(fingerprint === row.testsFingerprint &&
        fingerprint === matches[0].phases[phase].fingerprints.tests,
        `Original ${phase} tests fingerprint mismatch`);
}
"""
    try:
        result = subprocess.run(
            [
                "node",
                "--input-type=module",
                "-e",
                script,
                str(root),
                json.dumps(proof),
                json.dumps(module),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RecoveryValidationError(f"Cannot verify recording exception: {error}") from error
    if result.returncode:
        raise RecoveryValidationError(
            f"Recording exception verification failed: {result.stderr.strip()}"
        )
    return {
        "root": str(root),
        "proof": str(proof_path.resolve()),
        "sha256": context["expected_sha256"],
    }


def _scope(diagnostic: dict, code: str | None = None) -> tuple:
    return (
        diagnostic.get("changeId"),
        code or diagnostic.get("code"),
        diagnostic.get("requirementId"),
        diagnostic.get("detail"),
    )


# @id CODE-GATE-RECOVERY-002
# @implements REQ-GATE-RECOVERY-002
# @design DES-GATE-RECOVERY-002
def plan_historical_waivers(gate_report: dict, chronology_context: dict | None = None) -> dict:
    diagnostics = []
    for check in _array(gate_report.get("checks")):
        diagnostics.extend(_array(_object(check).get("diagnostics", [])))
    diagnostics.extend(_array(gate_report.get("waiverDiagnostics", [])))
    unique = {json.dumps(_object(row), sort_keys=True): row for row in diagnostics}
    candidates, blocked, resolved = [], [], []
    errors = {_scope(row) for row in unique.values() if row.get("severity") == "error"}
    exception_verified = False
    for row in unique.values():
        code = row.get("code")
        if code == "CHANGE_WAIVER_STALE":
            match = re.search(r"CHANGE-\d+:(CHANGE_[A-Z_]+)", row.get("message", ""))
            if match and _scope(row, match[1]) in errors:
                continue
            if "condition=true" in row.get("message", ""):
                blocked.append(row)
            else:
                resolved.append(row)
            continue
        if row.get("severity") != "error":
            continue
        valid = _scope(row) in _HISTORICAL_WAIVER_SCOPES and all(
            key not in row or row[key] is not None for key in ["requirementId", "detail"]
        )
        if _scope(row) == _RECORDING_EXCEPTION and "requirementId" not in row:
            if chronology_context is not None and not exception_verified:
                _validate_recording_exception(chronology_context)
                exception_verified = True
            valid = exception_verified
        (candidates if valid else blocked).append(dict(row))
    key = lambda row: json.dumps(row, sort_keys=True)
    return {
        "candidates": sorted({_scope(row): row for row in candidates}.values(), key=key),
        "blocked": sorted(blocked, key=key),
        "resolved_stale": sorted(resolved, key=key),
    }


_MANUAL_FOLLOWUP_PATHS = {
    ".musubix/features/full-gate-recovery/requirements.md",
    ".musubix/features/full-gate-recovery/design.md",
    ".musubix/decisions/ADR-0127.md",
    *(f".musubix/changes/CHANGE-{number:03d}.md" for number in [42, 43, 45, 46]),
    "scripts/gate_recovery.py",
    "tests/test_gate_recovery.py",
}
_FOLLOWUP_PHASES = ["impact", "requirements", "design", "red", "implementation", "green", "quality"]


def _read_document(path: Path | str) -> dict:
    try:
        return _object(json.loads(Path(path).read_bytes()))
    except (OSError, json.JSONDecodeError) as error:
        raise RecoveryValidationError(f"Cannot read recovery document {path}: {error}") from error


def _recovery_hash(path: Path) -> str:
    try:
        return _sha(path.read_bytes())
    except OSError as error:
        raise RecoveryValidationError(f"Cannot read recovery artifact {path}: {error}") from error


def _recovery_root(value: Path | str) -> Path:
    if not isinstance(value, (str, Path)) or not str(value):
        raise RecoveryValidationError("Recovery root must be a nonempty directory path")
    try:
        path = Path(value).resolve(strict=True)
    except OSError as error:
        raise RecoveryValidationError(f"Recovery root is unavailable: {value}") from error
    if not path.is_dir():
        raise RecoveryValidationError(f"Recovery root is not a directory: {value}")
    return path


def _verified_document(artifact: dict) -> dict:
    path = Path(_object(artifact).get("path", ""))
    if not path.is_file() or path.is_symlink() or _sha(path.read_bytes()) != artifact.get("sha256"):
        raise RecoveryValidationError(f"Recovery artifact hash mismatch: {path}")
    return _read_document(path)


def _verify_native_followup_files(original: Path, root: Path) -> None:
    mutable = {
        f".musubix/evidence/{name}.json"
        for name in [
            "tdd",
            "order",
            "changes",
            "workflow",
            "change-waivers",
            "workflow-waivers",
            "formal",
            "model-correspondence",
            "performance",
            "quality",
        ]
    } | {
        f".musubix/evidence/approvals/{stage}.json"
        for stage in ["requirements", "design", "release"]
    }
    original_files = {
        path.relative_to(original).as_posix()
        for path in (original / ".musubix/evidence").rglob("*")
        if path.is_file()
    }
    current_files = {
        path.relative_to(root).as_posix()
        for path in (root / ".musubix/evidence").rglob("*")
        if path.is_file()
    }
    for name in original_files | current_files:
        before, after = _relative_file(original, name), _relative_file(root, name)
        if not after.is_file():
            raise RecoveryValidationError(f"Original native artifact removed: {name}")
        if before.is_file() and before.read_bytes() == after.read_bytes():
            continue
        allowed = name in mutable or bool(
            re.fullmatch(r"\.musubix/evidence/native/(test|performance)/[A-Za-z0-9_-]+\.json", name)
        )
        if not allowed:
            raise RecoveryValidationError(f"Unapproved native artifact change: {name}")
        _read_document(after)
    for name, key in [
        ("workflow", "events"),
        ("change-waivers", "waivers"),
        ("workflow-waivers", "waivers"),
    ]:
        before_path = original / f".musubix/evidence/{name}.json"
        if not before_path.is_file():
            continue
        before = _array(_read_document(before_path).get(key))
        after = _array(_read_document(root / f".musubix/evidence/{name}.json").get(key))
        if after[: len(before)] != before:
            raise RecoveryValidationError(f"Original native {name} records changed")


def _runtime_inventory(root: Path) -> dict:
    code = (
        "import sys,json,importlib.metadata,re;"
        "print(json.dumps({'python':sys.version.split()[0],"
        "'packages':{re.sub(r'[-_.]+','-',d.metadata['Name']).lower():d.version "
        "for d in importlib.metadata.distributions()}},sort_keys=True))"
    )
    try:
        result = subprocess.run(
            [str(root / ".venv/bin/python"), "-c", code],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RecoveryValidationError(f"Cannot inspect runtime: {error}") from error
    if result.returncode:
        raise RecoveryValidationError(f"Runtime inventory failed: {result.stderr.strip()}")
    return _object(json.loads(result.stdout))


def _native_followup_checks(root: Path, original: Path, followup: dict) -> None:
    script = r"""
import {createRequire} from 'node:module';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
const [root, original, serialized] = process.argv.slice(1);
const f = JSON.parse(serialized);
const module = f._nativeModule;
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const read = async name => JSON.parse(await readFile(path.join(root, name), 'utf8'));
const assert = (condition, message) => {if (!condition) throw new Error(message);};
const require = createRequire(module.packagePath);
const entry = require.resolve('musubix3/analysis');
assert(entry === module.entry && sha(await readFile(entry)) === module.sha256,
       'Original native module hash mismatch');
const api = await import(entry);
const config = await read('.musubix/config.json');
const trace = await api.buildTrace(root, false);
for (const result of [
    await api.validateTddEvidence(root),
    api.validateEvidenceOrderLog(await read('.musubix/evidence/order.json')),
    await api.checkTrace(root, trace, true, config.thresholds),
    await api.validatePerformanceEvidence(root),
    await api.validateModelCorrespondenceEvidence(root)
]) assert(result.valid, JSON.stringify(result.diagnostics));
const workflow = await api.validateWorkflow(root, config.workflow);
assert(workflow.present && !workflow.diagnostics.some(d => d.severity === 'error'),
       JSON.stringify(workflow.diagnostics));
const canonical = graph => {
    const keys = ['schemaVersion','generatedAt','nodes','edges','diagnostics','fingerprints'];
    assert(Object.keys(graph).length === keys.length && keys.every(k => Object.hasOwn(graph,k)),
           'Derived trace schema mismatch');
    const {generatedAt, ...value} = api.canonicalSort(graph);
    return JSON.stringify(sort(value));
};
function sort(value) {
    if (Array.isArray(value)) return value.map(sort);
    if (value && typeof value === 'object')
        return Object.fromEntries(Object.keys(value).sort().map(k => [k, sort(value[k])]));
    return value;
}
for (const name of ['.musubix/trace.json',
    ...f._tracePaths]) {
    const expected = name === '.musubix/trace.json' ? trace :
        api.featureTraceProjection(trace, path.posix.dirname(name));
    assert(canonical(await read(name)) === canonical(expected), `Derived trace mismatch: ${name}`);
}
for (const stage of ['requirements', 'design']) {
    const result = await api.validateApprovalStage(root, stage, config.approval);
    const approval = await read(`.musubix/evidence/approvals/${stage}.json`);
    assert(result.status === 'approved' && approval.artifactSha256 === f.approvals[stage],
           `Current ${stage} approval mismatch`);
}
const changes = (await read('.musubix/evidence/changes.json')).changes;
const change = changes.find(c => c.changeId === 'CHANGE-045');
const correction = changes.find(c => c.changeId === 'CHANGE-046');
assert(change && correction, 'Missing correction change');
const cycles = (await read('.musubix/evidence/tdd.json')).cycles;
const finalGreen = [change.phases.green, ...(change.tddBatches ?? []).map(b => b.green),
    correction.phases.green]
    .filter(Boolean).sort((a,b) => a.order - b.order).at(-1);
const finalSources = Object.assign({}, ...Object.values(
    finalGreen.fingerprints.requirementImplementations).map(row => row.fingerprints));
const testPaths = [...new Set(trace.nodes.filter(n => n.id.startsWith('TEST-'))
    .map(n => n.path))].sort();
assert(sha(JSON.stringify(await api.snapshot(root, testPaths))) === finalGreen.fingerprints.tests,
       'Final Green/current tests fingerprint mismatch');
const windows = [change, correction].flatMap(c => [
    {requirementIds:c.requirementIds, design:c.phases.design.order, green:c.phases.green?.order},
    ...(c.tddBatches ?? []).map(b => ({
        requirementIds:b.requirementIds, design:c.phases.design.order, green:b.green?.order
    }))
]);
for (const number of ['002', '003']) {
    const requirement = `REQ-GATE-RECOVERY-${number}`;
    const testId = `TEST-GATE-RECOVERY-${number}`;
    const matches = cycles.filter(c => c.requirementId === requirement && c.testId === testId &&
        !c.void && !c.archive && windows.some(w => w.requirementIds.includes(requirement) &&
            c.red?.order > w.design && c.green?.order < w.green))
        .sort((a,b) => a.green.order - b.green.order);
    assert(matches.length > 0, `Missing follow-up cycle: ${testId}`);
    const cycle = matches.at(-1);
    assert(!cycles.some(c => c.requirementId === requirement && c.testId === testId &&
        !c.void && !c.archive && c.red?.order > cycle.red.order && !c.green),
        `Newer incomplete Red cycle: ${testId}`);
    const node = trace.nodes.find(n => n.id === testId);
    assert(cycle.red.testFingerprint === cycle.green.testFingerprint &&
        await api.legacyTestFingerprint(root, node) === cycle.green.testFingerprint,
        `Red/Green/current test mismatch: ${testId}`);
    for (const [phase, expected] of [['red','failed'], ['green','passed']]) {
        const proof = f.testReports?.[testId]?.[phase];
        assert(proof, `Missing ${testId} ${phase} archive`);
        const bytes = await readFile(proof.path);
        const report = JSON.parse(bytes);
        assert(sha(bytes) === proof.sha256 && proof.sha256 === cycle[phase].reportSha256,
            `Native test report hash mismatch: ${testId}/${phase}`);
        const tests = report.tests?.filter(t => t.nodeid.includes(testId.replaceAll('-','_')));
        assert(tests?.length === 1 && tests[0].outcome === expected,
            `Native test report outcome mismatch: ${testId}/${phase}`);
    }
    const fingerprints = change.phases.green.fingerprints.requirementImplementations[requirement];
    assert(fingerprints?.paths.length > 0, `Missing implementation bindings: ${requirement}`);
    for (const name of fingerprints.paths)
        assert(sha(await readFile(path.join(root, name))) === finalSources[name],
               `Green/current implementation mismatch: ${name}`);
}
const diagnostics = [
    ...(await api.validateChangeEvidence(root)).diagnostics,
    ...(await api.validateChangeCompleteness(root)).diagnostics
];
console.log(JSON.stringify({diagnostics}));
"""
    try:
        result = subprocess.run(
            [
                "node",
                "--input-type=module",
                "-e",
                script,
                str(root),
                str(original),
                json.dumps(followup),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RecoveryValidationError(
            f"Native follow-up validation unavailable: {error}"
        ) from error
    if result.returncode:
        raise RecoveryValidationError(
            f"Native follow-up validation failed: {result.stderr.strip()}"
        )
    diagnostics = _object(json.loads(result.stdout))
    plan = plan_historical_waivers({"checks": [diagnostics]})
    if plan["blocked"]:
        raise RecoveryValidationError(f"Unapproved native change diagnostics: {plan['blocked']}")


# @id CODE-GATE-RECOVERY-007
# @implements REQ-GATE-RECOVERY-003
# @design DES-GATE-RECOVERY-003
def validate_recovery_followup(
    root: Path | str,
    original_manifest: Path | str,
    original_receipt: Path | str,
    followup: Path | str,
    expected_original: dict,
    chronology_context: dict | None = None,
) -> dict:
    root = _recovery_root(root)
    if not all(
        isinstance(value, (str, Path)) and str(value)
        for value in [original_manifest, original_receipt, followup]
    ):
        raise RecoveryValidationError("Recovery manifests must be nonempty file paths")
    manifest_path, receipt_path, followup_path = map(
        Path, [original_manifest, original_receipt, followup]
    )
    for path in [manifest_path, receipt_path, followup_path]:
        if path.is_symlink() or path.resolve().is_relative_to(root / ".musubix/evidence"):
            raise RecoveryValidationError("Recovery manifests must be outside protected evidence")
    if len({path.resolve() for path in [manifest_path, receipt_path, followup_path]}) != 3:
        raise RecoveryValidationError("Recovery manifests must be distinct files")
    manifest, receipt, document = map(_read_document, [manifest_path, receipt_path, followup_path])
    expected = _object(expected_original)
    if (
        set(expected) != {"transactionId", "manifestSha256"}
        or type(manifest.get("schemaVersion")) is not int
        or manifest.get("schemaVersion") != 1
        or manifest.get("state") != "completed"
        or type(document.get("schemaVersion")) is not int
        or document.get("schemaVersion") != 1
        or document.get("changeId") != "CHANGE-045"
        or manifest.get("root") != str(root)
        or _sha(manifest_path.read_bytes()) != expected.get("manifestSha256")
        or manifest.get("transactionId") != expected.get("transactionId")
        or any(
            document.get(key) != value or receipt.get(key) != value
            for key, value in expected.items()
        )
        or receipt.get("state") != "completed"
        or receipt.get("inputsVerified") is not True
        or receipt.get("prefixVerified") is not True
        or document.get("originalReceiptSha256") != _sha(receipt_path.read_bytes())
    ):
        raise RecoveryValidationError(
            "Original transport identity, receipt or follow-up schema mismatch"
        )
    original = _recovery_root(manifest.get("incomingRoot"))
    if original == root:
        raise RecoveryValidationError("Original independent root must differ from current root")
    artifacts = {}
    for row in _array(manifest.get("files")):
        name = _object(row).get("path")
        if not isinstance(name, str) or name in artifacts:
            raise RecoveryValidationError("Malformed or duplicate original artifact")
        artifacts[name] = row.get("afterSha256")
        path = _relative_file(original, name)
        if _recovery_hash(path) != row.get("afterSha256"):
            raise RecoveryValidationError(f"Original artifact hash mismatch: {name}")
        if name not in {
            f".musubix/evidence/{n}.json" for n in ["tdd", "order", "changes"]
        } and _recovery_hash(_relative_file(root, name)) != row.get("afterSha256"):
            raise RecoveryValidationError(f"Immutable audit artifact hash mismatch: {name}")
    if not all(
        f".musubix/evidence/{name}.json" in artifacts for name in ["tdd", "order", "changes"]
    ):
        raise RecoveryValidationError("Original native ledgers missing")
    try:
        validate_replay_artifacts(original, root)
    except ValueError as error:
        raise RecoveryValidationError(f"Original native prefix mismatch: {error}") from error
    _verify_native_followup_files(original, root)
    inputs = {}
    for row in _array(manifest.get("inputFiles")):
        name = _object(row).get("path")
        if not isinstance(name, str) or name in inputs or Path(name).as_posix() != name:
            raise RecoveryValidationError("Malformed or duplicate original input")
        inputs[name] = row.get("sha256")
        if _recovery_hash(_relative_file(original, name)) != row.get("sha256"):
            raise RecoveryValidationError(f"Original input hash mismatch: {name}")
    changes = {}
    for row in _array(document.get("inputChanges")):
        name = _object(row).get("path")
        if not isinstance(name, str):
            raise RecoveryValidationError("Malformed follow-up input path")
        if name in changes:
            raise RecoveryValidationError(f"Duplicate follow-up input: {name}")
        if name not in _MANUAL_FOLLOWUP_PATHS:
            raise RecoveryValidationError(f"Out-of-scope follow-up input: {name}")
        changes[name] = row
    current_files = set(
        _git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
        .decode()
        .rstrip("\0")
        .split("\0")
    )
    observed = {}
    for name in sorted(set(inputs) | current_files):
        if not name or name.startswith(".musubix/evidence/") or name == ".musubix/trace.json":
            continue
        path = _relative_file(root, name)
        current_hash = _sha(path.read_bytes()) if path.exists() else None
        if current_hash == inputs.get(name):
            continue
        if re.fullmatch(r"\.musubix/features/[^/]+/trace\.json", name):
            continue
        if name not in _MANUAL_FOLLOWUP_PATHS or current_hash is None:
            raise RecoveryValidationError(f"Unapproved input change: {name}")
        observed[name] = {
            "path": name,
            "beforeSha256": inputs.get(name),
            "afterSha256": current_hash,
        }
    if changes != observed:
        raise RecoveryValidationError(
            "Follow-up input changes do not match actual before/after hashes"
        )
    green_files = _object(document.get("greenFiles"))
    expected_files = {"scripts/gate_recovery.py", "tests/test_gate_recovery.py"}
    if set(green_files) != expected_files or any(
        _sha(_relative_file(root, name).read_bytes()) != value
        for name, value in green_files.items()
    ):
        raise RecoveryValidationError("Final Green/current source or test hash mismatch")
    approvals = _object(document.get("approvals"))
    if set(approvals) != {"requirements", "design"} or not all(approvals.values()):
        raise RecoveryValidationError("Current requirements/design approval hashes missing")
    ledger = _read_document(root / ".musubix/evidence/changes.json")
    records = [row for row in ledger["changes"] if row["changeId"] == "CHANGE-045"]
    if len(records) != 1:
        raise RecoveryValidationError("Missing unique CHANGE-045 record")
    phases = _object(records[0].get("phases"))
    if phases.get("red", {}).get("fingerprints", {}).get("tests") != phases.get("green", {}).get(
        "fingerprints", {}
    ).get("tests"):
        if chronology_context is None:
            raise RecoveryValidationError(
                "Missing independently pinned recording exception context"
            )
        if (
            _recovery_root(chronology_context.get("root")) != root
            or chronology_context.get("native_module") != manifest["nativeModule"]
        ):
            raise RecoveryValidationError(
                "Recording exception root or native module identity mismatch"
            )
        proof = _validate_recording_exception(chronology_context)
        if _object(document.get("chronologyProof")) != {
            "path": proof["proof"],
            "sha256": proof["sha256"],
        }:
            raise RecoveryValidationError("Follow-up recording proof binding mismatch")
    phase_artifacts = _object(document.get("phaseArtifacts"))
    if set(phase_artifacts) != set(_FOLLOWUP_PHASES):
        raise RecoveryValidationError("Missing follow-up phase artifacts")
    for name in _FOLLOWUP_PHASES:
        snapshot = _verified_document(_object(phase_artifacts[name]))
        matches = [
            row for row in snapshot.get("changes", []) if row.get("changeId") == "CHANGE-045"
        ]
        if len(matches) != 1 or matches[0].get("phases", {}).get(name) != phases.get(name):
            raise RecoveryValidationError(f"Native phase artifact mismatch: {name}")
    batches = _array(records[0].get("tddBatches", []))
    batch_artifacts = _array(document.get("batchArtifacts", []))
    if len(batch_artifacts) != len(batches):
        raise RecoveryValidationError("Missing corrective batch artifacts")
    for batch, artifacts in zip(batches, batch_artifacts):
        if artifacts.get("requirementIds") != batch.get("requirementIds"):
            raise RecoveryValidationError("Corrective batch requirement mismatch")
        for name in ["red", "implementation", "green"]:
            snapshot = _verified_document(_object(artifacts.get(name)))
            entries = [
                row for row in snapshot.get("changes", []) if row.get("changeId") == "CHANGE-045"
            ]
            matches = (
                [
                    row
                    for row in entries[0].get("tddBatches", [])
                    if row.get("requirementIds") == batch["requirementIds"]
                ]
                if len(entries) == 1
                else []
            )
            if len(matches) != 1 or matches[0].get(name) != batch.get(name):
                raise RecoveryValidationError(f"Corrective native batch artifact mismatch: {name}")
    corrections = [row for row in ledger["changes"] if row.get("changeId") == "CHANGE-046"]
    if (
        len(corrections) != 1
        or corrections[0].get("requirementIds") != ["REQ-GATE-RECOVERY-003"]
        or set(_object(corrections[0].get("phases"))) != set(_FOLLOWUP_PHASES)
    ):
        raise RecoveryValidationError("Missing complete correction CHANGE-046")
    correction_artifacts = _object(document.get("correctionArtifacts"))
    if set(correction_artifacts) != set(_FOLLOWUP_PHASES):
        raise RecoveryValidationError("Missing correction phase artifacts")
    for name in _FOLLOWUP_PHASES:
        snapshot = _verified_document(_object(correction_artifacts[name]))
        matches = [
            row for row in snapshot.get("changes", []) if row.get("changeId") == "CHANGE-046"
        ]
        if (
            len(matches) != 1
            or matches[0].get("requirementIds") != ["REQ-GATE-RECOVERY-003"]
            or matches[0].get("phases", {}).get(name) != corrections[0]["phases"][name]
        ):
            raise RecoveryValidationError(f"Native correction phase artifact mismatch: {name}")
    baseline = _verified_document(_object(document.get("runtimeBaseline")))
    if (
        baseline.get("schemaVersion") != 1
        or baseline.get("root") != _runtime_inventory(root)
        or baseline.get("original") != _runtime_inventory(original)
    ):
        raise RecoveryValidationError("Runtime inventory changed from pre-impact baseline")
    original_runtime, current_runtime = baseline["original"], baseline["root"]
    packages = _object(original_runtime.get("packages"))
    allowed_packages = {**packages, "pip": "26.2.2"}
    if (
        original_runtime.get("python") != current_runtime.get("python")
        or current_runtime.get("packages") != allowed_packages
        or "pip" in packages
        or datetime.fromisoformat(baseline["capturedAt"])
        >= datetime.fromisoformat(phases["impact"]["recordedAt"])
    ):
        raise RecoveryValidationError("Unapproved runtime difference or late inventory baseline")
    order = _read_document(root / ".musubix/evidence/order.json")["records"]
    index = phases["impact"]["order"] - 2
    if baseline.get("orderBeforeImpact") != (order[index] if index >= 0 else None):
        raise RecoveryValidationError("Runtime baseline does not bind pre-impact order")
    _native_followup_checks(
        root,
        original,
        {
            **document,
            "_nativeModule": manifest["nativeModule"],
            "_tracePaths": sorted(
                name
                for name in set(inputs) | current_files
                if re.fullmatch(r"\.musubix/features/[^/]+/trace\.json", name)
            ),
        },
    )
    return {
        "state": "completed",
        "inputsVerified": True,
        "prefixVerified": True,
        "followupVerified": True,
        **expected,
        "followupSha256": _sha(followup_path.read_bytes()),
    }


# @id CODE-GATE-RECOVERY-003
# @implements REQ-GATE-RECOVERY-003
# @design DES-GATE-RECOVERY-003
def assess_recovery_readiness(
    gate_report: dict, expected_checks: list[str], approval_report: dict, transport_context: dict
) -> dict:
    blockers = []
    if (
        not expected_checks
        or not all(isinstance(name, str) and name for name in expected_checks)
        or len(set(expected_checks)) != len(expected_checks)
        or "approval" not in expected_checks
    ):
        blockers.append("Expected check names must be nonempty, unique and include approval")
    rows = gate_report.get("checks")
    checks = {}
    if not isinstance(rows, list):
        blockers.append("Missing check results")
        rows = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            blockers.append("Malformed check result")
            continue
        name = row["name"]
        if name in checks:
            blockers.append(f"Duplicate check: {name}")
        checks[name] = row
        if row.get("status") not in {"pass", "fail", "skipped"}:
            blockers.append(f"Unknown check status: {name}")
        if "required" in row and type(row["required"]) is not bool:
            blockers.append(f"Invalid required flag: {name}")
    required = set(expected_checks) | {
        name for name, row in checks.items() if row.get("required") is True
    }
    for name in sorted(required):
        if name not in checks:
            blockers.append(f"Missing check: {name}")
        elif name != "approval" and checks[name].get("status") != "pass":
            blockers.append(f"Required check did not pass: {name}")
    stages = {}
    for row in approval_report.get("stages", []):
        if not isinstance(row, dict) or row.get("stage") in stages:
            blockers.append("Malformed or duplicate approval stage")
            continue
        stages[row.get("stage")] = row.get("status")
    if set(stages) != {"requirements", "design", "release"}:
        blockers.append("Missing or unknown approval stage")
    for stage in ["requirements", "design"]:
        if stages.get(stage) != "approved":
            blockers.append(f"Current {stage} approval is required")
    release_pending = stages.get("release") in {"missing", "stale"}
    if not release_pending and stages.get("release") != "approved":
        blockers.append("Unknown release approval status")
    approval_check = checks.get("approval", {})
    if release_pending:
        diagnostics = approval_check.get("diagnostics", [])
        if (
            approval_check.get("status") != "fail"
            or not diagnostics
            or any(
                row.get("code") not in {"APPROVAL_MISSING", "APPROVAL_STALE"}
                or row.get("path") != ".musubix/evidence/approvals/release.json"
                for row in diagnostics
            )
        ):
            blockers.append("Approval failure is not limited to release")
    elif approval_check.get("status") != "pass" or approval_report.get("valid") is False:
        blockers.append("Approval check contradicts approval stages")
    expected_status = (
        "fail"
        if release_pending or any(checks.get(name, {}).get("status") != "pass" for name in required)
        else "pass"
    )
    if gate_report.get("status") != expected_status:
        blockers.append("Overall gate status contradicts required checks")
    context_keys = {
        "root",
        "original_manifest",
        "original_receipt",
        "followup",
        "expected_original",
    }
    if not isinstance(transport_context, dict) or set(transport_context) not in (
        context_keys,
        context_keys | {"chronology_context"},
    ):
        blockers.append(
            "Actual transport file context and independently pinned identity are required"
        )
    else:
        try:
            validate_recovery_followup(**transport_context)
        except RecoveryValidationError as error:
            blockers.append(f"Transport follow-up verification failed: {error}")
    candidate = not blockers
    ready = candidate and not release_pending and gate_report.get("status") == "pass"
    if release_pending:
        blockers.append("Release approval pending")
    return {"candidate": candidate, "ready": ready, "blockers": blockers}
