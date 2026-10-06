---
schemaVersion: 1
feature: ai-structural-biology-scientist
---
# Design / 設計

Architecture blueprint for the new `ai-structural-biology-scientist`
Copilot Agent Skill. Mirrors the static manifest + single-dispatch +
shared-validation + shared-evidence pattern used by
`ai-chemistry-scientist`: a single skill entrypoint loads a static JSON
manifest mapping a method name to one handler wrapper, classifies a
bilingual request, and dispatches to exactly one structural-biology
module per request. Every module is a pure Python/numpy implementation
with no network calls, no external structural-biology libraries such as
Biopython or PyMOL, and no real PDB/mmCIF parsing beyond simple inline
coordinate lists supplied by the caller.

## DES-ASTRUCT-001: Method manifest & request dispatcher / 手法マニフェストと要求振り分け
Responsibilities: Load the static method-name-to-module manifest
(`.github/skills/ai-structural-biology-scientist/manifest.json`; each
entry has `modulePath`, `functionName`, and bilingual `names.en` /
`names.ja` lists, identical in shape to `ai-chemistry-scientist`'s
manifest), classify an incoming bilingual user request against the 5
supported method names/synonyms, detect the request's language
(Japanese or English), and on exactly one match resolve
`modulePath`/`functionName` to that module's handler wrapper function and
invoke it with `(request_text, language)`; ask a clarification question
on an ambiguous (multi-method) match and reject with no module invoked
on no match. Propagate the detected language to every downstream path
(module handler, DES-ASTRUCT-002 validation failure, clarification
question, rejection message) so that every user-facing sentence it
produces or forwards is rendered wholly in that language, limited to the
permitted technical tokens (method names, unit symbols, numeric values)
per REQ-ASTRUCT-001's acceptance. The 5 supported methods are
`secondary-structure-heuristic`, `hydrophobicity-burial-heuristic`,
`protein-protein-docking-score`, `structural-similarity-rmsd`, and
`residue-contact-map`. Every module's handler wrapper (one per method,
e.g. `handle_secondary_structure(request_text, language) ->
ModuleOutcome`) is responsible for: (1) extracting its module's
structured `params` from `request_text` (accepting them either as an
already-structured keyword-argument dict from a calling context or as a
single embedded JSON object literal within free text, exactly like the
chemistry template); (2) calling DES-ASTRUCT-002's
`validate_parameters` on the extracted `params` before any module
computation; (3) calling its own `run_*` function
(`run_secondary_structure`, `run_hydrophobicity`,
`run_protein_docking_score`, `run_structural_similarity`,
`run_contact_map`) with the extracted and already-validated `params`;
(4) for DES-ASTRUCT-010's and DES-ASTRUCT-030's raw results only,
substituting the raw result's `limitation_label_key` with the matching
`language`-specific fixed limitation text from that module's own section
below, producing a final `result` whose `limitation_label` field is
already localized prose; and (5) wrapping that (possibly
label-substituted) raw `run_*` result via DES-ASTRUCT-003's
`record_run` into a `RunRecord`.
Interfaces: `dispatch(request_text, language=None, manifest_path=None) ->
DispatchResult` where `DispatchResult` is one of
`{outcome: "dispatch", module, language, handler_result}`,
`{outcome: "clarification", candidates, language, clarification_question}`,
or `{outcome: "rejected", language, rejected_method}`. `handler_result`
is always a `ModuleOutcome`: either `{ok: true, run_record}` (a
DES-ASTRUCT-003 `RunRecord`) on success, or
`{ok: false, parameter, constraint, language}` on validation failure —
never a bare raw `run_*` result. `constraint` is the fixed,
language-invariant diagnostic string defined by the violated
requirement's acceptance or constraints (for example "must be a positive
odd integer", "must be > 0", or "must be a finite numeric 3-element
sequence"), identical regardless of `language`; only the surrounding
user-facing sentence a caller builds around `parameter` / `constraint`
is rendered in `language`. Reuse
`ai_data_scientist.language_router.detect_language` for language
detection, consistent with sibling skills.
Constraints: Must invoke at most one module per request
(REQ-ASTRUCT-002 acceptance's "no module invocation" clauses); must
never mix Japanese and English prose within one produced sentence
(REQ-ASTRUCT-001 acceptance); the manifest is a static, checked-in JSON
file, not a runtime-discovered plugin registry.
Requirements: REQ-ASTRUCT-001, REQ-ASTRUCT-002
ADRs: ADR-0041
Depends-On: none

## DES-ASTRUCT-002: Shared parameter / validity validator / 共通パラメータ・妥当性検証
Responsibilities: Validate each module's resolved input parameters
against that module's documented biochemical-validity,
geometric-definedness, or numerical-adequacy domain before any module
performs a lookup, averaging, scoring, superposition, or contact
calculation, and report the violated parameter and constraint on
failure. Provide a shared registry with one atomic validator function per
module; unlike `ai-chemistry-scientist`, no structural-biology module in
this increment uses per-item batch validation, so the shared API surface
is exactly `register_validator` plus `validate_parameters`.
Interfaces: `register_validator(module_name, validator) -> None`, where
each module registers its own validator at import time, and
`validate_parameters(module_name, params) -> ValidationResult`
`{ok: true}` | `{ok: false, parameter, constraint}`. Validators cover:
non-empty uppercase protein-sequence checks over the alphabet
`ACDEFGHIKLMNPQRSTVWY` (rejecting lowercase, empty, and out-of-alphabet
sequences) for DES-ASTRUCT-010/020; `window_size`
and `burial_threshold` domain checks for DES-ASTRUCT-020; partner record
shape plus finite non-negative integer counts and finite
`interface_area_A2 > 0` for DES-ASTRUCT-030; equal-length `N >= 3`
coordinate lists, each coordinate a `list` or `tuple` of exactly 3
finite real numbers (any other coordinate type, including numpy arrays,
is rejected), for DES-ASTRUCT-040; and coordinate-list cardinality
(same `list`/`tuple`-of-3-finite-numbers domain) plus
`distance_threshold_A` / `min_sequence_separation` domains for
DES-ASTRUCT-050.
Constraints: Validation must run to completion before any module-specific
state is produced for the whole run (REQ-ASTRUCT-003 acceptance); every
validation failure reports the parameter name and the fixed English
constraint string defined by the requirement, even when the surrounding
message is rendered in Japanese.
Requirements: REQ-ASTRUCT-003
ADRs: ADR-0042
Depends-On: DES-ASTRUCT-001

## DES-ASTRUCT-003: Reproducible run-evidence recorder / 再現可能な実行根拠記録
Responsibilities: Capture every module run's resolved input parameters
and output result as a JSON-safe structured record with exactly three
top-level keys (`metadata`, `parameters`, `result`) per REQ-ASTRUCT-004.
Called by each module's handler wrapper exactly once, immediately after
that module's own `run_*` function returns its raw result and only once
DES-ASTRUCT-002 validation has already succeeded — `record_run` is never
called on a validation-failure path. Unlike array-heavy simulation
evidence, every result in this skill is already JSON-safe (strings,
booleans, integers, floats, lists, and nested dicts/lists of these), so
no ndarray codec is needed.
Interfaces: `record_run(module_name, params, result, *, numpy_version) ->
RunRecord` `{metadata: {module, schema_version, numpy_version},
parameters, result}`.
Constraints: `metadata.numpy_version` is always included and always
matches the executing environment's `numpy.__version__`
(REQ-ASTRUCT-004); rerunning with identical `parameters` against the same
installed numpy version must reproduce a `result` that compares exactly
equal per REQ-ASTRUCT-004's tolerance rules; no random seed is ever
recorded because no module has a stochastic step.
Requirements: REQ-ASTRUCT-004
ADRs: ADR-0043
Depends-On: DES-ASTRUCT-001

Note on DES-ASTRUCT-010 through DES-ASTRUCT-050 below: each module's
`run_*(...)` function is the raw, unwrapped computation entry point. Its
DES-ASTRUCT-001 handler wrapper calls DES-ASTRUCT-002
`validate_parameters` before invocation, so every `run_*` function
receives only already-validated `params` and performs no parameter
revalidation of its own; none is called on a validation-failure path.
Every `run_*` function's return shape is exactly the `result` value
DES-ASTRUCT-003's `record_run` wraps into a `RunRecord`.

## DES-ASTRUCT-010: Secondary-structure heuristic module / 二次構造ヒューリスティックモジュール
Responsibilities: Receive the protein `sequence` already validated
atomically by its handler wrapper via `DES-ASTRUCT-002
.validate_parameters`, apply the fixed per-residue propensity table
verbatim
`A:(1.42,0.83,0.75) R:(0.98,0.93,1.09) N:(0.67,0.89,1.44) D:(1.01,0.54,1.45) C:(0.70,1.19,1.11) Q:(1.11,1.10,0.79) E:(1.51,0.37,1.12) G:(0.57,0.75,1.68) H:(1.00,0.87,1.13) I:(1.08,1.60,0.32) L:(1.21,1.30,0.49) K:(1.16,0.74,1.10) M:(1.45,1.05,0.50) F:(1.13,1.38,0.49) P:(0.57,0.55,1.88) S:(0.77,0.75,1.48) T:(0.83,1.19,0.98) W:(1.08,1.37,0.55) Y:(0.69,1.47,0.84) V:(1.06,1.70,0.41)`,
assign each residue exactly one class `H`, `E`, or `C` by selecting the
largest propensity and breaking any exact propensity tie by the fixed
preference order helix > sheet > coil, then compute
`secondary_structure`, `helix_fraction`, `sheet_fraction`, and
`coil_fraction`. Return a per-residue list in sequence order plus the
aggregate fields. Emit a raw `limitation_label_key` so the handler
wrapper can substitute the exact fixed bilingual limitation text before
recording evidence.
Interfaces: `run_secondary_structure(sequence) ->
SecondaryStructureResult {residues: list[{position, residue, class}],
secondary_structure, helix_fraction, sheet_fraction, coil_fraction,
limitation_label_key}`.
Constraints: Invalid sequence characters are rejected by the handler
wrapper before this function is ever called, naming the first invalid
character and its zero-based index per REQ-ASTRUCT-010; the fixed
`limitation_label_key` is
`"secondary_structure_heuristic_limitation"` (not yet localized — the
handler wrapper replaces it with `limitation_label` before
`record_run`); the same two-language text must also appear verbatim in
SKILL.md:
`secondary_structure_heuristic_limitation.en` = "Heuristic only: a fixed illustrative per-residue propensity lookup, not a validated secondary-structure predictor (no windowing, no real Chou-Fasman statistics).";
`secondary_structure_heuristic_limitation.ja` = "ヒューリスティックのみ：固定の説明用残基別 propensity lookup であり、検証済みの二次構造予測器ではない（windowing なし、実際の Chou-Fasman 統計なし）。"
Requirements: REQ-ASTRUCT-010
ADRs: ADR-0044
Depends-On: DES-ASTRUCT-001, DES-ASTRUCT-002, DES-ASTRUCT-003

## DES-ASTRUCT-020: Per-residue hydrophobicity / burial heuristic module / 残基ごとの疎水性・埋没度ヒューリスティックモジュール
Responsibilities: Receive `sequence`, `window_size`, and
`burial_threshold` already validated atomically by its handler wrapper
via `DES-ASTRUCT-002.validate_parameters`, look up each residue's exact
Kyte-Doolittle value from the fixed scale `A=1.8 R=-4.5 N=-3.5 D=-3.5
C=2.5 Q=-3.5 E=-3.5 G=-0.4 H=-3.2 I=4.5 L=3.8 K=-3.9 M=1.9 F=2.8
P=-1.6 S=-0.8 T=-0.7 W=-0.9 Y=-1.3 V=4.2`, compute the centered
sliding-window average over the in-bounds residues only, and assign
`label = "buried"` iff `window_average > burial_threshold` else
`"exposed"` for each residue.
Interfaces: `run_hydrophobicity(sequence, window_size=9,
burial_threshold=1.5) -> HydrophobicityResult {residues:
list[{position, residue, kd_value, window_average, label}]}`.
Constraints: `window_size` must already have been validated as a
positive odd integer and `burial_threshold` as a finite number before
this function is called; this module is a one-dimensional sequence
heuristic for relative burial tendency only, not a
solvent-accessible-surface or 3D packing calculation.
Requirements: REQ-ASTRUCT-020
ADRs: ADR-0045
Depends-On: DES-ASTRUCT-001, DES-ASTRUCT-002, DES-ASTRUCT-003

## DES-ASTRUCT-030: Protein-protein docking-score heuristic module / タンパク質間ドッキングスコア・ヒューリスティックモジュール
Responsibilities: Receive partner records `partner_a` and `partner_b`
of the form `{hydrophobic_count, charged_count}` and
`interface_area_A2` already validated atomically by its handler wrapper
via `DES-ASTRUCT-002.validate_parameters`, then compute the fixed
formulas verbatim:
`size_term = clip(1 - abs(interface_area_A2 - 800.0) / 800.0, 0, 1)`,
`hydrophobic_complementarity = min(A.hydrophobic_count, B.hydrophobic_count) / max(1, A.hydrophobic_count + B.hydrophobic_count)`,
`charge_complementarity = min(A.charged_count, B.charged_count) / max(1, A.charged_count + B.charged_count)`, and
`score = 0.5*size_term + 0.25*hydrophobic_complementarity + 0.25*charge_complementarity`.
Return those four scalar outputs and a raw `limitation_label_key` so the
handler wrapper can substitute the exact fixed bilingual limitation text
before recording evidence.
Interfaces: `run_protein_docking_score(partner_a, partner_b,
interface_area_A2) -> ProteinDockingScoreResult {size_term,
hydrophobic_complementarity, charge_complementarity, score,
limitation_label_key}` where `partner_a` / `partner_b` are
`{hydrophobic_count, charged_count}` records.
Constraints: Invalid partner counts or invalid `interface_area_A2` are
rejected by the handler wrapper before this function is ever called; the
fixed `limitation_label_key` is
`"protein_docking_score_heuristic_limitation"` (localized by the
handler wrapper before `record_run`); the same two-language text must
also appear verbatim in SKILL.md:
`protein_docking_score_heuristic_limitation.en` = "Heuristic only: a fixed-formula geometric/compositional complementarity score, not a physically accurate protein-protein docking simulation (no 3D structure, no energy function).";
`protein_docking_score_heuristic_limitation.ja` = "ヒューリスティックのみ：固定式の幾何・組成補完性スコアであり、物理的に正確なタンパク質間ドッキングシミュレーションではない（3D 構造なし、エネルギー関数なし）。"
The constant `800.0` Å² is a fixed documented typical-interface-size
constant for this skill.
Requirements: REQ-ASTRUCT-030
ADRs: ADR-0046
Depends-On: DES-ASTRUCT-001, DES-ASTRUCT-002, DES-ASTRUCT-003

## DES-ASTRUCT-040: Structural similarity / RMSD after optimal superposition module / 構造類似性・最適重ね合わせ後RMSDモジュール
Responsibilities: Receive coordinate lists `structure_a` and
`structure_b` already validated atomically by its handler wrapper via
`DES-ASTRUCT-002.validate_parameters`, center both structures on their
centroids, form the cross-covariance matrix, obtain the optimal rotation
via `numpy.linalg.svd`, apply the standard determinant-sign reflection
correction, and compute `rotation_matrix = R` and
`translation = centroid(B) - R @ centroid(A)` such that
`B_i ≈ R @ A_i + translation` for each point `i`. Return `rmsd`,
`rotation_matrix`, and `translation`, with matrix/vector values
serialized as plain nested Python lists.
Interfaces: `run_structural_similarity(structure_a, structure_b) ->
StructuralSimilarityResult {rmsd, rotation_matrix, translation}`.
Constraints: Unequal lengths, `N < 3`, and any coordinate that is not a
`list` or `tuple` of exactly 3 finite real numbers (numpy arrays and
other sequence types are rejected) are rejected by the handler wrapper
before this function is called; the reflection-correction step enforces
a proper rotation with determinant `+1`; when the cross-covariance
matrix between the centered A and B coordinates has rank less than 2
(fewer than 2 nonzero singular values — for example when all centered
points are collinear or coincident), `rmsd` remains deterministic but
`rotation_matrix` / `translation` are documented as not guaranteed
unique in this degenerate case, and the module still reports the result
produced by the same fixed SVD-based procedure without additional
canonicalization.
Requirements: REQ-ASTRUCT-040
ADRs: ADR-0047
Depends-On: DES-ASTRUCT-001, DES-ASTRUCT-002, DES-ASTRUCT-003

## DES-ASTRUCT-050: Residue contact-map heuristic module / 残基コンタクトマップ・ヒューリスティックモジュール
Responsibilities: Receive `coordinates`, `distance_threshold_A`, and
`min_sequence_separation` already validated atomically by its handler
wrapper via `DES-ASTRUCT-002.validate_parameters`, then evaluate
`contact[i][j]` as true iff `|i-j| >= min_sequence_separation` and the
Euclidean distance between coordinates `i` and `j` is less than or equal
to `distance_threshold_A`, with `contact[i][i] = false` always,
`contact_matrix` symmetric, and `total_contacts` counted only over the
upper triangle `i < j`.
Interfaces: `run_contact_map(coordinates, distance_threshold_A=8.0,
min_sequence_separation=3) -> ContactMapResult {contact_matrix,
total_contacts}`.
Constraints: `distance_threshold_A` must already have been validated as
a finite number greater than 0 and `min_sequence_separation` as an
integer greater than or equal to 1 before this function is called; the
coordinate list must already have been validated to contain at least 2
coordinates, each a `list` or `tuple` of exactly 3 finite real numbers;
this module is a C-alpha contact
heuristic only and does not infer atom-level contacts, side-chain
orientation, solvent effects, or dynamic ensembles.
Requirements: REQ-ASTRUCT-050
ADRs: ADR-0048
Depends-On: DES-ASTRUCT-001, DES-ASTRUCT-002, DES-ASTRUCT-003

## Planned source layout / 想定ソース構成

The implementation package for this feature is:

- `src/ai_structural_biology_scientist/__init__.py`
- `src/ai_structural_biology_scientist/dispatch.py`
- `src/ai_structural_biology_scientist/evidence.py`
- `src/ai_structural_biology_scientist/validation.py`
- `src/ai_structural_biology_scientist/secondary_structure.py`
- `src/ai_structural_biology_scientist/hydrophobicity.py`
- `src/ai_structural_biology_scientist/protein_docking_score.py`
- `src/ai_structural_biology_scientist/structural_similarity.py`
- `src/ai_structural_biology_scientist/contact_map.py`

This design also requires
`.github/skills/ai-structural-biology-scientist/manifest.json` and
`.github/skills/ai-structural-biology-scientist/SKILL.md`.

## Traceability summary / 追跡可能性一覧

| Design component | Requirement(s) | ADR |
| --- | --- | --- |
| DES-ASTRUCT-001 | REQ-ASTRUCT-001, REQ-ASTRUCT-002 | ADR-0041 |
| DES-ASTRUCT-002 | REQ-ASTRUCT-003 | ADR-0042 |
| DES-ASTRUCT-003 | REQ-ASTRUCT-004 | ADR-0043 |
| DES-ASTRUCT-010 | REQ-ASTRUCT-010 | ADR-0044 |
| DES-ASTRUCT-020 | REQ-ASTRUCT-020 | ADR-0045 |
| DES-ASTRUCT-030 | REQ-ASTRUCT-030 | ADR-0046 |
| DES-ASTRUCT-040 | REQ-ASTRUCT-040 | ADR-0047 |
| DES-ASTRUCT-050 | REQ-ASTRUCT-050 | ADR-0048 |

Every DES-ASTRUCT-010 through DES-ASTRUCT-050 module depends on
DES-ASTRUCT-001 (dispatch), DES-ASTRUCT-002 (validation), and
DES-ASTRUCT-003 (evidence schema); this table records the full
requirement / design coverage so any future ID mismatch is immediately
visible.

## Skill documentation deliverable / スキル文書成果物

`.github/skills/ai-structural-biology-scientist/SKILL.md` is a required
implementation deliverable (alongside `manifest.json` and the
`src/ai_structural_biology_scientist/` package) and must verbatim
include both exact bilingual limitation-label texts defined above:
`secondary_structure_heuristic_limitation.en` / `.ja`
(DES-ASTRUCT-010) and
`protein_docking_score_heuristic_limitation.en` / `.ja`
(DES-ASTRUCT-030), in both English and Japanese since REQ-ASTRUCT-001
requires every module's user-facing text to render in the request's
language.

## DES-ASTRUCT-060: npm skill-package completeness guard / npmスキル同梱完全性ガード
Responsibilities: Preserve parity between the npm bootstrap package's
shipped ai-structural-biology-scientist skill payload and its
importable Python sources by asserting that `package.json` `files`
contains both exact entries
`.github/skills/ai-structural-biology-scientist` and
`src/ai_structural_biology_scientist/**/*.py`, and by proving with an
`npm pack --dry-run --json` listing that the packed artifact contains
`.github/skills/ai-structural-biology-scientist/SKILL.md`,
`.github/skills/ai-structural-biology-scientist/manifest.json`, and
every current repository file matching
`src/ai_structural_biology_scientist/**/*.py`.
Interfaces: loadPackageManifest(path="package.json") -> PackageManifest;
listPackedFiles() -> set[str] from `npm pack --dry-run --json`;
assertAiStructuralBiologyScientistPackagingParity(packageManifest,
packedFiles) -> None.
Constraints: The authoritative packaged-artifact proof is the dry-run
pack listing, not only static inspection of `package.json`. This guard
covers npm distribution completeness only; Python package discovery
continues to rely on existing `src/` layout conventions, unchanged by
this design.
Requirements: REQ-ASTRUCT-060
ADRs: ADR-0113
Depends-On: DES-AISCI-020
