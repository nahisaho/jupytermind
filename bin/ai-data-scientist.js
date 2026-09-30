#!/usr/bin/env node
"use strict";

/**
 * npm bootstrap entrypoint for the ai-data-scientist Copilot Agent Skill.
 *
 * This script intentionally does NOT run as an npm "postinstall" script:
 * starting with npm v12, install-lifecycle scripts from dependencies are
 * disabled by default and require each consumer to run
 * `npm approve-scripts`, which is not a realistic onboarding step for a
 * published skill package. Instead, environment setup happens lazily on
 * the first invocation of this CLI (`npx ai-data-scientist setup`, or any
 * other subcommand), and is cached via a marker file so later invocations
 * are fast.
 */

const { spawnSync } = require("node:child_process");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");

const PACKAGE_ROOT = path.resolve(__dirname, "..");
const VENV_DIR = path.join(PACKAGE_ROOT, ".venv");
const IS_WINDOWS = process.platform === "win32";
const VENV_PYTHON = path.join(
  VENV_DIR,
  IS_WINDOWS ? "Scripts" : "bin",
  IS_WINDOWS ? "python.exe" : "python"
);
const PYPROJECT_PATH = path.join(PACKAGE_ROOT, "pyproject.toml");
const MARKER_PATH = path.join(VENV_DIR, ".ai-data-scientist-setup-complete.json");

function log(message) {
  process.stderr.write(`[ai-data-scientist] ${message}\n`);
}

function fileHash(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function findPythonLauncher() {
  const candidates = IS_WINDOWS ? ["python", "python3"] : ["python3", "python"];
  for (const candidate of candidates) {
    const probe = spawnSync(candidate, ["--version"], { stdio: "ignore" });
    if (probe.status === 0) return candidate;
  }
  throw new Error(
    "No Python 3 interpreter found on PATH (PATHにPython 3が見つかりません). " +
      "Install Python 3.10+ and re-run this command."
  );
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, { stdio: "inherit", cwd: PACKAGE_ROOT, ...options });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new Error(`Command failed (${result.status}): ${command} ${args.join(" ")}`);
  }
}

function readMarker() {
  try {
    return JSON.parse(fs.readFileSync(MARKER_PATH, "utf8"));
  } catch {
    return null;
  }
}

function isSetupCurrent() {
  if (!fs.existsSync(VENV_PYTHON)) return false;
  const marker = readMarker();
  if (!marker) return false;
  return marker.pyprojectSha256 === fileHash(PYPROJECT_PATH);
}

function ensureSetup() {
  if (isSetupCurrent()) return;

  log("Setting up Python environment (初回セットアップ: Python仮想環境を構築します)...");
  const python = findPythonLauncher();

  if (!fs.existsSync(VENV_DIR)) {
    run(python, ["-m", "venv", VENV_DIR]);
  }
  run(VENV_PYTHON, ["-m", "pip", "install", "--upgrade", "pip"]);
  run(VENV_PYTHON, ["-m", "pip", "install", "-e", PACKAGE_ROOT]);

  fs.writeFileSync(
    MARKER_PATH,
    JSON.stringify(
      { pyprojectSha256: fileHash(PYPROJECT_PATH), completedAt: new Date().toISOString() },
      null,
      2
    )
  );
  log("Setup complete (セットアップが完了しました).");
}

function main() {
  const [command, ...rest] = process.argv.slice(2);

  ensureSetup();

  if (!command || command === "setup") {
    log("Environment ready (環境は準備済みです).");
    return;
  }

  if (command === "test") {
    run(VENV_PYTHON, ["-m", "pytest", ...rest]);
    return;
  }

  // Pass through to the Python CLI for every other subcommand.
  run(VENV_PYTHON, ["-m", "ai_data_scientist.cli", command, ...rest]);
}

try {
  main();
} catch (err) {
  log(err.message || String(err));
  process.exit(1);
}
