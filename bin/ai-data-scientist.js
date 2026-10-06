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
const SKILLS_SOURCE_DIR = path.join(PACKAGE_ROOT, ".github", "skills");
const SKILL_ALLOWLIST = Object.freeze([
  "ai-data-scientist",
  "ai-chemistry-scientist",
  "ai-genomics-scientist",
  "ai-materials-scientist",
  "ai-structural-biology-scientist",
  "ai-scientist",
  "tech-writer",
  "japanese-prose",
  "presentation-planner",
]);

class SkillDeployError extends Error {}

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

function realpathNative(targetPath) {
  return fs.realpathSync.native(targetPath);
}

function isContained(candidateReal, rootReal) {
  return candidateReal === rootReal || candidateReal.startsWith(rootReal + path.sep);
}

function lstatIfExists(targetPath) {
  try {
    return fs.lstatSync(targetPath);
  } catch (err) {
    if (err.code === "ENOENT") return null;
    throw err;
  }
}

// Walks `targetDir` upward to the nearest already-existing ancestor and
// verifies that ancestor's real path is contained within `cwdReal` before
// anything beneath it may be created.
function resolveContainedAncestor(targetDir, cwdReal) {
  let current = targetDir;
  while (!fs.existsSync(current)) {
    const parent = path.dirname(current);
    if (parent === current) {
      throw new SkillDeployError(`No existing ancestor directory found for ${targetDir}`);
    }
    current = parent;
  }
  const existingAncestorReal = realpathNative(current);
  if (!isContained(existingAncestorReal, cwdReal)) {
    throw new SkillDeployError(
      `Refusing to use ${current} as an ancestor of ${targetDir}: it resolves ` +
        `outside the current working directory (${existingAncestorReal})`
    );
  }
  const missingComponents =
    targetDir === current
      ? []
      : path.relative(current, targetDir).split(path.sep).filter(Boolean);
  return { existingAncestorPath: current, existingAncestorReal, missingComponents };
}

// Creates `targetDir` one path segment at a time, re-verifying containment
// against `cwdReal` after creating each segment, before descending to the
// next one. Returns `targetDir`'s own verified real path.
function ensureContainedDir(targetDir, cwdReal) {
  const { existingAncestorPath, missingComponents } = resolveContainedAncestor(targetDir, cwdReal);
  let currentPath = existingAncestorPath;
  for (const component of missingComponents) {
    currentPath = path.join(currentPath, component);
    fs.mkdirSync(currentPath);
    const currentReal = realpathNative(currentPath);
    if (!isContained(currentReal, cwdReal)) {
      throw new SkillDeployError(
        `Refusing to continue past ${currentPath}: it resolves outside the ` +
          `current working directory (${currentReal})`
      );
    }
  }
  return realpathNative(targetDir);
}

/** @id CODE-AIDS-148
 * @implements REQ-AIDS-097
 * @design DES-AIDS-095
 */
// Deploys the 9 allowlisted skills from the installed package's
// `.github/skills/` into `<cwd>/.github/skills/`. Runs a full preflight of
// all 9 destinations (symlink-identity rejection plus canonical-skills-root
// containment) before removing or copying any of them, so a failure on a
// later skill never destroys an earlier, already-verified one.
function deploySkills() {
  const cwd = process.cwd();
  const cwdReal = realpathNative(cwd);
  const skillsRootReal = ensureContainedDir(path.join(cwd, ".github", "skills"), cwdReal);

  const plan = [];
  for (const name of SKILL_ALLOWLIST) {
    const destination = path.join(skillsRootReal, name);
    const lst = lstatIfExists(destination);
    if (lst) {
      if (lst.isSymbolicLink()) {
        throw new SkillDeployError(
          `Refusing to deploy skill "${name}": destination ${destination} is itself a symlink`
        );
      }
      const destinationReal = realpathNative(destination);
      if (!isContained(destinationReal, skillsRootReal)) {
        throw new SkillDeployError(
          `Refusing to deploy skill "${name}": destination ${destination} resolves ` +
            `outside the skills root (${destinationReal})`
        );
      }
    }
    plan.push({ name, destination });
  }

  for (const { name, destination } of plan) {
    const source = path.join(SKILLS_SOURCE_DIR, name);
    if (fs.existsSync(destination)) {
      fs.rmSync(destination, { recursive: true, force: true });
    }
    fs.cpSync(source, destination, { recursive: true });
    log(`Deployed skill "${name}" to ${destination}`);
  }
}

/** @id CODE-AIDS-149
 * @implements REQ-AIDS-097
 * @design DES-AIDS-095
 */
// Verifies the application Python modules the 9 deployed skills' documented
// entry points depend on are importable from the bootstrap venv.
function verifySkillPythonModules() {
  run(VENV_PYTHON, [
    "-c",
    "import ai_data_scientist, ai_chemistry_scientist, ai_genomics_scientist, " +
      "ai_materials_scientist, ai_structural_biology_scientist, ai_scientist",
  ]);
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
    deploySkills();
    verifySkillPythonModules();
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
