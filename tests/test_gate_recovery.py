"""Focused tests for auditable recovery of existing gate evidence."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _git(root, *args):
    return subprocess.check_output(
        [
            "git",
            "-c",
            "user.name=Recovery Test",
            "-c",
            "user.email=recovery@example.invalid",
            *args,
        ],
        cwd=root,
        stderr=subprocess.PIPE,
        text=True,
    ).strip()


def _native_package():
    binary = subprocess.check_output(
        ["npx", "--no-install", "--package", "musubix3@0.1.22", "-c", "command -v musubix3"],
        cwd=ROOT,
        text=True,
    ).strip()
    for parent in Path(binary).resolve().parents:
        package = parent / "package.json"
        if package.exists() and json.loads(package.read_text()).get("name") == "musubix3":
            return package
    raise AssertionError("Installed musubix3 package could not be resolved")


def _recording_exception_fixture(tmp_path):
    root = tmp_path / "root"
    root.mkdir(parents=True)
    _git(root, "init", "-q")
    old = (
        b"# @id TEST-GATE-RECOVERY-002\n# @verifies REQ-GATE-RECOVERY-002\n"
        b"def test_example():\n    assert True\n\n"
        b"def fixture(root, manual):\n"
        b'    for name in manual:\n        (root / name).write_bytes(b"new " + manual[name])\n'
    )
    new = old.replace(
        b'    for name in manual:\n        (root / name).write_bytes(b"new " + manual[name])\n',
        b'    for name, value in manual.items():\n        (root / name).write_bytes(b"new " + value)\n',
    )
    test_path = root / "tests/test_gate_recovery.py"
    test_path.parent.mkdir()
    test_path.write_bytes(new)
    phases, proof_phases = {}, {}
    for name, content in [("red", old), ("green", new)]:
        path = tmp_path / f"{name}.py"
        path.write_bytes(content)
        digest = _sha(content)
        fingerprint = _sha(
            json.dumps({"tests/test_gate_recovery.py": digest}, separators=(",", ":")).encode()
        )
        phases[name] = {"fingerprints": {"tests": fingerprint}}
        proof_phases[name] = {"path": str(path), "sha256": digest, "testsFingerprint": fingerprint}
    _json(
        root / ".musubix/evidence/changes.json",
        {"changes": [{"changeId": "CHANGE-045", "phases": phases}]},
    )
    proof = tmp_path / "proof.json"
    _json(proof, {"schemaVersion": 1, "changeId": "CHANGE-045", "phases": proof_phases})
    package = _native_package()
    entry = Path(
        subprocess.check_output(
            [
                "node",
                "--input-type=module",
                "-e",
                "import {createRequire} from 'node:module';console.log(createRequire(process.argv[1]).resolve('musubix3/analysis'));",
                str(package),
            ],
            text=True,
        ).strip()
    )
    return {
        "root": root,
        "proof": proof,
        "expected_sha256": _sha(proof.read_bytes()),
        "native_module": {
            "packagePath": str(package),
            "entry": str(entry),
            "version": json.loads(package.read_text())["version"],
            "sha256": _sha(entry.read_bytes()),
        },
    }


def _native_followup_contract(tmp_path):
    from gate_recovery import RecoveryValidationError, _native_followup_checks

    tmp_path.mkdir(parents=True)
    package = tmp_path / "package.json"
    entry = tmp_path / "analysis.mjs"
    _json(
        package, {"name": "musubix3", "type": "module", "exports": {"./analysis": "./analysis.mjs"}}
    )
    trace = {
        "schemaVersion": 1,
        "generatedAt": "fixture",
        "nodes": [
            {"id": f"TEST-GATE-RECOVERY-{number}", "path": "tests/test_gate_recovery.py", "line": 1}
            for number in ["002", "003"]
        ],
        "edges": [{"from": "a", "to": target, "relation": "verifies"} for target in ["b", "c"]],
        "diagnostics": [{"code": code, "severity": "info", "message": code} for code in ["A", "B"]],
        "fingerprints": {"a": "one", "b": "two"},
    }
    raw_trace = copy.deepcopy(trace)
    for name in ["nodes", "edges", "diagnostics"]:
        raw_trace[name].reverse()
    raw_trace["fingerprints"] = {"b": "two", "a": "one"}
    raw_trace["generatedAt"] = "later"
    entry.write_text(
        "import {createRequire} from 'node:module';"
        "import {readFile} from 'node:fs/promises';"
        "import {createHash} from 'node:crypto';"
        f"const native = await import(createRequire({json.dumps(str(_native_package()))})"
        ".resolve('musubix3/analysis'));"
        "export const canonicalSort = native.canonicalSort;"
        f"export const buildTrace = async () => ({json.dumps(raw_trace)});"
        """
