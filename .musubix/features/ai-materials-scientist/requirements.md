---
schemaVersion: 1
feature: ai-materials-scientist
---
# Requirements / 要求

Feature: A new Copilot Agent Skill, `ai-materials-scientist`, that hosts
domain-specific computational-materials-science modules behind a single
skill boundary (MECE scale hierarchy: electronic / atomistic / mesoscale /
continuum), analogous to how `ai-data-scientist` hosts generic data-analysis
modules and `ai-scientist` hosts the generic research-process phases. This
first increment adds seven modules selected by MECE scale-hierarchy survey
of computational materials science methods (DFT excluded as infeasible for
a lightweight numpy/scipy-only implementation): phase-field, molecular
dynamics, classical Monte Carlo, kinetic Monte Carlo, single-point crystal
plasticity, a simplified finite-element solver, and a simplified CALPHAD-
style binary phase diagram calculator. `ai-scientist`'s `experimental-design`
and `data-analysis` phases may delegate to this skill as a
`skillDependency`, mirroring the existing `tech-writer` / `japanese-prose` /
`presentation-planner` delegation pattern.

All modules are pure Python/numpy/scipy implementations (no external solver
binaries, no network calls); each module validates its own input
parameters, per its own stated domain, and rejects a run that would be
numerically unstable or physically undefined before performing any
simulation step or state mutation.

## REQ-AIMS-001: Bilingual instruction support / 日英両対応の指示理解
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall accept user requests and produce user-facing messages in whichever of Japanese or English the user's request used, for every module in this skill.
Acceptance: A fixed Japanese-language fixture request ("フェーズフィールド法でシミュレーションしたい") produces a response whose every sentence is Japanese prose (English technical tokens limited to method names, unit symbols, and numeric values are permitted); the English-equivalent fixture request ("I want to run a phase-field simulation") produces an all-English response; neither response contains a sentence mixing Japanese and English prose.

## REQ-AIMS-002: Module routing by request content / 要求内容によるモジュール振り分け
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user's request text contains one of the module manifest's registered name/synonym strings for a supported method, the system shall dispatch the request to exactly that method's module handler and execute no other module, where the supported methods are phase-field, molecular dynamics, classical Monte Carlo, kinetic Monte Carlo, crystal plasticity, finite element, and CALPHAD/phase-diagram, each with both an English and a Japanese registered name/synonym list in the manifest.
Acceptance: For each of the 7 methods, a fixture request using its registered English name and a separate fixture request using its registered Japanese name each dispatch to exactly that method's handler and no other; a fixture request containing two different methods' registered names yields a clarification question listing both candidates with no module invoked; a fixture request containing none of the registered names yields a rejection message with no module invoked.

## REQ-AIMS-003: Simulation run parameter validation / シミュレーション実行パラメータ検証
Priority: must
Type: functional
Pattern: unwanted-behavior
Statement: If a requested simulation's input parameters fail that module's own documented stability or physical-definedness domain, then the system shall reject the run and report which parameter violated which named constraint, before performing any simulation step or state mutation.
Acceptance: A phase-field request whose time step exceeds the explicit stability bound reported by DES-AIMS-010 for its grid spacing, mobility, and gradient-energy coefficient is rejected with a message naming the time-step parameter and the violated inequality; no field array is modified and no snapshot is recorded. The same pattern (reject before mutation, name the parameter and constraint) applies to every module's documented domain, including: non-finite (NaN/Inf) values in any numeric input array; a negative or zero step count; a non-positive output interval; and each module-specific domain listed in its own requirement below.
Constraints: This requirement's "stability or physical-definedness domain" is defined per module by REQ-AIMS-010/020/030/040/050/060/070; it does not itself define a single universal numerical-stability test applicable across all seven modules.

