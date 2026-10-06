"""Tests for REQ-AIDS-097: `npx jupytermind setup` / `npx ai-data-scientist
setup` deploys the 9 allowlisted `.github/skills` into the consuming
project with an all-or-nothing, containment-checked preflight, and
verifies the application Python modules those skills depend on are
importable from the bootstrap venv.

TEST-AIDS-307 through TEST-AIDS-316 (CHANGE-031).

Most scenarios invoke `bin/ai-data-scientist.js` as a real subprocess with
`cwd` set to a temporary "consumer project" directory, while the script's
own `PACKAGE_ROOT` (resolved from `__dirname`, independent of `cwd`)
stays pinned to this repository checkout, so the already-built `.venv`
and the real `.github/skills` source tree are reused without any
environment-variable test seam.

TEST-AIDS-312 and TEST-AIDS-316 instead exercise the actual consumer-
facing install path end-to-end: `npm pack` + `npm install` into a real
consumer project's own `node_modules`, then the real `npx --no-install
<bin> setup` command run from that project's own directory, resolving
the CLI strictly through npm's own `node_modules/.bin` PATH mechanism
rather than an absolute script path chosen by the test.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI_SCRIPT = REPO_ROOT / "bin" / "ai-data-scientist.js"
SKILL_ALLOWLIST = (
    "ai-data-scientist",
    "ai-chemistry-scientist",
    "ai-genomics-scientist",
    "ai-materials-scientist",
    "ai-structural-biology-scientist",
    "ai-scientist",
    "tech-writer",
    "japanese-prose",
    "presentation-planner",
)


def _run_setup(cwd: Path, command: str = "setup") -> subprocess.CompletedProcess:
    return subprocess.run(
        ["node", str(CLI_SCRIPT), command],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )


def _tree_snapshot(root: Path) -> dict[str, bytes]:
    snapshot: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            snapshot[str(path.relative_to(root))] = path.read_bytes()
    return snapshot


def _install_packed_tarball(tmp_path: Path) -> Path:
    """Packs this repository's npm package into a real tarball and installs
    it directly into the consumer project directory under `tmp_path`
    (`<consumer>/node_modules/jupytermind`), returning that consumer
    project directory. This is the actual consumer-facing install path
    REQ-AIDS-097 describes: `npm install jupytermind` run from inside a
    project, as opposed to invoking `bin/ai-data-scientist.js` directly
    from this checkout, or installing into one directory while running
    the CLI from an unrelated directory.

    The installed copy's own `.venv` is a symlink to this checkout's
    already-bootstrapped `.venv` (whose marker file's `pyprojectSha256`
    matches the installed, byte-identical `pyproject.toml`), so
    `ensureSetup()` legitimately short-circuits instead of redundantly
    rebuilding an identical multi-hundred-megabyte virtual environment for
    every test invocation; this does not weaken the assertions below,
    which are specifically about skill-tree deployment sourced from the
    installed package directory, not about venv bootstrapping (covered by
    pre-existing tests).
    """
    pack_dir = tmp_path / "pack"
    pack_dir.mkdir()
    pack_result = subprocess.run(
        ["npm", "pack", "--silent", "--pack-destination", str(pack_dir)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=True,
    )
    tarball_name = pack_result.stdout.strip().splitlines()[-1]
    tarball_path = pack_dir / tarball_name

    consumer_project = tmp_path / "consumer-project"
    consumer_project.mkdir()
    subprocess.run(
        [
            "npm",
            "install",
            "--silent",
            "--no-audit",
            "--no-fund",
            str(tarball_path),
        ],
        cwd=consumer_project,
        capture_output=True,
        text=True,
        timeout=180,
        check=True,
    )
    installed_root = consumer_project / "node_modules" / "jupytermind"
    assert installed_root.is_dir(), "npm install did not create node_modules/jupytermind"
    assert (installed_root / ".github" / "skills").is_dir()
    assert (consumer_project / "node_modules" / ".bin" / "jupytermind").exists(), (
        "npm did not generate a bin shim for jupytermind"
    )
    assert (consumer_project / "node_modules" / ".bin" / "ai-data-scientist").exists(), (
        "npm did not generate a bin shim for ai-data-scientist"
    )

    os.symlink(REPO_ROOT / ".venv", installed_root / ".venv")
    return consumer_project


# @id TEST-AIDS-307
# @verifies REQ-AIDS-097
def test_TEST_AIDS_307_clean_install_deploys_all_nine_skills_with_full_tree(tmp_path):
    result = _run_setup(tmp_path)
    assert result.returncode == 0, result.stderr

    skills_dir = tmp_path / ".github" / "skills"
    assert skills_dir.is_dir()

    for name in SKILL_ALLOWLIST:
        source = REPO_ROOT / ".github" / "skills" / name
        destination = skills_dir / name
        assert destination.is_dir(), f"{name} was not deployed"
        assert _tree_snapshot(source) == _tree_snapshot(destination), (
            f"{name}'s deployed tree does not byte-match the packaged source"
        )

    assert not any(p.name.startswith("sdd-") for p in skills_dir.iterdir())


# @id TEST-AIDS-308
# @verifies REQ-AIDS-097
def test_TEST_AIDS_308_allowlist_excludes_sdd_test_double_even_when_present_in_source(
    tmp_path,
):
    injected = REPO_ROOT / ".github" / "skills" / "sdd-test"
    injected.mkdir()
    (injected / "SKILL.md").write_text("test double, must never be deployed\n", encoding="utf-8")
    try:
        result = _run_setup(tmp_path)
        assert result.returncode == 0, result.stderr
        assert not (tmp_path / ".github" / "skills" / "sdd-test").exists()
    finally:
        (injected / "SKILL.md").unlink()
        injected.rmdir()


# @id TEST-AIDS-309
# @verifies REQ-AIDS-097
def test_TEST_AIDS_309_stale_leftover_and_local_modification_are_overwritten(tmp_path):
    destination = tmp_path / ".github" / "skills" / "ai-data-scientist"
    destination.mkdir(parents=True)
    (destination / "SKILL.md").write_text("locally modified\n", encoding="utf-8")
    (destination / "local-notes.txt").write_text("stale leftover\n", encoding="utf-8")

    result = _run_setup(tmp_path)
    assert result.returncode == 0, result.stderr

    source = REPO_ROOT / ".github" / "skills" / "ai-data-scientist"
    assert _tree_snapshot(source) == _tree_snapshot(destination)
    assert not (destination / "local-notes.txt").exists()
    assert "ai-data-scientist" in result.stderr
    assert str(destination) in result.stderr


# @id TEST-AIDS-310
# @verifies REQ-AIDS-097
def test_TEST_AIDS_310_symlink_escape_rejected_before_any_destructive_write(tmp_path):
    skills_dir = tmp_path / ".github" / "skills"
    skills_dir.mkdir(parents=True)

    sentinel_dir = skills_dir / "ai-data-scientist"
    sentinel_dir.mkdir()
    sentinel_file = sentinel_dir / "sentinel.txt"
    sentinel_file.write_text("do-not-touch\n", encoding="utf-8")

    outside_target = tmp_path.parent / f"{tmp_path.name}-outside-target"
    outside_target.mkdir()
    (skills_dir / "ai-genomics-scientist").symlink_to(outside_target, target_is_directory=True)

    result = _run_setup(tmp_path)

    assert result.returncode != 0
    assert "success" not in result.stdout.lower()
    assert sentinel_file.read_text(encoding="utf-8") == "do-not-touch\n"
    assert (skills_dir / "ai-genomics-scientist").is_symlink()
    assert list(outside_target.iterdir()) == []


# @id TEST-AIDS-311
# @verifies REQ-AIDS-097
def test_TEST_AIDS_311_destination_that_is_itself_a_symlink_is_rejected(tmp_path):
    skills_dir = tmp_path / ".github" / "skills"
    skills_dir.mkdir(parents=True)

    sentinel_dir = skills_dir / "ai-data-scientist"
    sentinel_dir.mkdir()
    sentinel_file = sentinel_dir / "sentinel.txt"
    sentinel_file.write_text("do-not-touch\n", encoding="utf-8")

    in_root_target = skills_dir / "ai-genomics-scientist-real"
    in_root_target.mkdir()
    (skills_dir / "ai-genomics-scientist").symlink_to(in_root_target, target_is_directory=True)

    result = _run_setup(tmp_path)

    assert result.returncode != 0
    assert "success" not in result.stdout.lower()
    assert sentinel_file.read_text(encoding="utf-8") == "do-not-touch\n"
    assert (skills_dir / "ai-genomics-scientist").is_symlink()


# @id TEST-AIDS-312
# @verifies REQ-AIDS-097
def test_TEST_AIDS_312_npx_ai_data_scientist_setup_alias_behaves_identically(tmp_path):
    """Runs the real `npx ai-data-scientist setup` command (via npm's own
    `npx`/PATH resolution, `--no-install` so it never silently reaches out
    to the registry) from inside the actual npm-installed consumer
    project, proving the alias is a genuine, independently resolvable npm
    `bin` entry rather than merely the same script path invoked two
    different ways in test code."""
    consumer = _install_packed_tarball(tmp_path)
    installed_root = consumer / "node_modules" / "jupytermind"
    result = subprocess.run(
        ["npx", "--no-install", "ai-data-scientist", "setup"],
        cwd=consumer,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    for name in SKILL_ALLOWLIST:
        source_dir = installed_root / ".github" / "skills" / name
        dest_dir = consumer / ".github" / "skills" / name
        assert dest_dir.is_dir(), f"{name} was not deployed"
        assert _tree_snapshot(dest_dir) == _tree_snapshot(source_dir), (
            f"{name}'s deployed tree does not byte-match the installed package's source"
        )


# @id TEST-AIDS-313
# @verifies REQ-AIDS-097
def test_TEST_AIDS_313_outward_symlinked_github_ancestor_rejected_before_any_write(tmp_path):
    outside_target = tmp_path.parent / f"{tmp_path.name}-github-outside"
    outside_target.mkdir()
    (tmp_path / ".github").symlink_to(outside_target, target_is_directory=True)

    result = _run_setup(tmp_path)

    assert result.returncode != 0
    assert "success" not in result.stdout.lower()
    assert (tmp_path / ".github").is_symlink()
    assert list(outside_target.iterdir()) == []


# @id TEST-AIDS-314
# @verifies REQ-AIDS-097
def test_TEST_AIDS_314_in_cwd_redirected_github_symlink_is_permitted(tmp_path):
    redirected_root = tmp_path / "alternate-output"
    redirected_root.mkdir()
    (tmp_path / ".github").symlink_to(redirected_root, target_is_directory=True)

    result = _run_setup(tmp_path)

    assert result.returncode == 0, result.stderr
    canonical_skills_root = redirected_root / "skills"
    assert canonical_skills_root.is_dir()
    for name in SKILL_ALLOWLIST:
        assert (canonical_skills_root / name).is_dir()
        assert (tmp_path / ".github" / "skills" / name).is_dir()


# @id TEST-AIDS-315
# @verifies REQ-AIDS-097
def test_TEST_AIDS_315_python_modules_importable_after_setup(tmp_path):
    result = _run_setup(tmp_path)
    assert result.returncode == 0, result.stderr

    venv_python = (
        REPO_ROOT
        / ".venv"
        / ("Scripts" if os.name == "nt" else "bin")
        / ("python.exe" if os.name == "nt" else "python")
    )
    import_check = subprocess.run(
        [
            str(venv_python),
            "-c",
            (
                "import ai_data_scientist, ai_chemistry_scientist, ai_genomics_scientist, "
                "ai_materials_scientist, ai_structural_biology_scientist, ai_scientist"
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert import_check.returncode == 0, import_check.stderr


# @id TEST-AIDS-316
# @verifies REQ-AIDS-097
def test_TEST_AIDS_316_installed_tarball_npx_jupytermind_setup_deploys_skills(tmp_path):
    """Proves the actual consumer-facing acceptance path end-to-end: a real
    `npm pack` tarball installed with `npm install` into a consumer
    project's own `node_modules`, then run via the real `npx jupytermind
    setup` command (`--no-install` so it resolves strictly from the
    already-installed local `node_modules/.bin`, never reaching out to the
    registry) executed from that consumer project's own directory —
    exactly as a real user would — deploys all 9 allowlisted skills whose
    file trees are byte-identical to the installed package's own
    `.github/skills/<name>/` sources."""
    consumer = _install_packed_tarball(tmp_path)
    installed_root = consumer / "node_modules" / "jupytermind"

    result = subprocess.run(
        ["npx", "--no-install", "jupytermind", "setup"],
        cwd=consumer,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    for name in SKILL_ALLOWLIST:
        source_dir = installed_root / ".github" / "skills" / name
        dest_dir = consumer / ".github" / "skills" / name
        assert dest_dir.is_dir()
        assert _tree_snapshot(dest_dir) == _tree_snapshot(source_dir)
    assert not (consumer / ".github" / "skills" / "sdd-test").exists()