export const snapshot = async (root, paths) => Object.fromEntries(await Promise.all(
    paths.map(async name => [name, createHash('sha256')
        .update(await readFile(root+'/'+name)).digest('hex')])
));
export const validateTddEvidence = async () => ({valid:true});
export const validateEvidenceOrderLog = () => ({valid:true});
export const checkTrace = async () => ({valid:true});
export const validatePerformanceEvidence = async () => ({valid:true});
export const validateModelCorrespondenceEvidence = async () => ({valid:true});
export const validateWorkflow = async () => ({
    present:true, verified:false, diagnostics:[{severity:'warning', code:'WAIVED'}]
});
export const validateApprovalStage = async () => ({status:'approved', diagnostics:[]});
export const legacyTestFingerprint = async () => 'test-fingerprint';
export const validateChangeEvidence = async () => ({diagnostics:[]});
export const validateChangeCompleteness = async () => ({diagnostics:[]});
""",
        encoding="utf-8",
    )
    trace_path = tmp_path / ".musubix/trace.json"
    _json(trace_path, trace)
    _json(tmp_path / ".musubix/config.json", {"thresholds": {}, "approval": {}, "workflow": {}})
    _json(tmp_path / ".musubix/evidence/order.json", {"records": []})
    for stage in ["requirements", "design"]:
        _json(tmp_path / f".musubix/evidence/approvals/{stage}.json", {"artifactSha256": stage})
    source = tmp_path / "scripts/gate_recovery.py"
    source.parent.mkdir()
    source.write_text("fixture = True\n")
    test_path = tmp_path / "tests/test_gate_recovery.py"
    test_path.parent.mkdir()
    test_path.write_text("test_fixture = True\n")
    tests_fingerprint = _sha(
        json.dumps(
            {"tests/test_gate_recovery.py": _sha(test_path.read_bytes())}, separators=(",", ":")
        ).encode()
    )
    implementation = {
        "paths": ["scripts/gate_recovery.py"],
        "fingerprints": {"scripts/gate_recovery.py": _sha(source.read_bytes())},
    }
    change = {
        "changeId": "CHANGE-045",
        "requirementIds": ["REQ-GATE-RECOVERY-002", "REQ-GATE-RECOVERY-003"],
        "phases": {
            "design": {"order": 2},
            "green": {
                "order": 100,
                "fingerprints": {
                    "requirementImplementations": {
                        f"REQ-GATE-RECOVERY-{number}": implementation for number in ["002", "003"]
                    }
                },
            },
        },
    }
    correction = {
        "changeId": "CHANGE-046",
        "requirementIds": ["REQ-GATE-RECOVERY-003"],
        "phases": {
            "design": {"order": 110},
            "green": {
                "order": 200,
                "fingerprints": {
                    "tests": tests_fingerprint,
                    "requirementImplementations": {"REQ-GATE-RECOVERY-003": implementation},
                },
            },
        },
    }
    _json(tmp_path / ".musubix/evidence/changes.json", {"changes": [change, correction]})
    followup = {
        "_nativeModule": {
            "packagePath": str(package),
            "entry": str(entry),
            "sha256": _sha(entry.read_bytes()),
        },
        "_tracePaths": [],
        "approvals": {"requirements": "requirements", "design": "design"},
        "testReports": {},
    }
    cycles = []
    for index, number in enumerate(["002", "003"]):
        test = f"TEST-GATE-RECOVERY-{number}"
        cycle = {"testId": test, "requirementId": f"REQ-GATE-RECOVERY-{number}"}
        followup["testReports"][test] = {}
        for offset, (phase, outcome) in enumerate([("red", "failed"), ("green", "passed")], 1):
            report = tmp_path / f"{number}-{phase}.json"
            _json(report, {"tests": [{"nodeid": test.replace("-", "_"), "outcome": outcome}]})
            digest = _sha(report.read_bytes())
            cycle[phase] = {
                "order": 10 + index * 110 + offset,
                "reportSha256": digest,
                "testFingerprint": "test-fingerprint",
            }
            followup["testReports"][test][phase] = {"path": str(report), "sha256": digest}
        cycles.append(cycle)
    _json(tmp_path / ".musubix/evidence/tdd.json", {"cycles": cycles})
    before = trace_path.read_bytes()
    _native_followup_checks(tmp_path, tmp_path / "unused-original", followup)
    assert trace_path.read_bytes() == before
    changed = []
    for name, field in [("nodes", "line"), ("edges", "relation"), ("diagnostics", "message")]:
        value = copy.deepcopy(trace)
        value[name][0][field] = "changed"
        changed.append(value)
    changed.append({**trace, "fingerprints": {"a": "changed", "b": "two"}})
    changed.append({**trace, "nodes": [*trace["nodes"], copy.deepcopy(trace["nodes"][0])]})
    value = copy.deepcopy(trace)
    value["nodes"][0]["generatedAt"] = "hidden change"
    changed.extend([value, {**trace, "unknown": "changed"}])
    for value in changed:
        _json(trace_path, value)
        stored = trace_path.read_bytes()
        with pytest.raises(RecoveryValidationError, match="trace|Trace"):
            _native_followup_checks(tmp_path, tmp_path / "unused-original", followup)
        assert trace_path.read_bytes() == stored
    trace_path.write_bytes(before)
    incomplete = {**cycles[-1], "red": {**cycles[-1]["red"], "order": 250}}
    incomplete.pop("green")
    _json(tmp_path / ".musubix/evidence/tdd.json", {"cycles": [*cycles, incomplete]})
    with pytest.raises(RecoveryValidationError, match="cycle|Red|incomplete"):
        _native_followup_checks(tmp_path, tmp_path / "unused-original", followup)


def _followup_fixture(tmp_path, monkeypatch):
    import gate_recovery as recovery

    tmp_path.mkdir(parents=True, exist_ok=True)
    original, root = tmp_path / "original", tmp_path / "root"
    manual = {
        "scripts/gate_recovery.py": b"old implementation",
        "tests/test_gate_recovery.py": b"old test",
    }
    ledgers = {
        "order": {"schemaVersion": 1, "records": []},
        "tdd": {"schemaVersion": 1, "cycles": [], "chain": []},
        "changes": {"schemaVersion": 2, "changes": []},
    }
    for folder in [original, root]:
        folder.mkdir()
        _git(folder, "init", "-q")
        for name, value in manual.items():
            path = folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
        for name, value in ledgers.items():
            _json(folder / f".musubix/evidence/{name}.json", value)
    artifact = ".musubix/evidence/native/recovery/fixture/provenance.json"
    for folder in [original, root]:
        _json(folder / artifact, {"valid": True})
    for name, value in manual.items():
        (root / name).write_bytes(b"new " + value)
    phases = {}
    for index, name in enumerate(
        ["impact", "requirements", "design", "red", "implementation", "green", "quality"], 1
    ):
        phases[name] = {
            "phase": name,
            "order": index,
            "recordedAt": "2021-01-01T00:00:00+00:00",
            "fingerprints": {},
        }
    correction = {
        "changeId": "CHANGE-046",
        "requirementIds": ["REQ-GATE-RECOVERY-003"],
        "phases": {name: {**phase, "order": phase["order"] + 7} for name, phase in phases.items()},
    }
    _json(
        root / ".musubix/evidence/changes.json",
        {
            "schemaVersion": 2,
            "changes": [
                {
                    "changeId": "CHANGE-045",
                    "requirementIds": ["REQ-GATE-RECOVERY-002", "REQ-GATE-RECOVERY-003"],
                    "phases": phases,
                },
                correction,
            ],
        },
    )
    manifest = {
        "schemaVersion": 1,
        "transactionId": "fixture-transaction",
        "state": "completed",
        "root": str(root),
        "incomingRoot": str(original),
        "nativeModule": {"packagePath": str(_native_package())},
        "inputFiles": [{"path": name, "sha256": _sha(data)} for name, data in manual.items()],
        "files": [
            {"path": name, "afterSha256": _sha((original / name).read_bytes())}
            for name in [*(f".musubix/evidence/{n}.json" for n in ledgers), artifact]
        ],
    }
    manifest_path, receipt_path = tmp_path / "transport.json", tmp_path / "receipt.json"
    _json(manifest_path, manifest)
    expected = {
        "transactionId": manifest["transactionId"],
        "manifestSha256": _sha(manifest_path.read_bytes()),
    }
    _json(
        receipt_path,
        {**expected, "state": "completed", "inputsVerified": True, "prefixVerified": True},
    )
    runtime = {"python": "3.12.13", "packages": {"example": "1", "pip": "26.2.2"}}
    baseline_path = tmp_path / "runtime.json"
    _json(
        baseline_path,
        {
            "schemaVersion": 1,
            "capturedAt": "2020-01-01T00:00:00+00:00",
            "root": runtime,
            "original": {"python": "3.12.13", "packages": {"example": "1"}},
            "orderBeforeImpact": None,
        },
    )
    followup = {
        "schemaVersion": 1,
        "changeId": "CHANGE-045",
        **expected,
        "originalReceiptSha256": _sha(receipt_path.read_bytes()),
        "inputChanges": [
            {
                "path": name,
                "beforeSha256": _sha(data),
                "afterSha256": _sha((root / name).read_bytes()),
            }
            for name, data in manual.items()
        ],
        "approvals": {"requirements": "requirements-hash", "design": "design-hash"},
        "runtimeBaseline": {
            "path": str(baseline_path),
            "sha256": _sha(baseline_path.read_bytes()),
        },
        "phaseArtifacts": {},
        "correctionArtifacts": {},
        "greenFiles": {name: _sha((root / name).read_bytes()) for name in manual},
    }
    for name, phase in phases.items():
        path = tmp_path / f"{name}.json"
        _json(
            path,
            {"schemaVersion": 2, "changes": [{"changeId": "CHANGE-045", "phases": {name: phase}}]},
        )
        followup["phaseArtifacts"][name] = {
            "path": str(path),
            "sha256": _sha(path.read_bytes()),
        }
    for name in phases:
        path = tmp_path / f"correction-{name}.json"
        _json(path, {"schemaVersion": 2, "changes": [correction]})
        followup["correctionArtifacts"][name] = {
            "path": str(path),
            "sha256": _sha(path.read_bytes()),
        }
    followup_path = tmp_path / "followup.json"
    _json(followup_path, followup)
    monkeypatch.setattr(
        recovery,
        "_runtime_inventory",
        lambda folder: (
            runtime if folder == root else {"python": "3.12.13", "packages": {"example": "1"}}
        ),
    )
    calls = []

    def native_checks(folder, source, document):
        calls.append((folder, source, document))

    monkeypatch.setattr(recovery, "_native_followup_checks", native_checks)
    context = {
        "root": root,
        "original_manifest": manifest_path,
        "original_receipt": receipt_path,
        "followup": followup_path,
        "expected_original": expected,
    }
    return context, followup, calls


def _transport(tmp_path):
    from gate_recovery import validate_replay_artifacts

    before = tmp_path / "before"
    incoming = tmp_path / "incoming"
    documents = {
        "order.json": {"schemaVersion": 1, "records": [{"sequence": 1, "recordSha256": "a"}]},
        "tdd.json": {
            "schemaVersion": 1,
            "cycles": [{"cycleId": "old", "green": {"valid": True}}],
            "chain": [{"sequence": 1, "recordSha256": "b"}],
        },
        "changes.json": {
            "schemaVersion": 2,
            "changes": [{"changeId": "CHANGE-001", "phases": {"green": {"order": 1}}}],
        },
    }
    for root in [before, incoming]:
        (root / "src").mkdir(parents=True)
        (root / "src/example.py").write_text("value = 1\n")
        for name, value in documents.items():
            _json(root / ".musubix/evidence" / name, value)
    after_order = copy.deepcopy(documents["order.json"])
    after_order["records"].append({"sequence": 2, "recordSha256": "c"})
    _json(incoming / ".musubix/evidence/order.json", after_order)
    assert validate_replay_artifacts(before, incoming)["prefixVerified"] is True
    wrong_schema = copy.deepcopy(documents["changes.json"])
    wrong_schema["schemaVersion"] = 1
    _json(incoming / ".musubix/evidence/changes.json", wrong_schema)
    with pytest.raises(ValueError, match="Unsupported native evidence schema"):
        validate_replay_artifacts(before, incoming)
    _json(incoming / ".musubix/evidence/changes.json", documents["changes.json"])
    damaged = copy.deepcopy(documents["tdd.json"])
    damaged["cycles"][0]["green"]["valid"] = False
    _json(incoming / ".musubix/evidence/tdd.json", damaged)
    with pytest.raises(ValueError, match="preserv|prefix"):
        validate_replay_artifacts(before, incoming)
    _json(incoming / ".musubix/evidence/tdd.json", documents["tdd.json"])

    script = ROOT / "scripts/gate_recovery_transport.mjs"
    plan = tmp_path / "plan.json"
    manifest = tmp_path / "transaction.json"
    _json(
        plan,
        {
            "root": str(before),
            "incomingRoot": str(incoming),
            "nativePackage": str(_native_package()),
            "inputFiles": ["src/example.py"],
            "files": [".musubix/evidence/" + name for name in documents],
        },
    )

    def run(*args, expected=0):
        result = subprocess.run(
            ["node", str(script), *map(str, args)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == expected, result.stdout + result.stderr
        return json.loads(result.stdout) if result.returncode == 0 else result.stderr

    _json(incoming / ".musubix/evidence/changes.json", wrong_schema)
    assert "Unsupported evidence schema" in run("plan", plan, manifest, expected=1)
    _json(incoming / ".musubix/evidence/changes.json", documents["changes.json"])
    run("plan", plan, manifest)
    planned = json.loads(manifest.read_text())
    assert planned["state"] == "planned"
    assert planned["before"]["order"]["sequence"] == 1
    assert planned["after"]["order"]["sequence"] == 2
    interrupted = subprocess.run(
        [
            "node",
            "--input-type=module",
            "-e",
            (
                "const m = await import(process.argv[1]);"
                "await m.applyTransport(process.argv[2], {"
                "afterRename: () => { throw new Error('injected interruption'); }});"
            ),
            script.as_uri(),
            str(manifest),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert interrupted.returncode != 0
    assert "injected interruption" in interrupted.stderr
    assert json.loads(manifest.read_text())["state"] == "applying"
    recovered = run("recover", manifest)
    assert recovered["state"] == "completed"
    assert recovered["inputsVerified"] is True
    assert recovered["prefixVerified"] is True
    assert (before / ".musubix/evidence/order.json").read_bytes() == (
        incoming / ".musubix/evidence/order.json"
    ).read_bytes()
    assert run("recover", manifest)["state"] == "completed"
    successor = copy.deepcopy(after_order)
    successor["records"].append({"sequence": 3, "recordSha256": "d"})
    _json(before / ".musubix/evidence/order.json", successor)
    assert run("recover", manifest)["prefixVerified"] is True
    _json(before / ".musubix/evidence/order.json", documents["order.json"])
    assert "prefix" in run("recover", manifest, expected=1).lower()
    _json(before / ".musubix/evidence/order.json", successor)
    (before / "src/example.py").write_text("value = 2\n")
    assert "input" in run("recover", manifest, expected=1).lower()
    (before / "src/example.py").write_text("value = 1\n")
    tampered = json.loads(manifest.read_text())
    tampered["files"] = [
        {
            "path": "src/example.py",
            "beforeSha256": _sha(b"value = 1\n"),
            "afterSha256": _sha(b"value = 1\n"),
        }
    ]
    unsafe_manifest = tmp_path / "tampered.json"
    _json(unsafe_manifest, tampered)
    assert "artifact" in run("recover", unsafe_manifest, expected=1).lower()

    marker = tmp_path / "writer-ready"
    holder = subprocess.Popen(
        [
            "node",
            "--input-type=module",
            "-e",
            (
                "import { createRequire } from 'node:module';"
                "import { pathToFileURL } from 'node:url';"
                "import { writeFile } from 'node:fs/promises';"
                "const api = await import(pathToFileURL(createRequire(process.argv[1])"
                ".resolve('musubix3/analysis')));"
                "const stopped = new Promise(r => process.stdin.once('data', r));"
                "await api.withEvidenceWriterLock(process.argv[2], 'test-writer', async () => {"
                "await writeFile(process.argv[3], 'ready'); await stopped; });"
            ),
            planned["nativeModule"]["packagePath"],
            str(before),
            str(marker),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline and holder.poll() is None:
            time.sleep(0.01)
        assert marker.exists(), "Native competing writer did not acquire its lock"
        assert "EVIDENCE_WRITER" in run("recover", manifest, expected=1)
    finally:
        holder.communicate(input="\n", timeout=10)

    _json(before / ".musubix/evidence/order.json", documents["order.json"])
    second_manifest = tmp_path / "second-transaction.json"
    run("plan", plan, second_manifest)
    second_interrupt = subprocess.run(
        [
            "node",
            "--input-type=module",
            "-e",
            (
                "const m = await import(process.argv[1]);"
                "await m.applyTransport(process.argv[2], {"
                "afterProgress: () => { throw new Error('injected progress interruption'); }});"
            ),
            script.as_uri(),
            str(second_manifest),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert second_interrupt.returncode != 0
    assert json.loads(second_manifest.read_text())["completedPaths"]
    assert run("recover", second_manifest)["state"] == "completed"
    _json(before / ".musubix/evidence/order.json", documents["order.json"])
    race_manifest = tmp_path / "race-transaction.json"
    run("plan", plan, race_manifest)
    external_path = before / ".musubix/evidence/tdd.json"
    interfered = subprocess.run(
        [
            "node",
            "--input-type=module",
            "-e",
            (
                "import { writeFile } from 'node:fs/promises';"
                "const m = await import(process.argv[1]); let injected = false;"
                "await m.applyTransport(process.argv[2], { afterRename: async () => {"
                "if (!injected) { injected = true;"
                "await writeFile(process.argv[3], 'uncoordinated write\\n'); } }});"
            ),
            script.as_uri(),
            str(race_manifest),
            str(external_path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert interfered.returncode != 0
    assert "Unknown current artifact hash" in interfered.stderr
    assert external_path.read_bytes() == b"uncoordinated write\n"
    unapproved = json.loads(plan.read_text())
    unapproved["files"] = [".musubix/evidence/approvals/design.json"]
    _json(plan, unapproved)
    assert "artifact" in run("plan", plan, tmp_path / "unsafe.json", expected=1).lower()


# @id TEST-GATE-RECOVERY-001
# @verifies REQ-GATE-RECOVERY-001
def test_TEST_GATE_RECOVERY_001_audits_real_sources_and_preserves_evidence(tmp_path):
    from gate_recovery import audit_replay_sources, build_replay_provenance

    root = tmp_path / "repository"
    (root / "src").mkdir(parents=True)
    (root / "src/empty.py").write_bytes(b"")
    _git(root, "init", "-q")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "Initial real tree")
    old = _git(root, "rev-parse", "HEAD")
    (root / "src/example.py").write_text("old = True\n")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "Introduce implementation")
    (root / "src/example.py").write_text("fixed = True\n")
    audit = audit_replay_sources(root, old, ["src/example.py", "src/empty.py"])
    assert audit["revision"] == old
    assert audit["files"]["src/example.py"]["past"] == {"exists": False, "sha256": None}
    assert audit["files"]["src/empty.py"]["past"] == {"exists": True, "sha256": _sha(b"")}
    assert audit["files"]["src/example.py"]["current"]["sha256"] == _sha(b"fixed = True\n")
    for revision, paths in [
        ("HEAD", ["src/example.py"]),
        ("not-a-real-commit", ["src/example.py"]),
        (old, ["../outside.py"]),
        (old, [str(root / "src/example.py")]),
        (old, ["tests/test_example.py"]),
        (old, [".musubix/evidence/tdd.json"]),
        (old, ["src/empty.py"]),
    ]:
        with pytest.raises(ValueError):
            audit_replay_sources(root, revision, paths)
    alternate = _git(root, "commit-tree", "HEAD^{tree}", "-p", old, "-m", "Other branch")
    with pytest.raises(ValueError, match="ancestor"):
        audit_replay_sources(root, alternate, ["src/example.py"])
    (root / "src/link.py").symlink_to(tmp_path / "outside.py")
    with pytest.raises(ValueError, match="path|symlink"):
        audit_replay_sources(root, old, ["src/link.py"])

    record = tmp_path / "record.json"
    report = tmp_path / "report.json"
    record.write_text('{"valid": true}')
    report.write_text('{"selected": 1}')
    phase = {
        "audit": audit,
        "testId": "TEST-EXAMPLE-001",
        "testSha256": _sha(b"immutable assertions"),
        "command": ".venv/bin/pytest -k test_TEST_EXAMPLE_001",
        "environmentSha256": _sha(b"fixed environment"),
        "sources": {name: data["past"] for name, data in audit["files"].items()},
        "selected": 1,
        "exitCode": 1,
        "testStatus": "failed",
        "record": {"path": str(record), "sha256": _sha(record.read_bytes())},
        "report": {"path": str(report), "sha256": _sha(report.read_bytes())},
    }
    green = {
        **phase,
        "exitCode": 0,
        "testStatus": "passed",
        "sources": {name: data["current"] for name, data in audit["files"].items()},
    }
    assert build_replay_provenance(phase, green)["valid"] is True
    for key, value in [
        ("testSha256", _sha(b"changed assertions")),
        ("command", "another command"),
        ("environmentSha256", _sha(b"changed environment")),
        ("selected", 0),
        ("exitCode", 1),
        ("sources", phase["sources"]),
    ]:
        with pytest.raises(ValueError):
            build_replay_provenance(phase, {**green, key: value})
    forged_audits = []
    empty_audit = {**audit, "files": {}}
    forged_audits.append(empty_audit)
    forged_audits.append({**audit, "head": audit["revision"]})
    forged_audits.append({**audit, "revision": 123})
    unchanged_audit = copy.deepcopy(audit)
    for row in unchanged_audit["files"].values():
        row["past"] = row["current"]
    forged_audits.append(unchanged_audit)
    for forged in forged_audits:
        red_sources = {name: data["past"] for name, data in forged["files"].items()}
        green_sources = {name: data["current"] for name, data in forged["files"].items()}
        with pytest.raises(ValueError):
            build_replay_provenance(
                {**phase, "audit": forged, "sources": red_sources},
                {**green, "audit": forged, "sources": green_sources},
            )
    with pytest.raises(ValueError):
        build_replay_provenance({**phase, "record": {"sha256": _sha(b"")}}, green)
    report.write_text("changed after execution")
    with pytest.raises(ValueError, match="hash"):
        build_replay_provenance(phase, green)
    _transport(tmp_path / "transport")


# @id TEST-GATE-RECOVERY-002
# @verifies REQ-GATE-RECOVERY-002
def test_TEST_GATE_RECOVERY_002_plans_only_actual_complete_historical_scopes(tmp_path):
    from inspect import signature

    from gate_recovery import plan_historical_waivers

    def diagnostic(code, **fields):
        return {"code": code, "severity": "error", **fields}

    scopes = [
        diagnostic("CHANGE_RECORD_MISSING", changeId="CHANGE-022"),
        diagnostic("CHANGE_PHASE_MISSING", changeId="CHANGE-020", detail="phase:red"),
        diagnostic("CHANGE_RED_UNPROVEN", changeId="CHANGE-001", requirementId="REQ-AISCI-004"),
        diagnostic("CHANGE_GREEN_UNPROVEN", changeId="CHANGE-019", requirementId="REQ-AISCI-004"),
        diagnostic("CHANGE_COMPLETENESS_TDD", changeId="CHANGE-026", requirementId="REQ-AIDS-044"),
        diagnostic("CHANGE_COMPLETENESS_TDD", changeId="CHANGE-003", requirementId="REQ-AIMS-002"),
        diagnostic("CHANGE_RED_UNPROVEN", changeId="CHANGE-011", requirementId="REQ-AIDS-082"),
        diagnostic("CHANGE_GREEN_UNPROVEN", changeId="CHANGE-039", requirementId="REQ-AIDS-110"),
        diagnostic(
            "CHANGE_ORDER_MIGRATION_REQUIRED",
            changeId="CHANGE-021",
            detail="requirement:REQ-ACHEM-100",
        ),
    ]
    malformed = [
        diagnostic("CHANGE_GREEN_UNPROVEN", changeId="CHANGE-019"),
        diagnostic("CHANGE_PHASE_MISSING", changeId="CHANGE-020"),
        diagnostic("CHANGE_RECORD_MISSING", changeId="CHANGE-042"),
        diagnostic("CHANGE_RED_UNPROVEN", changeId="CHANGE-001", requirementId="REQ-AISCI-999"),
        diagnostic("CHANGE_PHASE_MISSING", changeId="CHANGE-020", detail="phase:impact"),
        diagnostic("CHANGE_RED_UNPROVEN", changeId="CHANGE-003", requirementId="REQ-AIMS-002"),
        diagnostic(
            "CHANGE_ORDER_MIGRATION_REQUIRED", changeId="CHANGE-021", requirementId="REQ-ACHEM-100"
        ),
        diagnostic(
            "CHANGE_ORDER_MIGRATION_REQUIRED",
            changeId="CHANGE-021",
            detail="requirement:REQ-ACHEM-101",
        ),
        diagnostic(
            "CHANGE_ORDER_MIGRATION_REQUIRED",
            changeId="CHANGE-039",
            detail="requirement:REQ-ACHEM-100",
        ),
        diagnostic("CHANGE_REQUIREMENTS_MISMATCH", changeId="CHANGE-026"),
        diagnostic("TDD_TEST_STALE", testId="TEST-AIDS-021"),
        diagnostic("CHANGE_RECORD_MISSING", changeId="CHANGE-022", requirementId="REQ-AIDS-044"),
        diagnostic(
            "CHANGE_PHASE_MISSING",
            changeId="CHANGE-020",
            detail="phase:red",
            requirementId="REQ-AISCI-023",
        ),
        diagnostic(
            "CHANGE_RED_UNPROVEN",
            changeId="CHANGE-001",
            requirementId="REQ-AISCI-004",
            detail="phase:red",
        ),
    ]
    stale = {
        "code": "CHANGE_WAIVER_STALE",
        "severity": "warning",
        "changeId": "CHANGE-005",
        "message": "Waiver for CHANGE-005:CHANGE_GREEN_UNPROVEN:REQ-ACHEM-003 is stale.",
        "requirementId": "REQ-ACHEM-003",
    }
    report = {
        "checks": [
            {"name": "change-history", "diagnostics": [*scopes, *malformed, stale]},
            {"name": "change-completeness", "diagnostics": scopes},
        ]
    }
    result = plan_historical_waivers(report)
    assert result["candidates"] == sorted(scopes, key=lambda row: json.dumps(row, sort_keys=True))
    assert len(result["blocked"]) == len(malformed)
    assert result["resolved_stale"] == [stale]
    assert len(plan_historical_waivers({"checks": [{"diagnostics": [stale]}]})["candidates"]) == 0
    with pytest.raises(ValueError):
        plan_historical_waivers({"checks": "not a report"})
    exception = diagnostic(
        "CHANGE_TEST_CHANGED_AFTER_RED",
        changeId="CHANGE-045",
        detail="REQ-GATE-RECOVERY-002,REQ-GATE-RECOVERY-003",
    )
    scoped = {"checks": [{"diagnostics": [exception]}]}
    assert plan_historical_waivers(scoped)["blocked"] == [exception]
    context = _recording_exception_fixture(tmp_path)
    kwargs = (
        {"chronology_context": context}
        if "chronology_context" in signature(plan_historical_waivers).parameters
        else {}
    )
    assert plan_historical_waivers(scoped, **kwargs)["candidates"] == [exception]
    for fields in [
        {"changeId": "CHANGE-044"},
        {"requirementId": "REQ-GATE-RECOVERY-002"},
        {"detail": "REQ-GATE-RECOVERY-003,REQ-GATE-RECOVERY-002"},
        {"detail": "REQ-GATE-RECOVERY-002"},
    ]:
        row = {**exception, **fields}
        assert plan_historical_waivers(
            {"checks": [{"diagnostics": [row]}]}, chronology_context=context
        )["blocked"] == [row]
    with pytest.raises(ValueError, match="hash|identity"):
        plan_historical_waivers(scoped, chronology_context={**context, "expected_sha256": "0" * 64})
    proof = context["proof"].read_bytes()
    document = json.loads(proof)
    red = Path(document["phases"]["red"]["path"])
    red.write_bytes(red.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="hash"):
        plan_historical_waivers(scoped, chronology_context=context)
    red.write_bytes(red.read_bytes()[:-1])
    document["phases"]["red"]["testsFingerprint"] = "0" * 64
    _json(context["proof"], document)
    with pytest.raises(ValueError, match="fingerprint"):
        plan_historical_waivers(
            scoped,
            chronology_context={**context, "expected_sha256": _sha(context["proof"].read_bytes())},
        )


# @id TEST-GATE-RECOVERY-003
# @verifies REQ-GATE-RECOVERY-003
def test_TEST_GATE_RECOVERY_003_distinguishes_candidate_ready_and_blocked(tmp_path, monkeypatch):
    from gate_recovery import assess_recovery_readiness

    _native_followup_contract(tmp_path / "native-contract")
    expected = ["commands", "tdd", "approval"]
    gate = {
        "status": "pass",
        "checks": [{"name": name, "status": "pass", "required": True} for name in expected],
    }
    approval = {
        "stages": [
            {"stage": name, "status": "approved"} for name in ["requirements", "design", "release"]
        ]
    }
    transport = {
        "state": "completed",
        "inputsVerified": True,
        "prefixVerified": True,
        "followupVerified": True,
    }
    assert assess_recovery_readiness(gate, expected, approval, transport)["ready"] is False
    from gate_recovery import RecoveryValidationError, validate_recovery_followup

    transport, followup, calls = _followup_fixture(tmp_path, monkeypatch)
    assert validate_recovery_followup(**transport)["followupVerified"] is True
    assert calls and calls[-1][:2] == (transport["root"], tmp_path / "original")
    assert assess_recovery_readiness(gate, expected, approval, transport)["ready"] is True
    saved = transport["followup"].read_bytes()
    for field in ["inputChanges", "greenFiles", "approvals", "correctionArtifacts"]:
        invalid = copy.deepcopy(followup)
        invalid[field] = [] if field == "inputChanges" else {}
        _json(transport["followup"], invalid)
        with pytest.raises(RecoveryValidationError):
            validate_recovery_followup(**transport)
        assert assess_recovery_readiness(gate, expected, approval, transport)["candidate"] is False
    invalid = copy.deepcopy(followup)
    invalid["inputChanges"].append(copy.deepcopy(invalid["inputChanges"][0]))
    _json(transport["followup"], invalid)
    with pytest.raises(RecoveryValidationError, match="duplicate|Duplicate"):
        validate_recovery_followup(**transport)
    invalid = copy.deepcopy(followup)
    correction_path = Path(invalid["correctionArtifacts"]["green"]["path"])
    correction = json.loads(correction_path.read_bytes())
    correction["changes"][0]["phases"]["green"]["order"] += 1
    tampered = tmp_path / "tampered-correction.json"
    _json(tampered, correction)
    invalid["correctionArtifacts"]["green"] = {
        "path": str(tampered),
        "sha256": _sha(tampered.read_bytes()),
    }
    _json(transport["followup"], invalid)
    with pytest.raises(RecoveryValidationError, match="correction|Correction"):
        validate_recovery_followup(**transport)
    transport["followup"].write_bytes(saved)
    for path in [
        transport["root"] / "scripts/gate_recovery.py",
        transport["root"] / ".musubix/evidence/native/recovery/fixture/provenance.json",
        transport["original_receipt"],
        tmp_path / "green.json",
    ]:
        data = path.read_bytes()
        path.write_bytes(data + b"\n ")
        with pytest.raises(RecoveryValidationError):
            validate_recovery_followup(**transport)
        path.write_bytes(data)
    unknown = transport["root"] / "scripts/unapproved.py"
    unknown.write_text("changed = True\n")
    with pytest.raises(RecoveryValidationError, match="scope|input|Input"):
        validate_recovery_followup(**transport)
    unknown.unlink()
    before_native = len(calls)
    assert validate_recovery_followup(**transport)["state"] == "completed"
    assert len(calls) == before_native + 1
    monkeypatch.setattr(
        "gate_recovery._runtime_inventory",
        lambda folder: {"python": "3.12.13", "packages": {"example": "2"}},
    )
    with pytest.raises(RecoveryValidationError, match="environment|runtime|Runtime"):
        validate_recovery_followup(**transport)
    monkeypatch.undo()
    transport, _, _ = _followup_fixture(tmp_path / "valid", monkeypatch)
    candidate = copy.deepcopy(gate)
    candidate["status"] = "fail"
    candidate["checks"][-1]["status"] = "fail"
    candidate["checks"][-1]["diagnostics"] = [
        {
            "code": "APPROVAL_MISSING",
            "path": ".musubix/evidence/approvals/release.json",
        }
    ]
    pending = copy.deepcopy(approval)
    pending["stages"][-1]["status"] = "missing"
    result = assess_recovery_readiness(candidate, expected, pending, transport)
    assert result["candidate"] is True
    assert result["ready"] is False
    for status in ["fail", "skipped", "unknown"]:
        invalid = copy.deepcopy(gate)
        invalid["checks"][0]["status"] = status
        result = assess_recovery_readiness(invalid, expected, approval, transport)
        assert result["ready"] is False
        assert result["candidate"] is False
        assert result["blockers"]
    for invalid in [
        {**gate, "checks": gate["checks"][:-1]},
        {**gate, "checks": [*gate["checks"], gate["checks"][0]]},
        {**gate, "status": "fail"},
        {
            **gate,
            "checks": [*gate["checks"], {"name": "implicit", "required": True, "status": "fail"}],
        },
    ]:
        assert (
            assess_recovery_readiness(invalid, expected, approval, transport)["candidate"] is False
        )
    for stages in [
        approval["stages"][:-1],
        [*approval["stages"], approval["stages"][0]],
        [{**stage, "status": "stale"} for stage in approval["stages"]],
    ]:
        assert (
            assess_recovery_readiness(gate, expected, {"stages": stages}, transport)["ready"]
            is False
        )
    for state in ["planned", "applying", "blocked"]:
        assert (
            assess_recovery_readiness(gate, expected, approval, {**transport, "state": state})[
                "candidate"
            ]
            is False
        )
    for field in ["inputsVerified", "prefixVerified"]:
        assert (
            assess_recovery_readiness(gate, expected, approval, {**transport, field: False})[
                "ready"
            ]
            is False
        )
    assert assess_recovery_readiness(gate, [], approval, transport)["ready"] is False
    assert (
        assess_recovery_readiness(gate, [*expected, "tdd"], approval, transport)["ready"] is False
    )