## REQ-AIMS-004: Reproducible run evidence / 再現可能な実行根拠
Priority: must
Type: functional
Pattern: event-driven
Statement: When a simulation run completes, the system shall record a result with exactly three top-level keys: `metadata` (a JSON-safe dict containing at least `module`, `unit_system`, `schema_version`, and `seed` set to the integer seed or to `null` when the module is deterministic), `parameters` (a JSON-safe dict of the resolved input parameters), and `arrays` (a dict of named `numpy.ndarray` values, each `float64` unless that module's own requirement states an integer array), including an explicit random seed in `metadata.seed` for any module whose governing algorithm is stochastic.
Acceptance: For a stochastic module (classical Monte Carlo or kinetic Monte Carlo) given an explicit seed, two runs with identical `parameters` and the same `metadata.seed` produce `arrays` entries that compare equal element-by-element with `numpy.array_equal`, in the same process/runtime; for a deterministic module (phase-field, molecular dynamics, crystal plasticity, finite element, CALPHAD), two runs with identical `parameters` produce `arrays` entries that compare equal with `numpy.array_equal` without needing a seed, and `metadata.seed` is `null`. Cross-platform or cross-runtime bit-for-bit reproducibility is explicitly out of scope.

## REQ-AIMS-005: Shared unit and dimension convention / 共通の単位・次元規約
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall interpret and report every physical quantity in a named unit system recorded alongside the result: SI units (kelvin for temperature, mole fraction in the closed interval zero to one for composition, seconds for time, pascals for stress, and inverse seconds for shear strain rate) for the finite-element, CALPHAD, and crystal-plasticity modules, and an explicitly named reduced/non-dimensional unit system (Lennard-Jones reduced units for molecular dynamics; J equals kB equals 1 for classical Monte Carlo and kinetic Monte Carlo's rate units; dimensionless order-parameter and grid units for phase-field) for the remaining modules.
Acceptance: Every module's recorded run evidence (REQ-AIMS-004) includes `metadata.unit_system` naming one of the conventions above; no module accepts or silently reinterprets a quantity under an unnamed or mixed unit convention.

## REQ-AIMS-010: Phase-field microstructure evolution / フェーズフィールド法による組織形成の時間発展
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests a phase-field simulation with an initial order-parameter field on a periodic 2D grid and a model choice of Allen-Cahn or Cahn-Hilliard and a grid spacing and a mobility and a gradient-energy coefficient and a time step and a step count, the system shall integrate the selected governing PDE using the fixed bulk free-energy density f(c) = c^2 * (1-c)^2 on c constrained to [0,1], the periodic five-point discrete Laplacian L(c)[i,j] = (c[i+1,j] + c[i-1,j] + c[i,j+1] + c[i,j-1] - 4*c[i,j]) / dx^2 with maximum-magnitude eigenvalue lambda_max = 8 / dx^2, and the chemical potential mu = f'(c) - kappa * L(c), stepping forward-Euler as c_new = c - dt * M * mu for Allen-Cahn and c_new = c + dt * M * L(mu) for Cahn-Hilliard, and report the field at each requested output interval (including the initial field as the step-zero snapshot) together with the model-specific explicit stability time-step bound it computed from the supplied grid spacing, mobility, and gradient-energy coefficient: dt_bound = 2 / (M * (2 + kappa * lambda_max)) for Allen-Cahn, and dt_bound = 2 / (M * lambda_max * (2 + kappa * lambda_max)) for Cahn-Hilliard.
Acceptance: On a reference 64x64 periodic grid with kappa = 1.0, M = 1.0, and dx = 1.0 (so lambda_max = 8.0, dt_bound = 0.2 for Allen-Cahn, and dt_bound = 0.025 for Cahn-Hilliard), using a deterministic initial field c(i,j) = 0.5 + 0.01 * cos(2*pi*i/64) * cos(2*pi*j/64) for grid indices i,j in [0,64), run for 200 steps with output every 20 steps with the requested time step at or below the module's own reported dt_bound: a Cahn-Hilliard run's total field mass (grid sum of the field, scaled by dx^2) satisfies abs(mass_final - mass_initial) <= 1e-10 * max(1.0, abs(mass_initial)) between the step-zero snapshot and the last recorded snapshot; an Allen-Cahn run's total discrete free energy F = dx^2 * sum_over_cells(f(c[i,j]) + (kappa/2) * (((c[i+1,j]-c[i,j])/dx)^2 + ((c[i,j+1]-c[i,j])/dx)^2)), using periodic forward differences for the edge-gradient terms, is non-increasing (each recorded snapshot's F is less than or equal to the previous recorded snapshot's F plus 1e-10 absolute tolerance) between every pair of consecutive recorded snapshots including the step-zero snapshot.
Constraints: A request with M <= 0, kappa < 0, dx <= 0, a time step at or below 0, or a step count at or below 0 is rejected under REQ-AIMS-003 before any integration step.

## REQ-AIMS-020: Molecular dynamics trajectory integration / 分子動力学による軌道積分
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests a molecular dynamics simulation with initial particle positions and velocities and Lennard-Jones parameters epsilon and sigma and particle mass and a cutoff radius and a periodic square box in 2D and a time step and a step count, the system shall integrate Newton's equations of motion in Lennard-Jones reduced units with the velocity-Verlet algorithm using a shifted-force Lennard-Jones potential truncated at the cutoff radius and the minimum-image convention for periodic pairwise distances, rejecting a cutoff radius greater than half the box side length, and report position, velocity, and total energy at each requested output interval together with the explicit stability time-step bound it computed as the conservative heuristic dt_bound = 0.005 * sigma * sqrt(mass / epsilon).
Acceptance: On a reference fixture of 4 particles placed at the corners of a 2D square of reduced side length 1.5 sigma inside a periodic square box of reduced side length 6.0 sigma, with epsilon = 1.0, sigma = 1.0, mass = 1.0, cutoff = 2.5 sigma (at or below half the box side length of 3.0 sigma), zero initial velocity, and a time step at or below the module's own reported stability bound (dt_bound = 0.005 for this fixture), run for 1000 steps with output every 10 steps: the maximum absolute relative deviation of total energy (kinetic plus shifted-potential) from its initial value, taken over every recorded snapshot (not only the first and last), is less than or equal to 0.01 (1%). A request with non-finite positions/velocities, non-positive mass, non-positive epsilon or sigma, any pairwise particle separation below 0.8 sigma, a cutoff radius greater than half the box side length, or a non-positive box size is rejected under REQ-AIMS-003 before any integration step.

## REQ-AIMS-030: Classical Monte Carlo lattice sampling / 古典モンテカルロ格子サンプリング
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests a classical Monte Carlo simulation with a periodic square lattice of linear size L and a nearest-neighbor Ising interaction with coupling J and a temperature in units of J over kB and a step count measured in full-lattice sweeps and an explicit random seed, the system shall perform single-site spin-flip trial moves accepted or rejected by the Metropolis criterion and report the sweep-averaged energy per site and absolute magnetization per site computed over the sweeps after a specified equilibration count.
Acceptance: On a reference L = 20 periodic square lattice with J = 1 (J > 0), kB = 1, random seed 12345, an all-spins-up (+1) initial configuration, 2000 equilibration sweeps, and 8000 sampling sweeps: a run at reduced temperature T = 1.5 (T > 0, below the Onsager critical temperature T_c = 2.269185 J/kB) yields a sampled mean absolute magnetization per site greater than 0.8; a run at T = 3.5 (above T_c, same seed and initial configuration) yields a sampled mean absolute magnetization per site less than 0.2.
Constraints: A request with L at or below 0, J at or below 0, T at or below 0, an equilibration-sweep count below 0, or a sampling-sweep count at or below 0 is rejected under REQ-AIMS-003 before any spin-flip trial move.

## REQ-AIMS-040: Kinetic Monte Carlo event-driven evolution / 速度論的モンテカルロによるイベント駆動時間発展
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests a kinetic Monte Carlo simulation of a single tracer walker on an unwrapped (non-periodic coordinate tracking) 2D square nearest-neighbor lattice with 4 equally rated hop directions of per-directed-hop jump rate Gamma and a jump length a and a total simulated time and a base random seed, the system shall derive 200 independent realization seeds as base_seed + realization_index (realization_index from 0 to 199) and, for each realization, select and execute hops by the rejection-free (BKL) algorithm, drawing an exponential waiting time with rate equal to the sum of available event rates (4 * Gamma) at each step, and report the tracer's unwrapped displacement at each requested output time, defined as its displacement after the last event at or before that time.
Acceptance: With Gamma = 1.0, a = 1.0, a base random seed of 7, and a requested output time of t = 100, averaged over the 200 realization seeds derived as above (7 + 0 through 7 + 199): the sample mean of the squared unwrapped displacement magnitude at t = 100, divided by (4 * Gamma * a^2 * t), is between 0.9 and 1.1 (i.e. within 10% of the theoretical value of 1.0 for the nearest-neighbor directed-hop-rate convention D = Gamma * a^2 per Cartesian dimension, mean-squared displacement = 2 * d_dimensions * D * t = 4 * Gamma * a^2 * t for d_dimensions = 2).
Constraints: A request with Gamma at or below 0, a at or below 0, a total simulated time at or below 0, or a requested output time outside the half-open interval (0, total_simulated_time] is rejected under REQ-AIMS-003 before any hop event is drawn; a realization's rejection-free sampling never advances past the requested total simulated time.

## REQ-AIMS-050: Single-point crystal plasticity slip activation / 単一材料点の結晶塑性すべり系活性化
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests a crystal plasticity evaluation with a crystal orientation represented as a proper orthogonal 3x3 matrix Q mapping crystal-frame vectors to the sample frame and the FCC {111}<110> 12-member slip-system family defined by the exact ordered list of crystal-frame slip-plane-normal and slip-direction pairs in the fixed Table CP-12 list (given in this requirement's Constraints) and an applied Cauchy stress tensor expressed in the sample frame and a critical resolved shear stress and a reference shear rate gamma_dot_0 and a rate-sensitivity exponent n, the system shall reject under REQ-AIMS-003 an orientation matrix Q that is not orthogonal with determinant +1, rotate each system's crystal-frame plane normal and slip direction into the sample frame as n_sample = Q * n_crystal and d_sample = Q * d_crystal, normalize each rotated system's plane normal and slip direction to unit vectors, compute each system's signed Schmid factor as the double contraction of the normalized Schmid tensor (normalized sample-frame plane normal outer product normalized sample-frame slip direction) with the sample-frame stress tensor divided by the stress tensor's Frobenius norm (rejecting a zero-norm stress tensor under REQ-AIMS-003), compute each system's signed resolved shear stress tau as the Schmid factor times the stress tensor's Frobenius norm, report as active every system whose absolute resolved shear stress is at or above the critical resolved shear stress, set the plastic shear-strain-rate on each active system to gamma_dot_0 * sign(tau) * abs(tau / critical_resolved_shear_stress)^n, and set it to exactly 0.0 on every inactive system.

Acceptance: For an FCC single crystal with orientation Q = identity (crystal frame aligned with sample frame) loaded in uniaxial tension along [100] with applied stress tensor sigma_hat * diag(1,0,0) (sigma_hat > 0), a critical resolved shear stress set to 0.3 * sigma_hat, gamma_dot_0 = 0.001, and n = 20, applying Table CP-12's fixed order: systems 1, 4, 7, and 10 have signed Schmid factor exactly 0.0 (within 1e-9 absolute error) and are reported inactive with plastic shear-strain-rate exactly 0.0; systems 2, 3, 5, 6, 8, and 9 have signed Schmid factor +0.408248 (within 1% relative error of +1/sqrt(6)), are reported active, and have plastic shear-strain-rate +0.001 * (0.408248 / 0.3)^20 (approximately +0.4743, within 1% relative error); systems 11 and 12 have signed Schmid factor -0.408248 (within 1% relative error of -1/sqrt(6)), are reported active, and have plastic shear-strain-rate -0.001 * (0.408248 / 0.3)^20 (approximately -0.4743, within 1% relative error).
Constraints: This module evaluates a single material point only; it does not perform finite-element mesh coupling, spatial stress redistribution between grains, multiple integration points, or polycrystal homogenization. A request is rejected under REQ-AIMS-003 before any Schmid-factor computation if any of the following hold: the orientation Q is not a finite real 3x3 array; the maximum absolute entry of (Q^T * Q - I) exceeds 1e-6; abs(det(Q) - 1) exceeds 1e-6; the stress tensor is not a finite real symmetric (within 1e-6 absolute entrywise tolerance) 3x3 array; the stress tensor's Frobenius norm is below 1e-12; the critical resolved shear stress is at or below 0; gamma_dot_0 is at or below 0; or n is at or below 0. Table CP-12 (plane normal; slip direction) in fixed order: 1:(1,1,1);(0,1,-1) 2:(1,1,1);(1,0,-1) 3:(1,1,1);(1,-1,0) 4:(1,1,-1);(0,1,1) 5:(1,1,-1);(1,0,1) 6:(1,1,-1);(1,-1,0) 7:(1,-1,1);(0,1,1) 8:(1,-1,1);(1,0,-1) 9:(1,-1,1);(1,1,0) 10:(-1,1,1);(0,1,-1) 11:(-1,1,1);(1,0,1) 12:(-1,1,1);(1,1,0)

## REQ-AIMS-060: Simplified finite-element field solver / 簡易有限要素法による場の求解
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests a finite-element simulation with a 1D line mesh restricted to steady-state heat conduction physics or a 2D structured rectangular Cartesian mesh of linear (2-node line or 4-node quadrilateral) elements with a choice of steady-state heat conduction or plane-strain linear-elasticity physics and material properties and boundary conditions, the system shall assemble the corresponding linear finite-element stiffness system and solve it for the nodal field (temperature or displacement), rejecting an unstructured mesh, a higher-order element, a nonlinear material law, plane-strain linear-elasticity requested on a 1D line mesh, or a singular/underconstrained assembled system before attempting a solve.
Acceptance: On a reference 1D line mesh of 11 equally spaced nodes over a length of 1.0 m with uniform thermal conductivity, fixed temperature 273.15 K at the left end and 373.15 K at the right end, and no internal heat source, the solved nodal temperature profile matches the linear analytical solution T(x) = 273.15 + 100 * x (kelvin) to within 1e-6 absolute error (kelvin) at every node.
Constraints: Supports only 1D line and 2D structured Cartesian meshes of the named linear elements; unstructured meshes, higher-order elements, nonlinear materials, contact, dynamics, and adaptive remeshing are unsupported and rejected. A request with non-positive thermal conductivity, a Young's modulus at or below 0, or a Poisson's ratio outside the open interval (-1, 0.5) is rejected under REQ-AIMS-003 before assembly.

## REQ-AIMS-070: Simplified binary CALPHAD phase diagram / 簡易2元系CALPHAD状態図計算
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests a binary phase diagram calculation with an explicit symmetric regular-solution interaction parameter Omega for a single solution phase and an explicit temperature below that phase's consolute temperature T_c equals Omega over (2 * R), the system shall compute that phase's molar Gibbs free energy of mixing curve G_mix(x) = R * T * (x * ln(x) + (1-x) * ln(1-x)) + Omega * x * (1-x) across a composition grid and determine the two nontrivial equilibrium (binodal) compositions, bracketed respectively in the open interval (0, 0.5) and (0.5, 1) and excluding the trivial root x = 0.5, by numerically solving the symmetric regular-solution coexistence condition ln(x / (1-x)) + (Omega / (R * T)) * (1 - 2*x) = 0 with an independent bracketed root-finder.
Acceptance: For Omega = 10000 J/mol, R = 8.314 J/(mol K), and T = 400 K (below T_c = Omega / (2R) ≈ 601.4 K), the two computed binodal compositions x_alpha (bracketed in (0, 0.5)) and x_beta (bracketed in (0.5, 1), satisfying x_beta = 1 - x_alpha) match the reference root-finder solution of the coexistence equation (approximately 0.0701 and 0.9299) to within 1e-4 absolute error in mole fraction.
Constraints: Supports only a single binary symmetric regular-solution phase model with explicitly supplied Omega and T; does not support asymmetric/sub-regular (Redlich-Kister) models, multicomponent systems, multiphase equilibrium between more than one solution phase, or any TDB thermodynamic-database file parsing. A request with Omega <= 0, T <= 0 K, or T >= T_c (Omega / (2R)) is rejected under REQ-AIMS-003 before any root-finding attempt; the root-finder brackets exclude the singular composition endpoints x = 0 and x = 1.

## REQ-AIMS-080: npm package ships ai-materials-scientist implementation sources / npmパッケージにai-materials-scientist実装ソースを同梱
Priority: must
Type: non-functional
Pattern: ubiquitous
Statement: The repository's npm bootstrap package shall ship the ai-materials-scientist skill payload (`.github/skills/ai-materials-scientist/SKILL.md` and `.github/skills/ai-materials-scientist/manifest.json`, where present) together with a `package.json` `files` entry `src/ai_materials_scientist/**/*.py` whose effect is that every current repository file matching that glob is included in the packed artifact.
Acceptance: An automated test loads `package.json`, asserts its `files` array contains both `.github/skills/ai-materials-scientist` and `src/ai_materials_scientist/**/*.py`, and asserts an `npm pack --dry-run --json` file listing includes `.github/skills/ai-materials-scientist/SKILL.md` and every current repository file matching `src/ai_materials_scientist/**/*.py`.
