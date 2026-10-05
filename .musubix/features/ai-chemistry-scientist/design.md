---
schemaVersion: 1
feature: ai-chemistry-scientist
---
# Design / 設計

Architecture blueprint for the new `ai-chemistry-scientist` Copilot Agent
Skill. Mirrors the module-manifest dispatch pattern already used by
`ai-scientist` (`src/ai_scientist/manifest.py`) and reused verbatim by
`ai-materials-scientist` (`src/ai_materials_scientist/dispatch.py`): a
single skill entrypoint loads a static manifest mapping a method name to a
module function, and dispatches to exactly one module per request. Every
cheminformatics module is a pure Python/RDKit/numpy/scikit-learn
implementation; none calls an external solver binary or the network.

## DES-ACHEM-001: Method manifest & request dispatcher / 手法マニフェストと要求振り分け
Responsibilities: Load the static method-name-to-module manifest
(`.github/skills/ai-chemistry-scientist/manifest.json`; each entry has
`modulePath`, `functionName`, and bilingual `names.en`/`names.ja` lists,
identical in shape to `ai-materials-scientist`'s manifest), classify an
incoming bilingual user request against the 11 supported method
names/synonyms, detect the request's language (Japanese or English), and
on exactly one match resolve `modulePath`/`functionName` to that module's
handler wrapper function and invoke it with `(request_text, language)`
(the same `request_text` dispatch itself was given, unparsed); ask a
clarification question on an ambiguous (multi-method) match and reject
with no module invoked on no match. Propagate the detected language to
every downstream path (module handler, DES-ACHEM-002 validation failure,
clarification question, rejection message) so that every user-facing
sentence it produces or forwards is rendered wholly in that language,
limited to the permitted technical tokens (method names, unit symbols,
numeric values) per REQ-ACHEM-001's acceptance. Every module's handler
wrapper (one per method, e.g. `handle_molecular_descriptors(request_text,
language) -> ModuleOutcome`) is responsible for: (1) extracting its
module's structured `params` from `request_text` (parsing a SMILES string
or numeric arguments out of free text, or accepting them as
already-structured keyword arguments from a calling context — this
extraction is each handler wrapper's own documented responsibility, not
`dispatch`'s); (2) for the 10 atomic-validation modules
(DES-ACHEM-020/030/040/050/060/070/080/090/100/110) only, calling
DES-ACHEM-002's `validate_parameters` on the extracted `params` first,
returning a localized rejection `ModuleOutcome` with no further call on
failure; (3) calling its own `run_*` function (DES-ACHEM-010..110) with
the extracted (and, for atomic modules, already-validated) `params`; (4) for
DES-ACHEM-020's, DES-ACHEM-050's, DES-ACHEM-070's, DES-ACHEM-090's, and
DES-ACHEM-100's results only, substituting the raw result's
`limitation_label_key` (e.g. `"admet_heuristic_limitation"`) with the
matching `language`-specific fixed text from that module's own
Responsibilities section (e.g.
`admet_heuristic_limitation.en`/`.ja`), producing a final `result` whose
`limitation_label` field is already localized prose; and (5) wrapping
that (possibly label-substituted) raw `run_*` result via DES-ACHEM-003's
`record_run` into a `RunRecord`. The manifest and dispatcher's internal
method-routing tables (`_RUN_MODULE_PATHS`, `_RUN_FUNCTION_NAMES`) cover
exactly these 11 method slugs: `molecular-descriptors`,
`admet-prediction`, `qsar-modeling`, `molecular-similarity`,
`docking-score`, `drug-likeness-rules`, `structural-alerts`,
`molecular-formula-mass`, `bioactivity-classification`,
`salt-removal`, and `structure-format-conversion`;
`_LIMITATION_LABEL_MODULES` includes exactly `admet-prediction`,
`docking-score`, `structural-alerts`, `bioactivity-classification`, and
`salt-removal`. `structure-format-conversion` (DES-ACHEM-110) is not in
`_LIMITATION_LABEL_MODULES`: it is a deterministic local-format
conversion, not a heuristic module.
DES-ACHEM-010 (the one per-item-validated, batch-capable module per
ADR-0026) is the sole exception to step (2): its handler wrapper calls
`run_molecular_descriptors` directly with no separate upfront
`validate_parameters` call, because REQ-ACHEM-003's per-item granularity
requires `DES-ACHEM-002.validate_batch_item` to run interleaved with
per-item computation inside `run_molecular_descriptors` itself
(DES-ACHEM-010's own Responsibilities), not before it.
Interfaces: `dispatch(request_text, language=None, manifest_path=None) ->
DispatchResult` where `DispatchResult` is one of
`{outcome: "dispatch", module, language, handler_result}`,
`{outcome: "clarification", candidates, language, clarification_question}`,
or `{outcome: "rejected", language, rejected_method}`. `handler_result` is
always a `ModuleOutcome`: either `{ok: true, run_record}` (a DES-ACHEM-003
`RunRecord`) on success, or `{ok: false, parameter, constraint, language}`
(REQ-ACHEM-003's rejection) on validation failure — never a bare raw
`run_*` result. `constraint` is the fixed, language-invariant diagnostic
string defined by the violated requirement's acceptance (e.g. "must parse
to a valid RDKit molecule"), identical regardless of `language` — only
the surrounding user-facing sentence a caller builds around `parameter`/
`constraint` is rendered in `language`, matching REQ-ACHEM-003's
acceptance quoting that exact English constraint text unconditionally.
All three `DispatchResult` outcome variants', and `ModuleOutcome`'s,
other user-facing text is rendered in `language`. Reuses
`ai_data_scientist.language_router.detect_language` for language detection
(same helper `ai_materials_scientist.dispatch` already depends on).
Constraints: Must invoke at most one module per request (REQ-ACHEM-002
acceptance's "execute no other module" clause); must never mix Japanese
and English prose within one produced sentence (REQ-ACHEM-001
acceptance); the manifest is a static, checked-in JSON file, not a
runtime-discovered plugin registry.
Requirements: REQ-ACHEM-001, REQ-ACHEM-002
ADRs: ADR-0025
Depends-On: none


## DES-ACHEM-002: Shared parameter & chemical-validity validator / 共通パラメータ・化学的妥当性検証
Responsibilities: Validate each module's resolved input parameters against
that module's documented chemical-validity or numerical-adequacy domain
before any module performs a descriptor computation, model fit, or
similarity/score calculation, and report the violated parameter and
constraint on failure. Supports two granularities selected by the calling
module: atomic (reject the whole run on any invalid parameter) for
REQ-ACHEM-020/030/040/050/060/070/080/090/100/110, and per-item (reject
only the invalid item, continue computing the rest) for REQ-ACHEM-010's
batch SMILES input. For REQ-ACHEM-110 specifically, atomic validation
checks, in this fixed order, (a) `input_format` is one of `smiles`,
`inchi`, `molblock` (on failure: `parameter="input_format"`,
`constraint="must be one of the supported formats"`); (b) `output_format`
is one of `smiles`, `inchi`, `inchikey`, `molblock` (on failure:
`parameter="output_format"`, `constraint="must be one of the supported
formats"`); (c) `input_value` parses with the `input_format`-matching
RDKit parser into a non-empty molecule with no dummy/query atom (the same
`parse_smiles`-style chemical-validity domain reused by REQ-ACHEM-100 and
every other module) (on failure: `parameter="input_value"`,
`constraint="must parse with the <input_format>-matching RDKit parser"`);
all three checks run before any format conversion, per REQ-ACHEM-110
Constraints.
Interfaces: `validate_parameters(module_name, params) -> ValidationResult`
`{ok: true}` | `{ok: false, parameter, constraint}` for atomic validation;
`validate_batch_item(module_name, item_params) -> ValidationResult` (same
shape) invoked once per batch item for per-item validation, called by
`run_molecular_descriptors` itself (DES-ACHEM-010) for each SMILES in its
input list, interleaved with computing that item's descriptors — not by
the handler wrapper, since DES-ACHEM-010 is the sole module whose handler
wrapper skips the separate upfront `validate_parameters` call
(DES-ACHEM-001).
Constraints: Must run to completion (no partial computation) before any
module-specific state is produced for the unit it validates — a whole run
for atomic modules, or a single batch item for REQ-ACHEM-010 (REQ-ACHEM-003
acceptance).
Requirements: REQ-ACHEM-003
ADRs: ADR-0026
Depends-On: DES-ACHEM-001

## DES-ACHEM-003: Run evidence recorder / 実行根拠記録
Responsibilities: Capture every module run's resolved input parameters and
output result as a JSON-safe structured record with exactly three
top-level keys (`metadata`, `parameters`, `result`) per REQ-ACHEM-004.
Called by each module's handler wrapper (DES-ACHEM-001) exactly once,
immediately after that module's own `run_*` function returns its raw
result and only once DES-ACHEM-002 validation has already succeeded —
`record_run` is never called on a validation-failure path. Unlike
`ai-materials-scientist`'s `arrays`-based evidence (DES-AIMS-003), no
ndarray codec is needed here: every module's raw `result` is already
JSON-safe (scalars, strings, lists, and nested dicts of these — each
module's own section below states its exact result shape), so
`record_run` returns a plain `dict` with no `to_json`/`from_json` codec
step required.
Interfaces: `record_run(module_name, params, result, *, rdkit_version,
scikit_learn_version=None) -> RunRecord` `{metadata: {module,
schema_version, rdkit_version, [scikit_learn_version]}, parameters,
result}`. `scikit_learn_version` is included in `metadata` only when
supplied (REQ-ACHEM-030's QSAR module always supplies it; the other 10
modules omit it).
Constraints: Re-running with identical `parameters` against the same
installed RDKit/scikit-learn versions must reproduce a `result` that
compares exactly equal per REQ-ACHEM-004's tolerance rules (`==` for
integers, `1e-9` absolute tolerance for floats); no random seed is ever
recorded because no module has a stochastic step (REQ-ACHEM-004
Constraints).
Requirements: REQ-ACHEM-004
ADRs: ADR-0027
Depends-On: DES-ACHEM-001

Note on DES-ACHEM-010 through DES-ACHEM-110 below: each module's
`run_*(...)` function is the raw, unwrapped computation entry point. For
the 10 atomic-validation modules
(DES-ACHEM-020/030/040/050/060/070/080/090/100/110), it is called
internally by its DES-ACHEM-001 handler wrapper only after DES-ACHEM-002
`validate_parameters` succeeds, so these 10 `run_*` functions receive only
already-validated `params` and perform no parameter revalidation of their
own; none of them is called on a validation-failure path. DES-ACHEM-010
is the sole exception (per-item granularity, ADR-0026): its own
Responsibilities below describe `validate_batch_item` running interleaved
with computation inside `run_molecular_descriptors` itself, which its
handler wrapper calls directly with no separate upfront
`validate_parameters` step. Every `run_*` function's return shape
(`DescriptorResult`, `AdmetResult`, `QsarResult`, `SimilarityResult`,
`DockingResult`, `DrugLikenessRulesResult`, `StructuralAlertsResult`,
`MolecularFormulaMassResult`, `BioactivityClassificationResult`,
`SaltRemovalResult`, `StructureConversionResult`) is
exactly the `result` value DES-ACHEM-003's `record_run` wraps into a
`RunRecord`.

## DES-ACHEM-010: Molecular descriptor module / 分子記述子モジュール
Responsibilities: Parse each input SMILES with `Chem.MolFromSmiles`,
validate each parsed-or-not item independently via
`DES-ACHEM-002.validate_batch_item` (REQ-ACHEM-003's per-item granularity
for this module), and for each successfully parsed molecule compute
exactly the 7 documented descriptors (`MolWt`, `MolLogP`, `TPSA`,
`NumHDonors`, `NumHAcceptors`, `NumRotatableBonds`,
`rdMolDescriptors.CalcNumRings`), reporting results in input order with a
per-item rejection object in place of descriptors for an invalid item.
Interfaces: `run_molecular_descriptors(smiles_list) -> list[DescriptorResult
| RejectedItem]` where `DescriptorResult = {smiles, mol_wt, mol_logp, tpsa,
num_h_donors, num_h_acceptors, num_rotatable_bonds, num_rings}` and
`RejectedItem = {smiles, ok: false, parameter: "smiles", constraint}`.
Constraints: Exactly these 7 descriptors, no others; one malformed SMILES
in a batch must not abort computation of the other items (REQ-ACHEM-010
acceptance).
Requirements: REQ-ACHEM-010
ADRs: ADR-0028
Depends-On: DES-ACHEM-001, DES-ACHEM-002, DES-ACHEM-003

## DES-ACHEM-020: ADMET heuristic screening module / ADMETヒューリスティックスクリーニングモジュール
Responsibilities: Receive the single input SMILES already validated
atomically by its handler wrapper via `DES-ACHEM-002.validate_parameters`
(REQ-ACHEM-003's atomic granularity; this function performs no
revalidation), compute DES-ACHEM-010's 7 descriptors for it, then evaluate
the 4 Lipinski criteria (`MolWt<=500`, `MolLogP<=5`, `NumHDonors<=5`,
`NumHAcceptors<=10`) in that fixed order to build `lipinski_violations`
and `lipinski_pass` (`true` iff at most 1 criterion violated), and the 2
Veber criteria (`NumRotatableBonds<=10`, `TPSA<=140`) in that fixed order
to build `veber_violations` and `veber_pass` (`true` iff both hold).
Interfaces: `run_admet_prediction(smiles) -> AdmetResult {descriptors,
lipinski_violations: list[str], lipinski_pass: bool, veber_violations:
list[str], veber_pass: bool, limitation_label_key}`.
Constraints: Criterion-check order is fixed (MolWt, MolLogP, NumHDonors,
NumHAcceptors for Lipinski; NumRotatableBonds, TPSA for Veber) so
`*_violations` lists are deterministic (REQ-ACHEM-020 acceptance);
invalid input is rejected by the handler wrapper under REQ-ACHEM-003
before this function is ever called; `limitation_label_key` is the fixed
string `"admet_heuristic_limitation"` (not yet localized — see
DES-ACHEM-001's handler wrapper, which substitutes the matching
`language` text from the table below into the final `RunRecord.result
.limitation_label` field before `record_run`, replacing
`limitation_label_key`); the same two-language text must also appear
verbatim in SKILL.md (REQ-ACHEM-020 Constraints):
`admet_heuristic_limitation.en` = "Heuristic only: not a physically or
clinically validated ADMET prediction."; `admet_heuristic_limitation.ja`
= "ヒューリスティックのみ: 物理的または臨床的に検証されたADMET予測ではあ
りません。"
Requirements: REQ-ACHEM-020
ADRs: ADR-0029
Depends-On: DES-ACHEM-001, DES-ACHEM-002, DES-ACHEM-003

## DES-ACHEM-030: QSAR linear-regression module / QSAR線形回帰モジュール
Responsibilities: Its handler wrapper calls `DES-ACHEM-002
.validate_parameters` on `{training_set, query_smiles_list}` before this
function is ever invoked, rejecting if any training or query SMILES fails
to parse (naming `training_set` or `query_smiles_list` respectively), if
fewer than 5 training compounds are supplied (naming `training_set`), or
if the training set's augmented design matrix `[1, MolWt, MolLogP, TPSA]`
is not full column rank 4 (naming `training_set`); `validate_parameters`
itself computes each training/query molecule's `MolWt`/`MolLogP`/`TPSA`
descriptors (via DES-ACHEM-010's descriptor computation) solely to check
parseability and matrix rank — this is part of DES-ACHEM-002's validation
step, not the "model fit" computation REQ-ACHEM-003's "before performing
any ... model fit" constraint restricts (ADR-0030). Once validation
passes, this function independently parses and computes its own
`MolWt`/`MolLogP`/`TPSA` descriptors for every training and query molecule
(a second, self-contained descriptor computation — `validate_parameters`'s
`{ok: true}`/`{ok: false, ...}` return carries no descriptor payload to
reuse; recomputing is intentional, since REQ-ACHEM-004 requires every
module computation to be a deterministic pure function, so the two
computations always agree and the duplication is a documented, accepted
cost, not a correctness risk), fits `sklearn.linear_model
.LinearRegression()` (default parameters) mapping those 3 features to the
supplied activity values, predicts each query molecule's activity from
the fitted model, and reports the fitted intercept and 3 coefficients
alongside each query's predicted activity.
Interfaces: `run_qsar_modeling(training_set, query_smiles_list) ->
QsarResult {coefficients: [mol_wt_coef, mol_logp_coef, tpsa_coef],
intercept, predictions: list[{smiles, predicted_activity}]}` where
`training_set` is `list[{smiles, activity}]`.
Constraints: Exactly the 3-feature OLS fit described above, no
regularization, no feature scaling (REQ-ACHEM-030 Constraints); training
sets failing the size or rank check, or any training/query SMILES failing
to parse, are rejected by the handler wrapper under REQ-ACHEM-003 before
this function (and therefore `LinearRegression.fit`/`.predict`) is ever
called; `coefficients`/`intercept`/`predicted_activity` values must be
plain Python `float`s (converted from `numpy.float64` via e.g.
`float(...)`), not raw `numpy.ndarray`/`numpy.float64` objects, so
DES-ACHEM-003's `result` stays JSON-safe.
Requirements: REQ-ACHEM-030
ADRs: ADR-0030
Depends-On: DES-ACHEM-001, DES-ACHEM-002, DES-ACHEM-003

## DES-ACHEM-040: Molecular similarity search module / 分子類似度検索モジュール
Responsibilities: Receive the query SMILES and `k` already validated
atomically by its handler wrapper via `DES-ACHEM-002.validate_parameters`
(rejecting `k` outside `[1, 20]`; this function performs no
revalidation); load the bundled 20-row `sample_molecules.csv` dataset once
(module-level cache, read-only, no network fetch); compute a radius-2,
2048-bit Morgan fingerprint (`AllChem.GetMorganFingerprintAsBitVect(mol,
radius=2, nBits=2048)` or the equivalent non-deprecated `MorganGenerator`
API) for the query and for every dataset molecule; compute Tanimoto
similarity (`c / (a + b - c)`) between the query and each dataset
fingerprint; and return the top-`k` entries sorted by descending
similarity, ties broken by ascending `name`.
Interfaces: `run_molecular_similarity(query_smiles, k=5) ->
SimilarityResult {query_smiles, results: list[{name, similarity}]}`
(`results` length is `min(k, 20)`, sorted descending by `similarity` then
ascending by `name` on ties).
Constraints: The dataset is the fixed, checked-in 20-row CSV pinned by
REQ-ACHEM-040's acceptance table — no user-supplied dataset override in
this increment; `k` must be an integer in `[1, 20]`, rejected by the
handler wrapper under REQ-ACHEM-003 before this function is ever called.
Requirements: REQ-ACHEM-040
ADRs: ADR-0031
Depends-On: DES-ACHEM-001, DES-ACHEM-002, DES-ACHEM-003

## DES-ACHEM-050: Simplified docking-score heuristic module / 簡易ドッキングスコア・ヒューリスティックモジュール
Responsibilities: Receive the ligand SMILES and pocket specification
(`pocket_volume_A3>0`, `pocket_hba_sites`/`pocket_hbd_sites` finite
non-negative integers) already validated atomically by its handler
wrapper via `DES-ACHEM-002.validate_parameters` (this function performs
no revalidation); compute the ligand's heavy-atom count, `NumHDonors`,
and `NumHAcceptors` via RDKit; compute `ligand_volume = heavy_atom_count
* 15.0`, `size_fit = clip(1 - abs(ligand_volume - pocket_volume_A3) /
pocket_volume_A3, 0, 1)`, `matched_pairs = min(ligand_hbd,
pocket_hba_sites) + min(ligand_hba,
pocket_hbd_sites)`, `hbond_fit = matched_pairs / max(1, ligand_hbd +
ligand_hba)`, and `score = 0.5*size_fit + 0.5*hbond_fit`.
Interfaces: `run_docking_score(ligand_smiles, pocket_spec) ->
DockingResult {score, size_fit, hbond_fit, limitation_label_key}` where
`pocket_spec = {pocket_volume_A3, pocket_hba_sites, pocket_hbd_sites}`.
Constraints: Fixed formula only, no 3D conformer generation or energy
function (REQ-ACHEM-050 Constraints); invalid input is rejected by the
handler wrapper under REQ-ACHEM-003 before this function is ever called;
`limitation_label_key` is the fixed string `"docking_heuristic_limitation"`
(localized by the handler wrapper exactly as DES-ACHEM-020's
`limitation_label_key` is, substituting the matching `language` text
below into `RunRecord.result.limitation_label`); the same two-language
text must also appear verbatim in SKILL.md:
`docking_heuristic_limitation.en` = "Heuristic only: not a physically
accurate docking simulation (no 3D conformer generation, no energy
function)."; `docking_heuristic_limitation.ja` = "ヒューリスティックのみ:
物理的に正確なドッキングシミュレーションではありません（3D配座生成・エ
ネルギー関数なし）。"
Requirements: REQ-ACHEM-050
ADRs: ADR-0032
Depends-On: DES-ACHEM-001, DES-ACHEM-002, DES-ACHEM-003

## DES-ACHEM-060: Drug-likeness rule screening module / Lipinski/Veber以外の薬物らしさルールスクリーニングモジュール
Responsibilities: Receive the single input SMILES already validated
atomically by its handler wrapper via `DES-ACHEM-002.validate_parameters`
(REQ-ACHEM-003's atomic granularity; this function performs no
revalidation), compute DES-ACHEM-010's 7 descriptors for it together
with `aromatic_ring_count = rdMolDescriptors.CalcNumAromaticRings(mol)`,
`mol_mr = Descriptors.MolMR(mol)`, and `heavy_atom_count =
mol.GetNumHeavyAtoms()`, then evaluate the Ghose criteria (`160 <= MolWt
<= 480`, `-0.4 <= MolLogP <= 5.6`, `40 <= MolMR <= 130`, and `20 <=
heavy_atom_count <= 70`) in that fixed check order to build
`ghose_violations` naming every violated criterion in the fixed check
order `MolWt`, `MolLogP`, `MolMR`, `heavy_atom_count` and `ghose_pass`
(`true` iff all 4 hold), and the Egan criteria (`TPSA <= 131.6` and
`MolLogP <= 5.88`) in that fixed check order to build
`egan_violations` naming every violated criterion in the fixed check
order `TPSA`, `MolLogP` and `egan_pass` (`true` iff both hold). This
module extends REQ-ACHEM-020 with the two additional fixed-threshold rule
outcomes, Ghose and Egan, computed from descriptors that may overlap with
those used by Lipinski/Veber (e.g. `MolWt`, `MolLogP`, `TPSA`); it
reports only the Ghose and Egan pass/violation outcomes and does not
re-report the Lipinski or Veber pass/violation outcomes already reported
by REQ-ACHEM-020.
Interfaces: `run_drug_likeness_rules(smiles) -> DrugLikenessRulesResult
{aromatic_ring_count, mol_mr, heavy_atom_count, ghose_violations:
list[str], ghose_pass: bool, egan_violations: list[str], egan_pass:
bool}`.
Constraints: Criterion-check order is fixed (`MolWt`, `MolLogP`, `MolMR`,
`heavy_atom_count` for Ghose; `TPSA`, `MolLogP` for Egan) so both
`*_violations` lists are deterministic (REQ-ACHEM-060 Acceptance);
invalid input is rejected by the handler wrapper under REQ-ACHEM-003
before this function is ever called; Ghose and Egan are deterministic
fixed-threshold rule screens over the computed descriptor values; no
external data, no stochastic step, and no network call are involved.
Requirements: REQ-ACHEM-060
ADRs: ADR-0049
Depends-On: DES-ACHEM-001, DES-ACHEM-002, DES-ACHEM-003

## DES-ACHEM-070: Structural alert screening module / 構造アラート(PAINS風)スクリーニングモジュール
Responsibilities: Receive the single input SMILES already validated
atomically by its handler wrapper via `DES-ACHEM-002.validate_parameters`
(REQ-ACHEM-003's atomic granularity; this function performs no
revalidation), compile and match exactly this fixed named SMARTS alert
list against the parsed molecule in its fixed alert-definition order:
`nitro_group: [NX3](=O)=O`, `aldehyde: [CX3H1](=O)`,
`michael_acceptor_enone: C=CC(=O)`, `epoxide: C1OC1`, and
`free_thiol: [SX2H]`. Report `alerts_matched` as the list of matched
alert names in that fixed alert-definition order, with non-matching alert
names omitted, and `alert_count` as its length.
Interfaces: `run_structural_alerts(smiles) -> StructuralAlertsResult
{alerts_matched: list[str], alert_count: int, limitation_label_key}`.
Constraints: Invalid input is rejected by the handler wrapper under
REQ-ACHEM-003 before this function is ever called; `limitation_label_key`
is the fixed string `"structural_alerts_heuristic_limitation"` (not yet
localized — see DES-ACHEM-001's handler wrapper, which substitutes the
matching `language` text from the table below into the final
`RunRecord.result.limitation_label` field before `record_run`,
replacing `limitation_label_key`); the same two-language text must also
appear verbatim in SKILL.md (REQ-ACHEM-070 Constraints):
`structural_alerts_heuristic_limitation.en` = "Heuristic only: a small
fixed illustrative SMARTS alert list, not the validated PAINS/Brenk
filter catalog."; `structural_alerts_heuristic_limitation.ja` =
"ヒューリスティックのみ: 固定の小規模な例示用SMARTSアラート一覧であり、
検証済みのPAINS/Brenkフィルタ・カタログではない。"
Requirements: REQ-ACHEM-070
ADRs: ADR-0050
Depends-On: DES-ACHEM-001, DES-ACHEM-002, DES-ACHEM-003

## DES-ACHEM-080: Molecular formula and exact mass module / 分子式・正確質量モジュール
Responsibilities: Receive the single input SMILES already validated
atomically by its handler wrapper via `DES-ACHEM-002.validate_parameters`
(REQ-ACHEM-003's atomic granularity; this function performs no
revalidation), parse the molecule, and compute `molecular_formula =
rdMolDescriptors.CalcMolFormula(mol)` and `exact_mass =
Descriptors.ExactMolWt(mol)`.
Interfaces: `run_molecular_formula_mass(smiles) ->
MolecularFormulaMassResult {molecular_formula, exact_mass}`.
Constraints: Invalid input is rejected by the handler wrapper under
REQ-ACHEM-003 before this function is ever called; determinism and
run-evidence behavior are exactly those of REQ-ACHEM-004; this module
introduces no additional metadata fields beyond the existing
`rdkit_version` requirement.
Requirements: REQ-ACHEM-080
ADRs: ADR-0051
Depends-On: DES-ACHEM-001, DES-ACHEM-002, DES-ACHEM-003

## DES-ACHEM-090: Heuristic target-class activity classification module / 標的クラス活性ヒューリスティック分類モジュール
Responsibilities: Receive the single input SMILES already validated
atomically by its handler wrapper via `DES-ACHEM-002.validate_parameters`
(REQ-ACHEM-003's atomic granularity; this function performs no
revalidation), compute DES-ACHEM-010's `tpsa`, `mol_logp`, and `mol_wt`
descriptors together with `aromatic_ring_count =
rdMolDescriptors.CalcNumAromaticRings(mol)`, then assign `label` by this
fixed decision order: first `"CNS_like"` iff `TPSA < 90` and `2.0 <=
MolLogP <= 5.0`; if that test fails, then `"kinase_inhibitor_like"` iff
`MolWt > 400` and `aromatic_ring_count >= 3`; otherwise `"other"`.
Interfaces: `run_bioactivity_classification(smiles) ->
BioactivityClassificationResult {label, tpsa, mol_logp, mol_wt,
aromatic_ring_count, limitation_label_key}`.
Constraints: Invalid input is rejected by the handler wrapper under
REQ-ACHEM-003 before this function is ever called; `limitation_label_key`
is the fixed string `"bioactivity_classifier_heuristic_limitation"` (not
yet localized — see DES-ACHEM-001's handler wrapper, which substitutes
the matching `language` text from the table below into the final
`RunRecord.result.limitation_label` field before `record_run`,
replacing `limitation_label_key`); the same two-language text must also
appear verbatim in SKILL.md (REQ-ACHEM-090 Constraints):
`bioactivity_classifier_heuristic_limitation.en` = "Heuristic only: not a
ChEMBL-trained or experimentally validated bioactivity classifier.";
`bioactivity_classifier_heuristic_limitation.ja` = "ヒューリスティックの
み: ChEMBLで学習済みでも実験的に検証済みでもない生物活性分類器ではな
い。"; the fixed decision order (`"CNS_like"` first,
`"kinase_inhibitor_like"` second, `"other"` last) is part of the
observable behavior and shall not be reordered.
Requirements: REQ-ACHEM-090
ADRs: ADR-0052
Depends-On: DES-ACHEM-001, DES-ACHEM-002, DES-ACHEM-003

## DES-ACHEM-100: SMILES salt removal / structure standardization module / SMILES塩除去・構造標準化モジュール
Responsibilities: Receive the single input SMILES already validated
atomically by its handler wrapper via `DES-ACHEM-002.validate_parameters`
(REQ-ACHEM-003's atomic granularity, reusing the shared `parse_smiles`
chemical-validity domain — rejects empty strings, unparseable SMILES, and
dummy/query atoms; this function performs no revalidation), split the
already-validated whole molecule into its disconnected fragments via
`Chem.GetMolFrags(mol, asMols=True, sanitizeFrags=False)`, score every
fragment by the fixed sort key `(-fragment.GetNumHeavyAtoms(),
Chem.MolToSmiles(fragment))` (ADR-0105), and report the first-ranked
fragment's canonical SMILES as `standardized_smiles`, every other
fragment's canonical SMILES (in the same ascending sort-key order) as
`removed_fragments`, and whether more than 1 fragment was present as
`fragments_removed`.
Interfaces: `run_salt_removal(smiles) -> SaltRemovalResult
{standardized_smiles, removed_fragments: list[str], fragments_removed:
bool, limitation_label_key}`.
Constraints: Invalid input (empty, unparseable, or containing a dummy/query
atom) is rejected by the handler wrapper under REQ-ACHEM-003 before this
function is ever called, using the identical `parse_smiles` domain as
DES-ACHEM-010/080/090; this function performs no parameter revalidation of
its own. The sort key is exactly `(-heavy_atom_count, canonical_smiles)`
(ADR-0105) — not RDKit's `rdMolStandardize.LargestFragmentChooser`
default. `limitation_label_key` is the fixed string
`"salt_removal_heuristic_limitation"` (not yet localized — see
DES-ACHEM-001's handler wrapper, which substitutes the matching `language`
text from the table below into the final `RunRecord.result
.limitation_label` field before `record_run`, replacing
`limitation_label_key`); the same two-language text must also appear
verbatim in SKILL.md (REQ-ACHEM-100 Constraints):
`salt_removal_heuristic_limitation.en` = "Heuristic only: treats every
disconnected fragment except the one with the greatest heavy-atom count as
removable salt/solvent; not always chemically correct (e.g. for a genuine
covalent multi-component cocrystal)."; `salt_removal_heuristic_limitation
.ja` = "ヒューリスティックのみ: 最大重原子数を持つフラグメント以外の
すべての分離フラグメントを除去可能な塩・溶媒として扱うが、常に化学的に
正しいとは限らない（例: 真の共有結合性多成分共結晶の場合）。"
Requirements: REQ-ACHEM-100
ADRs: ADR-0105
Depends-On: DES-ACHEM-001, DES-ACHEM-002, DES-ACHEM-003

## DES-ACHEM-110: Chemical structure format conversion module / 化学構造フォーマット変換モジュール
Responsibilities: Receive `{input_format, input_value, output_format}`
already validated atomically by its handler wrapper via
`DES-ACHEM-002.validate_parameters` (REQ-ACHEM-003's atomic granularity:
`input_format`/`output_format` each in their documented allowed sets, and
`input_value` parses with the `input_format`-matching RDKit parser into a
non-empty molecule with no dummy/query atom; this function performs no
revalidation), parse `input_value` with the `input_format`-matching RDKit
parser (`Chem.MolFromSmiles` for `smiles`, `Chem.inchi.MolFromInchi` for
`inchi`, `Chem.MolFromMolBlock` for `molblock`), render it with the
`output_format`-matching RDKit writer (`Chem.MolToSmiles` for `smiles`,
`Chem.inchi.MolToInchi` for `inchi`, `Chem.inchi.MolToInchiKey` for
`inchikey`, `Chem.MolToMolBlock` for `molblock`), and report
`{output_format, output_value}`.
Interfaces: `run_structure_conversion(input_format, input_value,
output_format) -> StructureConversionResult {output_format,
output_value}`.
Constraints: Invalid input (`input_format`/`output_format` outside their
documented allowed sets, or `input_value` failing to parse with the
`input_format`-matching parser, including empty input and dummy/query
atoms) is rejected by the handler wrapper under REQ-ACHEM-003 before this
function is ever called; this function performs no parameter revalidation
of its own (ADR-0106). `inchikey` is accepted only as `output_format`,
never `input_format`, per ADR-0106's one-way-hash rationale. This module
performs deterministic local RDKit format parsing/rendering only — no
network call, no PubChem/ChEMBL/DrugBank lookup of any kind (ADR-0106) —
and carries no heuristic-limitation label (it is a deterministic
representation-conversion operation for successfully converted
structures, not a predictive or approximate heuristic; it does not
promise bytewise, metadata, or coordinate preservation across formats
that do not share that information — e.g. a Molblock's 2D/3D coordinates
have no SMILES/InChI equivalent — per REQ-ACHEM-110 Constraints; this is
a documented scope boundary, not an approximation).
Requirements: REQ-ACHEM-110
ADRs: ADR-0106
Depends-On: DES-ACHEM-001, DES-ACHEM-002, DES-ACHEM-003

## Traceability summary / 追跡可能性一覧

| Design component | Requirement(s) | ADR |
| --- | --- | --- |
| DES-ACHEM-001 | REQ-ACHEM-001, REQ-ACHEM-002 | ADR-0025 |
| DES-ACHEM-002 | REQ-ACHEM-003 | ADR-0026 |
| DES-ACHEM-003 | REQ-ACHEM-004 | ADR-0027 |
| DES-ACHEM-010 | REQ-ACHEM-010 | ADR-0028 |
| DES-ACHEM-020 | REQ-ACHEM-020 | ADR-0029 |
| DES-ACHEM-030 | REQ-ACHEM-030 | ADR-0030 |
| DES-ACHEM-040 | REQ-ACHEM-040 | ADR-0031 |
| DES-ACHEM-050 | REQ-ACHEM-050 | ADR-0032 |
| DES-ACHEM-060 | REQ-ACHEM-060 | ADR-0049 |
| DES-ACHEM-070 | REQ-ACHEM-070 | ADR-0050 |
| DES-ACHEM-080 | REQ-ACHEM-080 | ADR-0051 |
| DES-ACHEM-090 | REQ-ACHEM-090 | ADR-0052 |
| DES-ACHEM-100 | REQ-ACHEM-100 | ADR-0105 |
| DES-ACHEM-110 | REQ-ACHEM-110 | ADR-0106 |

Every DES-ACHEM-010 through DES-ACHEM-110 module depends on DES-ACHEM-001
(dispatch), DES-ACHEM-002 (validation), and DES-ACHEM-003 (evidence
schema); this table records the full requirement/design/ADR coverage so a
change to any one artifact's linked IDs is immediately visible as a
mismatch.

## Skill documentation deliverable / スキル文書成果物

`.github/skills/ai-chemistry-scientist/SKILL.md` is a required
implementation deliverable (alongside `manifest.json` and the
`src/ai_chemistry_scientist/` package) and must verbatim include all
exact bilingual limitation-label texts defined above:
`admet_heuristic_limitation.en`/`.ja` (DES-ACHEM-020),
`docking_heuristic_limitation.en`/`.ja` (DES-ACHEM-050),
`structural_alerts_heuristic_limitation.en`/`.ja` (DES-ACHEM-070),
`bioactivity_classifier_heuristic_limitation.en`/`.ja`
(DES-ACHEM-090), and `salt_removal_heuristic_limitation.en`/`.ja`
(DES-ACHEM-100) (REQ-ACHEM-020, REQ-ACHEM-050, REQ-ACHEM-070,
REQ-ACHEM-090, and REQ-ACHEM-100 Constraints), in both English and
Japanese since REQ-ACHEM-001 requires every module's user-facing text to
render in the request's language. The newly added
`salt_removal_heuristic_limitation.en`/`.ja` text (DES-ACHEM-100,
verbatim, reproduced here as the single normative source alongside
DES-ACHEM-100's own Responsibilities section) is: `.en` = "Heuristic
only: treats every disconnected fragment except the one with the
greatest heavy-atom count as removable salt/solvent; not always
chemically correct (e.g. for a genuine covalent multi-component
cocrystal)."; `.ja` = "ヒューリスティックのみ: 最大重原子数を持つ
フラグメント以外のすべての分離フラグメントを除去可能な塩・溶媒として
扱うが、常に化学的に正しいとは限らない（例: 真の共有結合性多成分共
結晶の場合）。" DES-ACHEM-110 carries no
limitation-label text (it is not a heuristic module). This is a
documentation-content check performed during implementation review, not a
separate design component (it has no own interface/behavior beyond the
fixed strings already specified in DES-ACHEM-020/050/070/090/100).

## Review record (CHANGE-021) / レビュー記録(CHANGE-021)
DES-ACHEM-100/110 and the DES-ACHEM-001/002/003 amendments for this third
increment passed `musubix3 design validate`. An independent native
`rubber-duck` review found 5 issues on the first pass (stale
8-atomic-validation-module/9-method-slug counts in DES-ACHEM-001,
REQ-ACHEM-110's validation order/rejected-parameter/constraint strings not
specified in DES-ACHEM-002, an overclaimed "lossless-per-format-pair"
statement in DES-ACHEM-110, the salt-removal limitation text referenced
only by key rather than quoted verbatim in the Skill documentation
deliverable section, and a stale "8 modules" count in DES-ACHEM-003); all
5 were fixed, and a second review round confirmed zero remaining issues.
本増分（DES-ACHEM-100/110、および第3増分向けの DES-ACHEM-001/002/003
の改訂）は `musubix3 design validate` に合格した。独立した native
`rubber-duck` レビューは初回パスで 5 件の指摘（DES-ACHEM-001 の
「アトミック検証モジュール8件/手法スラッグ9件」という古い件数、
DES-ACHEM-002 に REQ-ACHEM-110 の検証順序・拒否パラメータ名・制約文字列が
未規定だった点、DES-ACHEM-110 の「フォーマット対ごとにロスレス」という
過大な主張、Skill文書成果物節で塩除去の制限文言がキー名でのみ参照され
リテラル引用されていなかった点、DES-ACHEM-003 の「8モジュール」という
古い件数）を検出し、すべて修正した上で、2回目のレビューで残存課題ゼロを
確認した。
