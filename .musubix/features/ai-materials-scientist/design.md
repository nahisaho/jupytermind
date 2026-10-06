---
schemaVersion: 1
feature: ai-materials-scientist
---
# Design / 設計

Architecture blueprint for the new `ai-materials-scientist` Copilot Agent
Skill. Mirrors the module-manifest dispatch pattern already used by
`ai-scientist` (`src/ai_scientist/manifest.py` /
`src/ai_scientist/phase_state.py`): a single skill entrypoint loads a
static manifest mapping a method name to a module function, and dispatches
to exactly one module per request. Every simulation module is a pure
Python/numpy/scipy implementation; none calls an external solver binary or
the network.

## DES-AIMS-001: Method manifest & request dispatcher / 手法マニフェストと要求振り分け
Responsibilities: Load the static method-name-to-module manifest, classify
an incoming bilingual user request against the seven supported method
names/synonyms, detect the request's language (Japanese or English), and
invoke exactly the matched module's handler function; ask a clarification
question on an ambiguous match and reject with the unmatched method name
on no match. Propagate the detected language to every downstream path
(module handler, DES-AIMS-002 validation failure, clarification question,
rejection message) so that every user-facing sentence it produces or
forwards is rendered wholly in that language, limited to the permitted
technical tokens (method names, unit symbols, numeric values) per
REQ-AIMS-001's acceptance.
Interfaces: dispatch(request_text, language) -> DispatchResult
{module, handler_result} | {clarification_question} | {rejected_method}.
All three outcome variants' user-facing text is rendered in `language`.
Constraints: Must invoke at most one module per request (REQ-AIMS-002
acceptance's "no other module" clause); must never mix Japanese and
English prose within one produced sentence (REQ-AIMS-001 acceptance).
Requirements: REQ-AIMS-001, REQ-AIMS-002
ADRs: ADR-0015
Depends-On: none

## DES-AIMS-002: Shared parameter & stability validator / 共通パラメータ・安定性検証
Responsibilities: Validate each module's resolved input parameters against
that module's documented numerical-stability and physical-definedness
constraints before any module performs a simulation step, and report the
violated parameter and constraint on failure.
Interfaces: validate_parameters(module_name, params) -> ValidationResult
{ok: true} | {ok: false, parameter, constraint}.
Constraints: Must run to completion (no partial simulation step) before any
module-specific state mutation (REQ-AIMS-003 acceptance).
Requirements: REQ-AIMS-003
ADRs: ADR-0016
Depends-On: DES-AIMS-001

## DES-AIMS-003: Run evidence recorder / 実行根拠記録
Responsibilities: Capture every module run's resolved input parameters
(including any random seed) and output summary as an in-memory structured
result with exactly three top-level keys (`metadata`, `parameters`,
`arrays`) per REQ-AIMS-004, and provide a JSON-safe persisted encoding of
that record together with a loader that reconstructs it.
Interfaces: record_run(module_name, params, result) -> RunRecord
{metadata: {module, unit_system, schema_version, seed}, parameters,
arrays: dict[str, numpy.ndarray]}. to_json(run_record) -> JsonSafeRecord
{metadata, parameters, arrays: dict[str, {dtype, shape, data}]} (one
explicit ndarray codec: dtype as a numpy dtype string, shape as a list of
ints, data as a nested JSON array in row-major order). from_json(
json_safe_record) -> RunRecord, reconstructing each `arrays` entry via
`numpy.array(data, dtype=dtype).reshape(shape)`.
Constraints: Re-running with identical explicit parameters (including seed)
must reproduce array-equal recorded numeric arrays via `numpy.array_equal`
(REQ-AIMS-004 acceptance); `from_json(to_json(record))`'s `arrays` must
compare array-equal to the original record's `arrays`.
Requirements: REQ-AIMS-004, REQ-AIMS-005
ADRs: ADR-0017
Depends-On: DES-AIMS-001

## DES-AIMS-010: Phase-field module / フェーズフィールドモジュール
Responsibilities: Integrate the Allen-Cahn or Cahn-Hilliard PDE on a
periodic finite-difference grid using the fixed potential f(c)=c^2*(1-c)^2,
the periodic five-point Laplacian, and the chemical potential
mu = f'(c) - kappa*L(c); compute and report each model's explicit
stability time-step bound; and report field snapshots at the requested
output interval.
Interfaces: run_phase_field(field0, model, dx, M, kappa, dt, steps,
output_every) -> PhaseFieldResult {snapshots, times, dt_bound}.
Constraints: Cahn-Hilliard mass conservation and Allen-Cahn discrete free
energy (dx^2-weighted, periodic forward-difference edges) monotonicity
must hold between recorded snapshots (REQ-AIMS-010 acceptance).
Requirements: REQ-AIMS-010
ADRs: ADR-0018
Depends-On: DES-AIMS-001, DES-AIMS-002, DES-AIMS-003

## DES-AIMS-020: Molecular dynamics module / 分子動力学モジュール
Responsibilities: Integrate Newton's equations of motion for a
Lennard-Jones particle system in a 2D periodic square box with the
velocity-Verlet algorithm, the minimum-image convention, and a
shifted-force potential, and report position, velocity, and total energy
at the requested output interval.
Interfaces: run_md(positions0, velocities0, lj_params, box_length, cutoff,
dt, steps, output_every) -> MdResult {snapshots, energies, times,
dt_bound}.
Constraints: Total energy relative drift must stay within the 1% tolerance
of REQ-AIMS-020's acceptance for a time step at or below the module's
reported stability limit (dt_bound = 0.005 * sigma * sqrt(mass/epsilon));
rejects cutoff > box_length / 2.
Requirements: REQ-AIMS-020
ADRs: ADR-0019
Depends-On: DES-AIMS-001, DES-AIMS-002, DES-AIMS-003

## DES-AIMS-030: Classical Monte Carlo module / 古典モンテカルロモジュール
Responsibilities: Run single-site Metropolis-criterion trial moves on a
periodic square nearest-neighbor Ising lattice of linear size L with
coupling J and temperature T (in units of J/kB), discard the configured
equilibration sweeps, and report the sweep-averaged energy per site and
absolute magnetization per site over the sampling sweeps.
Interfaces: run_monte_carlo(L, J, T, equilibration_sweeps,
sampling_sweeps, seed, initial_spins) -> MonteCarloResult {mean_energy,
mean_abs_magnetization, history}.
Constraints: Must discard the configured equilibration_sweeps before
computing the reported averages (REQ-AIMS-030 acceptance's magnetization
thresholds); reference fixture uses L=20, J=kB=1, seed=12345, an
all-spins-up initial configuration, 2000 equilibration sweeps, and 8000
sampling sweeps.
Requirements: REQ-AIMS-030
ADRs: ADR-0020
Depends-On: DES-AIMS-001, DES-AIMS-002, DES-AIMS-003

## DES-AIMS-040: Kinetic Monte Carlo module / 速度論的モンテカルロモジュール
Responsibilities: Execute the rejection-free (BKL) kinetic Monte Carlo
algorithm for a single tracer walker on an unwrapped 2D square lattice
with 4 equally rated hop directions of rate Gamma and jump length a,
deriving exactly 200 independent realization seeds as
base_seed + realization_index (0..199), and report each realization's
unwrapped displacement at each requested output time, defined as the
displacement after the last event at or before that time, never advancing
past total_time.
Interfaces: run_kmc(gamma, a, total_time, output_times, base_seed) ->
KmcResult {displacements, times, realization_seeds}.
Constraints: Simulated time must advance strictly monotonically by the
drawn exponential waiting time at every step and never exceed total_time
(REQ-AIMS-040 acceptance's diffusion-coefficient check depends on this);
rejects a requested output time outside (0, total_time].
Requirements: REQ-AIMS-040
ADRs: ADR-0021
Depends-On: DES-AIMS-001, DES-AIMS-002, DES-AIMS-003

## DES-AIMS-050: Crystal plasticity module / 結晶塑性モジュール
Responsibilities: Validate the crystal orientation matrix Q (orthogonality,
determinant) and stress tensor (symmetry, non-zero norm), rotate the fixed
Table CP-12 slip-system family from the crystal frame to the sample frame
via Q, compute the signed Schmid factor and resolved shear stress for every
slip system under an applied stress tensor, report active systems, and
compute the plastic shear-strain-rate on active systems via the signed
power-law rate-sensitivity relation.
Interfaces: run_crystal_plasticity(orientation_q, stress_tensor, crss,
gamma_dot_0, n) -> CrystalPlasticityResult {schmid_factors,
resolved_shear_stresses, active_systems, shear_strain_rates}.
Constraints: Single material point only; no finite-element mesh coupling
or inter-grain stress redistribution (REQ-AIMS-050 constraint); rejects a
non-orthogonal/non-unit-determinant Q or non-symmetric stress tensor before
any Schmid-factor computation.
Requirements: REQ-AIMS-050
ADRs: ADR-0022
Depends-On: DES-AIMS-001, DES-AIMS-002, DES-AIMS-003

## DES-AIMS-060: Simplified finite-element module / 簡易有限要素法モジュール
Responsibilities: Assemble a linear finite-element stiffness system for a
1D line mesh restricted to steady-state heat conduction, or a 2D
structured quadrilateral mesh under steady-state heat conduction or
plane-strain linear elasticity; apply the essential (Dirichlet) boundary
conditions by partitioning degrees of freedom into prescribed and free
sets, setting u[prescribed_dofs] := prescribed_values, forming the
adjusted load vector f_adjusted[free_dofs] := f[free_dofs] -
K[free_dofs, prescribed_dofs] @ prescribed_values, and forming the
constrained stiffness matrix as the free-free submatrix
constrained_stiffness := K[free_dofs, free_dofs] (K is the raw assembled
stiffness matrix); after assembly and before invoking the solver, verify
that the free-degree-of-freedom set is non-empty and that
constrained_stiffness's reciprocal condition number, computed as
1 / numpy.linalg.cond(constrained_stiffness, 2) (the 2-norm condition
number), is at or above 1e-10, rejecting an empty free-degree-of-freedom
set or a singular/underconstrained constrained_stiffness with the
violated boundary/constraint condition (the raw unconstrained stiffness
matrix K, expected to be singular prior to constraint application, is
never tested for this condition); only then solve K[free_dofs, free_dofs]
@ u[free_dofs] = f_adjusted[free_dofs] and report the nodal field solution
(prescribed degrees of freedom are reported directly as
u[prescribed_dofs] := prescribed_values).
Rejects plane-strain elasticity requested on a 1D mesh before assembly.
Interfaces: run_fem(mesh, material_properties, boundary_conditions,
physics) -> FemResult {nodal_values, mesh}; assemble_and_check(mesh,
material_properties, boundary_conditions, physics) -> AssemblyResult
{ok: true, constrained_stiffness, free_dofs, rhs_adjusted} | {ok: false,
violated_condition}.
Constraints: Limited to structured 1D/2D meshes and linear elements; no
adaptive meshing or nonlinear material laws (REQ-AIMS-060 scope); 1D
meshes support heat conduction only, never plane-strain elasticity;
temperatures are recorded in Kelvin only (REQ-AIMS-005); the solver is
never invoked on a system assemble_and_check reports as not ok; the
reciprocal-condition-number tolerance is fixed at 1e-10, computed on the
free-free submatrix constrained_stiffness := K[free_dofs, free_dofs] (not
the raw assembled K); an empty free_dofs set is itself a rejected
(violated_condition) case.
Requirements: REQ-AIMS-060
ADRs: ADR-0023
Depends-On: DES-AIMS-001, DES-AIMS-002, DES-AIMS-003

## DES-AIMS-070: Simplified CALPHAD module / 簡易CALPHADモジュール
Responsibilities: Compute the symmetric regular-solution molar Gibbs
free-energy-of-mixing curve across a composition grid at a requested
temperature below the phase's consolute temperature, and determine the two
nontrivial binodal compositions by bracketed root-finding on the
regular-solution coexistence equation, excluding the trivial x=0.5 root
and the singular x=0/x=1 endpoints.
Interfaces: run_calphad(omega, temperature, composition_grid) ->
CalphadResult {x_alpha, x_beta, free_energy_curve}.
Constraints: Built-in symmetric regular-solution model only; no
asymmetric/sub-regular (Redlich-Kister) models, multicomponent systems, or
TDB thermodynamic-database file parsing (REQ-AIMS-070 scope); rejects
Omega <= 0, T <= 0, or T >= T_c before root-finding.
Requirements: REQ-AIMS-070
ADRs: ADR-0024
Depends-On: DES-AIMS-001, DES-AIMS-002, DES-AIMS-003

## Traceability summary / 追跡可能性一覧

| Design component | Requirement(s) | ADR |
| --- | --- | --- |
| DES-AIMS-001 | REQ-AIMS-001, REQ-AIMS-002 | ADR-0015 |
| DES-AIMS-002 | REQ-AIMS-003 | ADR-0016 |
| DES-AIMS-003 | REQ-AIMS-004, REQ-AIMS-005 | ADR-0017 |
| DES-AIMS-010 | REQ-AIMS-010 | ADR-0018 |
| DES-AIMS-020 | REQ-AIMS-020 | ADR-0019 |
| DES-AIMS-030 | REQ-AIMS-030 | ADR-0020 |
| DES-AIMS-040 | REQ-AIMS-040 | ADR-0021 |
| DES-AIMS-050 | REQ-AIMS-050 | ADR-0022 |
| DES-AIMS-060 | REQ-AIMS-060 | ADR-0023 |
| DES-AIMS-070 | REQ-AIMS-070 | ADR-0024 |
| DES-AIMS-080 | REQ-AIMS-080 | ADR-0113 |

Every DES-AIMS-010 through DES-AIMS-070 module depends on DES-AIMS-001
(dispatch), DES-AIMS-002 (validation), and DES-AIMS-003 (evidence schema
and unit convention); this table records the full requirement/design/ADR
coverage so a change to any one artifact's linked IDs is immediately
visible as a mismatch.

## DES-AIMS-080: npm skill-package completeness guard / npmスキル同梱完全性ガード
Responsibilities: Preserve parity between the npm bootstrap package's
shipped ai-materials-scientist skill payload and its importable Python
sources by asserting that `package.json` `files` contains both exact
entries `.github/skills/ai-materials-scientist` and
`src/ai_materials_scientist/**/*.py`, and by proving with an `npm pack
--dry-run --json` listing that the packed artifact contains
`.github/skills/ai-materials-scientist/SKILL.md`,
`.github/skills/ai-materials-scientist/manifest.json`, and every
current repository file matching `src/ai_materials_scientist/**/*.py`.
Interfaces: The test reuses `src/ai_scientist/npm_packaging.py`'s
existing generic helpers — `load_package_files(package_json_path: str |
Path = "package.json") -> list[str]`, `load_npm_pack_dry_run_paths(
project_root: str | Path = ".") -> set[str]` (wraps `npm pack --dry-run
--json`), and `iter_skill_python_globs(package_files: Sequence[str]) ->
dict[str, str]` (maps each shipped `.github/skills/<slug>` entry to its
expected `src/<package>/**/*.py` glob) — rather than defining new
duplicate helper functions. The test-local assertion function composes
these in three steps: (1) `load_package_files()` contains both the
exact skill entry `.github/skills/ai-materials-scientist` and the exact
glob entry `src/ai_materials_scientist/**/*.py`; (2)
`iter_skill_python_globs(load_package_files())["\
.github/skills/ai-materials-scientist"] ==
"src/ai_materials_scientist/**/*.py"`; and (3) every current repository
file matching `src/ai_materials_scientist/**/*.py` (resolved via Python
glob expansion, not the literal glob string) is a member of
`load_npm_pack_dry_run_paths()`, together with
`.github/skills/ai-materials-scientist/SKILL.md` and
`.github/skills/ai-materials-scientist/manifest.json`.
Constraints: The authoritative packaged-artifact proof is the dry-run
pack listing, not only static inspection of `package.json`. This guard
covers npm distribution completeness only; Python package discovery
continues to rely on setuptools auto-discovery from `pyproject.toml`
`where = ["src"]` (unchanged by this design), so no explicit static
Python package list is required unless that project configuration
changes in the future. New tests must import and reuse
`src/ai_scientist/npm_packaging.py`'s helpers rather than redefining
equivalent logic.
Requirements: REQ-AIMS-080
ADRs: ADR-0113
Depends-On: DES-AISCI-020
