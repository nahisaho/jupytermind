---
schemaVersion: 1
feature: ai-chemistry-scientist
---
# Requirements / 要求

Feature: A new Copilot Agent Skill, `ai-chemistry-scientist`, that hosts
domain-specific cheminformatics/drug-discovery modules behind a single skill
boundary, analogous to how `ai-data-scientist` hosts generic data-analysis
modules, `ai-scientist` hosts the generic research-process phases, and
`ai-materials-scientist` hosts materials-science simulation modules. This
first increment adds five modules selected by MECE survey of the external
ToolUniverse project's cheminformatics/drug-discovery domain taxonomy (used
only to identify candidate domains, not to reuse any of its code, data, or
external API calls): molecular descriptor calculation, ADMET heuristic
screening, QSAR linear-regression modeling, molecular similarity search, and
a simplified docking-score heuristic.
This second increment extends the skill to 9 total modules by adding 4 more
modules — drug-likeness rule screening beyond Lipinski/Veber, structural
alert screening, molecular formula and exact mass, and heuristic target-class
activity classification — inspired by ToolUniverse's PubChem/ChEMBL/drug-
safety tool taxonomy (again only as domain inspiration, not to reuse any of
its code, data, or external API calls).
This third increment extends the skill to 11 total modules by adding 2 more
modules — SMILES salt removal/structure standardization and chemical
structure format conversion (SMILES/InChI/InChIKey/Molblock) — identified by
gap analysis against the `aipoch/openscience-skill-marketplace` catalog
(used only to identify candidate domains; no code, data, or license-encumbered
content from that catalog is reused, consistent with its own disclosed
license-ambiguity caveats).

This fourth increment extends the skill to 14 total modules by adding 3 more
modules — dose-response curve fitting, pharmacokinetic non-compartmental
analysis, and Michaelis-Menten enzyme kinetics — identified by MECE survey
of the external `mims-harvard/ToolUniverse` project's skill taxonomy,
restricted to the subset that is pure computation over user-supplied
numeric data with no external API/database dependency (used only to
identify candidate domains, not to reuse any of its code, data, or external
API calls).

All modules are implemented with RDKit (required dependency) plus
numpy/scikit-learn already present in this repository, and this fourth
increment's 3 modules additionally use `scipy.optimize.curve_fit` (`scipy`
is already a root `pyproject.toml` dependency, newly imported by
`ai_chemistry_scientist` here for the first time); no other external
solver binaries and no network calls. Each module validates its own input
parameters, per its own stated domain, and rejects a request that would be
chemically undefined (e.g. an unparseable SMILES string) or numerically
degenerate before performing any computation — at the validation granularity
(whole-run vs. per-batch-item) that REQ-ACHEM-003 defines for that module.

## REQ-ACHEM-001: Bilingual instruction support / 日英両対応の指示理解
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall accept user requests and produce user-facing messages in whichever of Japanese or English the user's request used, for every module in this chemistry skill.
Acceptance: A fixed Japanese-language fixture request ("分子記述子を計算したい") produces a response whose every sentence is Japanese prose (English technical tokens limited to method names, unit symbols, and numeric values are permitted); the English-equivalent fixture request ("I want to calculate molecular descriptors") produces an all-English response; neither response contains a sentence mixing Japanese and English prose.

## REQ-ACHEM-002: Module routing by request content / 要求内容によるモジュール振り分け
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user's request text contains one of the chemistry skill manifest's registered name/synonym strings for a supported method, the system shall dispatch the request to exactly that method's module handler and execute no other module, where the supported methods are the 11 manifest-registered chemistry modules defined by REQ-ACHEM-010/020/030/040/050/060/070/080/090/100/110, each with both an English and a Japanese registered name/synonym list in the manifest.
Acceptance: For each of the 11 methods, a fixture request using one of its registered English names and a separate fixture request using one of its registered Japanese names each dispatch to exactly that method's handler and no other; a fixture request containing two different methods' registered names yields a clarification question listing both candidates with no module invoked; a fixture request containing none of the registered names yields a rejection message with no module invoked.

## REQ-ACHEM-003: Input and parameter validation / 入力・パラメータ検証
Priority: must
Type: functional
Pattern: unwanted-behavior
Statement: If a requested module's input parameters fail that module's own documented chemical-validity or numerical-adequacy domain, then the system shall reject the run and report which parameter violated which named constraint, before performing any descriptor computation, model fit, or similarity/score calculation.
Acceptance: A single-SMILES request whose `smiles` parameter fails RDKit's `Chem.MolFromSmiles` parse (returns `None`) — for example the malformed string `"C1CC"` (unclosed ring) — is rejected with a message naming the `smiles` parameter and the constraint "must parse to a valid RDKit molecule"; no descriptor, score, or model computation is performed for that run. For a batch-capable module (REQ-ACHEM-010), a multi-SMILES request validates and rejects each input item independently: an invalid item is reported as a per-item rejection naming the `smiles` parameter and the violated constraint, while every other item in the same batch is still computed. The same per-run-or-per-item pattern (reject before computation, name the parameter and constraint) applies to every module's documented domain, including each module-specific domain listed in its own requirement below.
Constraints: This requirement's "chemical-validity or numerical-adequacy domain" is defined per module by REQ-ACHEM-010/020/030/040/050/060/070/080/090/100/110; it does not itself define a single universal validity test applicable across all modules in this skill. Validation granularity is per module: REQ-ACHEM-010 (batch descriptor calculation) validates and rejects each SMILES item independently without aborting the rest of the batch; REQ-ACHEM-020/030/040/050/060/070/080/090/100/110 (single-ligand/model/query modules) validate the whole run atomically and reject the entire run with no partial computation when any parameter is invalid.

## REQ-ACHEM-004: Reproducible run evidence / 再現可能な実行根拠
Priority: must
Type: functional
Pattern: event-driven
Statement: When a module run completes, the system shall record a deterministic result (produced without any random seed) with exactly three top-level keys: `metadata` (a JSON-safe dict containing at least `module`, `schema_version`, and `rdkit_version`), `parameters` (a JSON-safe dict of the resolved input parameters), and `result` (a JSON-safe dict or list of the module's output values).
Acceptance: For each of the 11 modules, two runs with identical `parameters` against the same installed RDKit/scikit-learn versions produce `result` values that compare exactly equal (numeric fields equal via `==` for integers and within `1e-9` absolute tolerance for floats); `metadata.rdkit_version` matches the installed `rdkit.__version__` string, and for the QSAR module (REQ-ACHEM-030) `metadata.scikit_learn_version` matches the installed `sklearn.__version__` string.
Constraints: "Deterministic" means every module's governing computation (RDKit descriptor calculation, rule screening, SMARTS substructure matching, molecular-formula/exact-mass calculation, heuristic target-class classification, scikit-learn `LinearRegression` least-squares fit, fingerprint similarity, the fixed arithmetic docking-score formula, fixed-sort-key fragment selection, or RDKit format parsing/rendering) is a pure function of `parameters` and the installed RDKit/scikit-learn version, with no stochastic step and therefore no seed to record.

## REQ-ACHEM-010: Molecular descriptor calculation / 分子記述子計算
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests molecular descriptors for one or more SMILES strings, the system shall parse each SMILES with RDKit and compute, for each successfully parsed molecule, exactly these seven descriptors via RDKit's own documented functions: molecular weight (`Descriptors.MolWt`), octanol-water partition coefficient (`Descriptors.MolLogP`, Crippen method), topological polar surface area in Å² (`Descriptors.TPSA`), hydrogen-bond donor count (`Descriptors.NumHDonors`), hydrogen-bond acceptor count (`Descriptors.NumHAcceptors`), rotatable bond count (`Descriptors.NumRotatableBonds`), and ring count (`rdMolDescriptors.CalcNumRings`), reporting each per input SMILES in the same order as supplied.
Acceptance: For the reference molecule aspirin (SMILES `"CC(=O)OC1=CC=CC=C1C(=O)O"`), the computed descriptors equal, within the tolerances of REQ-ACHEM-004: MolWt = 180.159 ± 0.01, MolLogP = 1.3101 ± 0.001, TPSA = 63.60 ± 0.01, NumHDonors = 1, NumHAcceptors = 3, NumRotatableBonds = 2, NumRings = 1. A batch request of `["CC(=O)OC1=CC=CC=C1C(=O)O", "C1CC"]` (aspirin followed by the malformed SMILES from REQ-ACHEM-003) returns the aspirin descriptors at index 0 and a per-item rejection (not a computed descriptor value) at index 1, without aborting the whole batch.

## REQ-ACHEM-020: ADMET heuristic screening / ADMETヒューリスティックスクリーニング
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests ADMET screening for a SMILES string, the system shall compute the REQ-ACHEM-010 descriptors and report two independent heuristic flags: a Lipinski's-Rule-of-Five outcome (`lipinski_pass`: true when at most 1 of the 4 criteria MolWt <= 500, MolLogP <= 5, NumHDonors <= 5, NumHAcceptors <= 10 is violated, each reported individually as `lipinski_violations` naming the violated criteria), and a Veber's-rule outcome (`veber_pass`: true only when both NumRotatableBonds <= 10 and TPSA <= 140 hold, each reported individually as `veber_violations` naming the violated criteria).
Acceptance: Aspirin (descriptors per REQ-ACHEM-010) has `lipinski_violations = []`, `lipinski_pass = true`, `veber_violations = []`, `veber_pass = true`. Cyclosporine A (SMILES `"CCC1NC(=O)C(C(O)C(C)CC=CC)N(C)C(=O)C(C(C)C)N(C)C(=O)C(CC(C)C)N(C)C(=O)C(CC(C)C)N(C)C(=O)C(C)NC(=O)C(C)NC(=O)C(CC(C)C)N(C)C(=O)C(C(C)C)N(C)C(=O)C(CC(C)C)N(C)C1=O"`, MolWt ≈ 1145.58, MolLogP ≈ 4.15, NumHDonors = 4, NumHAcceptors = 11, NumRotatableBonds = 15, TPSA ≈ 249.70) has `lipinski_violations = ["MolWt", "NumHAcceptors"]` (exactly this single ordered list of 2 criterion names, in the fixed criterion-check order MolWt, MolLogP, NumHDonors, NumHAcceptors) with `lipinski_pass = false`, and `veber_violations = ["NumRotatableBonds", "TPSA"]` (exactly this single ordered list, in the fixed criterion-check order NumRotatableBonds, TPSA) with `veber_pass = false`.
Constraints: This is an explicitly-labeled heuristic, not a physically or clinically validated ADMET prediction; the limitation label is part of the module's output and of SKILL.md documentation.

## REQ-ACHEM-030: QSAR linear-regression modeling / QSAR線形回帰モデリング
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests QSAR model fitting given a training set of at least 5 SMILES-activity pairs and a query list of SMILES, the system shall report a predicted activity value for each query molecule together with the fitted model's coefficients and intercept.
Acceptance: Given the fixed training set of exactly these 5 named compounds (`aspirin` = `"CC(=O)OC1=CC=CC=C1C(=O)O"`, `ibuprofen` = `"CC(C)CC1=CC=C(C=C1)C(C)C(=O)O"`, `caffeine` = `"CN1C=NC2=C1C(=O)N(C(=O)N2C)C"`, `paracetamol` = `"CC(=O)NC1=CC=C(C=C1)O"`, `naproxen` = `"COC1=CC2=CC(=CC=C2C=C1)C(C)C(=O)O"`) whose activity values are defined exactly by the known linear law `activity = 2.0*MolWt + 0.0*MolLogP + 0.0*TPSA - 50.0` (computed from each compound's own RDKit descriptors, with zero residual by construction; the resulting design matrix `[1, MolWt, MolLogP, TPSA]` for these 5 compounds has full column rank 4), the fitted model's intercept and 3 coefficients each equal the law's corresponding constant (`2.0, 0.0, 0.0`, intercept `-50.0`) within `1e-6` absolute tolerance, and for the query SMILES `"OC(=O)Cc1ccccc1Nc1c(Cl)cccc1Cl"` (diclofenac, not in the training set), the predicted activity equals `2.0*MolWt - 50.0` (using diclofenac's own descriptors, `MolWt ≈ 296.153`, predicted activity `≈ 542.306`) within `1e-6` absolute tolerance. A request with a 4-compound training set is rejected naming `training_set` and the "at least 5 compounds" constraint, with no model fit attempted.
Constraints: The feature vector is the 3 RDKit descriptors MolWt, MolLogP, and TPSA for every training and query molecule; the fit is an ordinary-least-squares linear regression (`sklearn.linear_model.LinearRegression` with default parameters) mapping those 3 features to the activity value. A training set with fewer than 5 compounds, or whose augmented design matrix `[1, MolWt, MolLogP, TPSA]` is not full column rank 4, is rejected under REQ-ACHEM-003, naming the `training_set` parameter and the constraint "must contain at least 5 compounds with a full-rank descriptor matrix", before any model fit is attempted.

## REQ-ACHEM-040: Molecular similarity search / 分子類似度検索
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests molecular similarity search for a query SMILES, the system shall compute a radius-2, 2048-bit Morgan fingerprint for the query and for every molecule in a bundled sample dataset of exactly 20 named molecules, compute the Tanimoto similarity between the query fingerprint and each dataset fingerprint, and return the top-`k` (default `k=5`) dataset entries ranked by descending similarity (ties broken by ascending `name`), each with its `name` and similarity value.
Acceptance: The bundled dataset `src/ai_chemistry_scientist/data/sample_molecules.csv` (columns `name,smiles`) contains exactly these 20 rows, in this order: `aspirin`=`"CC(=O)OC1=CC=CC=C1C(=O)O"`, `ibuprofen`=`"CC(C)CC1=CC=C(C=C1)C(C)C(=O)O"`, `caffeine`=`"CN1C=NC2=C1C(=O)N(C(=O)N2C)C"`, `paracetamol`=`"CC(=O)NC1=CC=C(C=C1)O"`, `naproxen`=`"COC1=CC2=CC(=CC=C2C=C1)C(C)C(=O)O"`, `diclofenac`=`"OC(=O)Cc1ccccc1Nc1c(Cl)cccc1Cl"`, `warfarin`=`"CC(=O)CC(c1ccccc1)c1c(O)c2ccccc2oc1=O"`, `metformin`=`"CN(C)C(=N)NC(=N)N"`, `atorvastatin`=`"CC(C)c1c(C(=O)Nc2ccccc2)c(-c2ccc(F)cc2)c(-c2ccc(O)cc2)n1CCC(O)CC(O)CC(=O)O"`, `omeprazole`=`"CC1=CN=C(C(=C1OC)C)CS(=O)c1nc2ccc(OC)cc2[nH]1"`, `loratadine`=`"CCOC(=O)N1CCC(=C2c3ccc(Cl)cc3CCc3cccnc23)CC1"`, `cetirizine`=`"OC(=O)COCCN1CCN(CC1)C(c1ccccc1)c1ccc(Cl)cc1"`, `simvastatin`=`"CCC(C)(C)C(=O)OC1CC(C)C=C2C=CC(C)C(CCC3CC(O)CC(=O)O3)C12"`, `lisinopril`=`"CCCCC(N(CCCC(N)C(=O)O)C(=O)C(CCc1ccccc1)N)C(=O)N1CCCC1C(=O)O"`, `amlodipine`=`"CCOC(=O)C1=C(COCCN)NC(C)=C(C(=O)OC)C1c1ccccc1Cl"`, `losartan`=`"CCCCc1nc(Cl)c(CO)n1Cc1ccc(-c2ccccc2-c2nnn[nH]2)cc1"`, `metoprolol`=`"COCCc1ccc(OCC(O)CNC(C)C)cc1"`, `furosemide`=`"NS(=O)(=O)c1cc(C(=O)O)c(NCc2ccco2)cc1Cl"`, `ranitidine`=`"CNC(=C[N+](=O)[O-])NCCSCc1ccc(CN(C)C)o1"`, `sertraline`=`"CNC1CCC(c2ccc(Cl)c(Cl)c2)c2ccccc21"`. A query of the exact aspirin SMILES against this dataset, at the default `k=5`, returns exactly this ranked list: `aspirin` (1.0), `warfarin` (0.244898 ± 0.00001), `paracetamol` (0.222222 ± 0.00001), `diclofenac` (0.195652 ± 0.00001), `naproxen` (0.195652 ± 0.00001, tied with `diclofenac`, ordered after it by the ascending-name tie-break). A query of the exact ibuprofen SMILES, at the default `k=5`, returns exactly: `ibuprofen` (1.0), `naproxen` (0.4 ± 0.00001), `warfarin` (0.215686 ± 0.00001), `cetirizine` (0.196429 ± 0.00001), `metoprolol` (0.196078 ± 0.00001).
Constraints: Fingerprints are computed as `AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)` (or the equivalent non-deprecated RDKit `MorganGenerator` API producing identical bit vectors), using RDKit's default `useChirality=False`/`useFeatures=False` invariants; Tanimoto similarity is `c / (a + b - c)` for bit counts `a`, `b` of the two fingerprints and `c` of their intersection. `k` must be an integer in `[1, 20]`; a request with `k` outside this range is rejected under REQ-ACHEM-003, naming the `k` parameter and the constraint "must be an integer in [1, 20]".

## REQ-ACHEM-050: Simplified docking-score heuristic / 簡易ドッキングスコア・ヒューリスティック
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests a docking score for a ligand SMILES against a pocket specification, the system shall report a heuristic docking score in the closed interval 0 to 1 for that ligand-pocket pair.
Acceptance: For aspirin (13 heavy atoms → `ligand_volume = 195.0`; NumHDonors = 1, NumHAcceptors = 3) against a pocket spec `{pocket_volume_A3: 200.0, pocket_hba_sites: 2, pocket_hbd_sites: 1}`: `size_fit = 1 - abs(195.0 - 200.0) / 200.0 = 0.975`, `matched_pairs = min(1, 2) + min(3, 1) = 2`, `hbond_fit = 2 / max(1, 1 + 3) = 0.5`, `score = 0.5*0.975 + 0.5*0.5 = 0.7375`, each within `1e-9` absolute tolerance. A `pocket_volume_A3 <= 0` request is rejected naming `pocket_volume_A3` and the constraint "must be > 0" before any score computation.
Constraints: The pocket specification is `pocket_volume_A3` (must be a finite number `> 0`), `pocket_hba_sites`, and `pocket_hbd_sites` (each must be a finite non-negative integer), enforced under REQ-ACHEM-003. `ligand_volume = heavy_atom_count * 15.0` (Å³, a fixed documented per-heavy-atom constant); `size_fit = clip(1 - abs(ligand_volume - pocket_volume_A3) / pocket_volume_A3, 0, 1)`; `matched_pairs = min(ligand_hbd, pocket_hba_sites) + min(ligand_hba, pocket_hbd_sites)`; `hbond_fit = matched_pairs / max(1, ligand_hbd + ligand_hba)`; `score = 0.5 * size_fit + 0.5 * hbond_fit`. A higher score denotes better heuristic geometric/polar complementarity only; this is an explicitly-labeled heuristic, not a physically accurate docking simulation (no 3D conformer generation, no energy function), and the limitation label is part of the module's output and of SKILL.md documentation.

## REQ-ACHEM-060: Drug-likeness rule screening beyond Lipinski/Veber / Lipinski/Veber以外の薬物らしさルールスクリーニング
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests drug-likeness rule screening for a SMILES string, the system shall report `aromatic_ring_count`, `mol_mr`, `heavy_atom_count`, a Ghose-filter outcome (`ghose_pass`: true iff all of `160 <= MolWt <= 480`, `-0.4 <= MolLogP <= 5.6`, `40 <= MolMR <= 130`, and `20 <= heavy_atom_count <= 70` hold; `ghose_violations` naming every violated criterion in the fixed check order `MolWt`, `MolLogP`, `MolMR`, `heavy_atom_count`), and an Egan-filter outcome (`egan_pass`: true iff both `TPSA <= 131.6` and `MolLogP <= 5.88` hold; `egan_violations` naming every violated criterion in the fixed check order `TPSA`, `MolLogP`), where all of those outputs are computed from the REQ-ACHEM-010 descriptors together with aromatic ring count (`rdMolDescriptors.CalcNumAromaticRings`), molar refractivity (`Descriptors.MolMR`), and heavy-atom count (`mol.GetNumHeavyAtoms()`).
Acceptance: For aspirin (`"CC(=O)OC1=CC=CC=C1C(=O)O"`), RDKit computes `aromatic_ring_count = 1`, `mol_mr = 44.7103 ± 0.0001` (full-precision `44.71030000000002`), and `heavy_atom_count = 13`; therefore `ghose_violations = ["heavy_atom_count"]`, `ghose_pass = false`, `egan_violations = []`, and `egan_pass = true`. For ethanol (`"CCO"`), RDKit computes `aromatic_ring_count = 0`, `mol_mr = 12.7598 ± 0.0001`, and `heavy_atom_count = 3`; therefore `ghose_violations = ["MolWt", "MolMR", "heavy_atom_count"]`, `ghose_pass = false`, `egan_violations = []`, and `egan_pass = true`. The violation-name lists for both filters are emitted only in their documented fixed criterion-check order. All floating-point fixture values in this Acceptance are compared within `1e-4` absolute tolerance (4-decimal presentation); the recorded `result` itself preserves full floating-point precision per REQ-ACHEM-004 (compared there within `1e-9` absolute tolerance), with no intentional output rounding.
Constraints: This module extends REQ-ACHEM-020 with two additional fixed-threshold rule outcomes, Ghose and Egan, computed from descriptors that may overlap with those used by Lipinski/Veber (e.g. MolWt, MolLogP, TPSA); it reports only the Ghose and Egan pass/violation outcomes and does not re-report the Lipinski or Veber pass/violation outcomes already reported by REQ-ACHEM-020. Validation remains atomic per REQ-ACHEM-003: a request whose `smiles` parameter does not parse to a valid RDKit molecule is rejected before any descriptor or rule computation. Ghose and Egan are deterministic fixed-threshold rule screens over the computed descriptor values; no external data, no stochastic step, and no network call are involved.

## REQ-ACHEM-070: Structural alert (PAINS-like) screening / 構造アラート(PAINS風)スクリーニング
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests structural alert screening for a SMILES string, the system shall report `alerts_matched` as the list of matched alert names in the fixed alert-definition order given here, with non-matching alert names omitted, and `alert_count` as its length, where matching is evaluated against exactly this fixed named SMARTS alert list on the parsed molecule: `nitro_group: [NX3](=O)=O`, `aldehyde: [CX3H1](=O)`, `michael_acceptor_enone: C=CC(=O)`, `epoxide: C1OC1`, and `free_thiol: [SX2H]`.
Acceptance: Each of the 5 SMARTS strings in this requirement parses successfully with RDKit's `Chem.MolFromSmarts` (returns non-`None`). For the alert-rich fixture molecule `"O=CC=CC(=O)C1OC1"`, RDKit substructure matching yields `alerts_matched = ["aldehyde", "michael_acceptor_enone", "epoxide"]` and `alert_count = 3`. For aspirin (`"CC(=O)OC1=CC=CC=C1C(=O)O"`), RDKit substructure matching against the same 5 SMARTS yields `alerts_matched = []` and `alert_count = 0`.
Constraints: Validation remains atomic per REQ-ACHEM-003: a request whose `smiles` parameter does not parse to a valid RDKit molecule is rejected before any SMARTS matching. This is an explicitly-labeled heuristic only: "Heuristic only: a small fixed illustrative SMARTS alert list, not the validated PAINS/Brenk filter catalog." / 「ヒューリスティックのみ: 固定の小規模な例示用SMARTSアラート一覧であり、検証済みのPAINS/Brenkフィルタ・カタログではない。」 The limitation label is part of the module's output and of SKILL.md documentation.

## REQ-ACHEM-080: Molecular formula and exact mass / 分子式・正確質量
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests molecular formula and exact mass for a SMILES string, the system shall parse the SMILES and record a `result` containing exactly `{molecular_formula, exact_mass}` within the REQ-ACHEM-004 `RunRecord` envelope (`metadata`/`parameters`/`result`), where `molecular_formula = rdMolDescriptors.CalcMolFormula(mol)` and `exact_mass = Descriptors.ExactMolWt(mol)`.
Acceptance: For aspirin (`"CC(=O)OC1=CC=CC=C1C(=O)O"`), RDKit returns `molecular_formula = "C9H8O4"` and `exact_mass = 180.0423 ± 0.0001` (from executed output `180.042258736`, rounded to 4 decimal places for this acceptance fixture).
Constraints: Validation remains atomic per REQ-ACHEM-003: a request whose `smiles` parameter does not parse to a valid RDKit molecule is rejected before any formula or mass computation. Determinism and run-evidence behavior are exactly those of REQ-ACHEM-004; this module introduces no additional metadata fields beyond the existing `rdkit_version` requirement.

## REQ-ACHEM-090: Heuristic target-class activity classification / 標的クラス活性ヒューリスティック分類
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests target-class activity classification for a SMILES string, the system shall report `{label, tpsa, mol_logp, mol_wt, aromatic_ring_count}`, where `tpsa`, `mol_logp`, and `mol_wt` are the REQ-ACHEM-010 descriptors, `aromatic_ring_count = rdMolDescriptors.CalcNumAromaticRings(mol)`, and `label` is assigned by this fixed decision order: first `"CNS_like"` iff `TPSA < 90` and `2.0 <= MolLogP <= 5.0`; if that test fails, then `"kinase_inhibitor_like"` iff `MolWt > 400` and `aromatic_ring_count >= 3`; otherwise `"other"`.
Acceptance: For diazepam (`"CN1C(=O)CN=C(c2ccccc2)c2cc(Cl)ccc21"`), RDKit computes `tpsa = 32.67 ± 0.0001`, `mol_logp = 3.1538 ± 0.0001` (full-precision `3.1538000000000025`), `mol_wt = 284.746 ± 0.001`, and `aromatic_ring_count = 2`, so the label is exactly `"CNS_like"`. For nilotinib (`"CC1=C(C=C(C=C1)NC(=O)C2=CC(=CC(=C2)N3CCN(CC3)C)C(F)(F)F)NC4=NC=NC(=N4)C5=CN=CC=C5"`), RDKit computes `tpsa = 99.17 ± 0.0001`, `mol_logp = 5.00852 ± 0.0001`, `mol_wt = 548.573 ± 0.001`, and `aromatic_ring_count = 4`, so it fails the first (`"CNS_like"`) branch and is classified exactly as `"kinase_inhibitor_like"`. For aspirin (`"CC(=O)OC1=CC=CC=C1C(=O)O"`), RDKit computes `tpsa = 63.60 ± 0.0001`, `mol_logp = 1.3101 ± 0.0001`, `mol_wt = 180.159 ± 0.001`, and `aromatic_ring_count = 1`, so the label is exactly `"other"`. All floating-point fixture values in this Acceptance are compared within the stated decimal-place tolerance (presentation rounding only); the recorded `result` preserves full floating-point precision per REQ-ACHEM-004 (compared there within `1e-9` absolute tolerance), with no intentional output rounding.
Constraints: Validation remains atomic per REQ-ACHEM-003: a request whose `smiles` parameter does not parse to a valid RDKit molecule is rejected before any descriptor or classification computation. This is an explicitly-labeled heuristic only: "Heuristic only: not a ChEMBL-trained or experimentally validated bioactivity classifier." / 「ヒューリスティックのみ: ChEMBLで学習済みでも実験的に検証済みでもない生物活性分類器ではない。」 The fixed decision order (`"CNS_like"` first, `"kinase_inhibitor_like"` second, `"other"` last) is part of the observable behavior and shall not be reordered.

## REQ-ACHEM-100: SMILES salt removal / structure standardization / SMILES塩除去・構造標準化
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests salt removal/structure standardization for a SMILES string, the system shall report `{standardized_smiles, removed_fragments, fragments_removed}` for it, where RDKit splits the string into its disconnected fragments (`Chem.GetMolFrags(mol, asMols=True, sanitizeFrags=False)`), `standardized_smiles` is the canonical SMILES of the fragment ranked first by the sort key `(-heavy_atom_count, canonical_smiles)` (i.e. greatest heavy-atom count, ties broken by ascending canonical SMILES), `removed_fragments` is the canonical SMILES of every other fragment ordered by that same sort key ascending, and `fragments_removed` is `true` iff the input had more than 1 fragment.
Acceptance: For `"CC(=O)O.CCN"` (acetic acid + ethylamine, heavy-atom counts 4 and 3): `standardized_smiles = "CC(=O)O"`, `removed_fragments = ["CCN"]`, `fragments_removed = true`. For `"[Na+].[Cl-]"` (both 1 heavy atom, tied): `standardized_smiles = "[Cl-]"` (ascending canonical-SMILES tie-break: `"[Cl-]" < "[Na+]"`), `removed_fragments = ["[Na+]"]`, `fragments_removed = true`. For `"CCO"` (single fragment, no salt): `standardized_smiles = "CCO"`, `removed_fragments = []`, `fragments_removed = false`. For `"O.CC(=O)O.O"` (acetic acid plus 2 water fragments, each 1 heavy atom): `standardized_smiles = "CC(=O)O"`, `removed_fragments = ["O", "O"]` (sort key ties on both count and canonical SMILES; either input occurrence order is acceptable among exact duplicates), `fragments_removed = true`. The empty string `""` and the dummy-atom SMILES `"*"` are each rejected under the Constraints below (not computed) with no `standardized_smiles` result.
Constraints: `smiles` validation uses exactly the same chemical-validity domain as every other module in this skill (the shared `parse_smiles` domain already used by REQ-ACHEM-010/080/090 and others): the empty string, a string that fails `Chem.MolFromSmiles`, and a string that parses but contains any dummy/query atom (RDKit atomic number 0, e.g. `"*"`) are each rejected under REQ-ACHEM-003, naming `smiles` and the constraint "must parse to a valid RDKit molecule", before any fragment splitting or selection. This fragment-selection rule (sort key `(-heavy_atom_count, canonical_smiles)`) is a fixed, documented, deterministic rule — not RDKit's built-in `rdMolStandardize.LargestFragmentChooser` default heuristic, whose internal fragment-scoring/tie-break behavior this requirement does not rely on. No network call, no external salt/solvent lookup table; this module heuristically treats "every disconnected fragment except the one ranked first by the sort key" as removable salt/solvent, which is not always chemically correct (e.g. for a genuine covalent multi-component cocrystal) — this is an explicitly-labeled heuristic, and the limitation label is part of the module's output and of SKILL.md documentation.

## REQ-ACHEM-110: Chemical structure format conversion / 化学構造フォーマット変換
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests structure format conversion, the system shall report `{output_format, output_value}` for it, where the request supplies `input_format` (one of `smiles`, `inchi`, `molblock`), `input_value`, and `output_format` (one of `smiles`, `inchi`, `inchikey`, `molblock`); RDKit parses `input_value` per `input_format` (`Chem.MolFromSmiles` for `smiles`, `Chem.inchi.MolFromInchi` for `inchi`, `Chem.MolFromMolBlock` for `molblock`) and renders `output_value` from the parsed molecule per `output_format` (`Chem.MolToSmiles` for `smiles`, `Chem.inchi.MolToInchi` for `inchi`, `Chem.inchi.MolToInchiKey` for `inchikey`, `Chem.MolToMolBlock` for `molblock`).
Acceptance: For aspirin (`input_format="smiles"`, `input_value="CC(=O)OC1=CC=CC=C1C(=O)O"`): `output_format="smiles"` yields `output_value="CC(=O)Oc1ccccc1C(=O)O"`; `output_format="inchi"` yields `output_value="InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)"`; `output_format="inchikey"` yields `output_value="BSYNRYMUTXBXSQ-UHFFFAOYSA-N"`. Converting that same InChI string back (`input_format="inchi"`, `output_format="smiles"`) yields `output_value="CC(=O)Oc1ccccc1C(=O)O"` (the same canonical SMILES, confirming canonical structural round-trip equivalence for this fixture — not a general guarantee that every format pair is lossless, since e.g. a Molblock's 2D/3D coordinates have no SMILES/InChI equivalent). For the fixed ethanol Molblock fixture (`input_format="molblock"`, `input_value` equal to the exact literal text `"\n     RDKit          2D\n\n  3  2  0  0  0  0  0  0  0  0999 V2000\n    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0\n    1.2990    0.7500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0\n    2.5981   -0.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0\n  1  2  1  0\n  2  3  1  0\nM  END\n"` using `\n` for line breaks), `output_format="smiles"` yields `output_value="CCO"`. The empty string `""`, a malformed value for the stated `input_format`, an `input_format`/`output_format` value outside the documented allowed sets (e.g. `input_format="inchikey"`), and a value that parses but contains any dummy/query atom (RDKit atomic number 0, e.g. `input_format="smiles"`, `input_value="*"`) are each rejected under the Constraints below (not converted).
Constraints: Validation remains atomic per REQ-ACHEM-003: `input_format` and `output_format` must each be one of their respective documented allowed values (rejected naming `input_format`/`output_format` and the constraint "must be one of the supported formats" otherwise); `input_value` must parse successfully with the `input_format`-matching RDKit parser into a non-empty molecule containing no dummy/query atom (RDKit atomic number 0) — the same chemical-validity domain as REQ-ACHEM-100 and every other module in this skill — (rejected naming `input_value` and the constraint "must parse with the <input_format>-matching RDKit parser" otherwise); both checks run, in that order, before any format conversion. `"inchikey"` is accepted only as an `output_format` (it is a one-way hash with no RDKit parser back to a molecule), never as an `input_format`. This module performs deterministic representation conversion only; it does not promise bytewise, metadata, or coordinate preservation across formats that do not share that information (e.g. SMILES/InChI carry no 2D/3D coordinates). No network call; no PubChem/ChEMBL/DrugBank lookup of any kind — this module performs only local RDKit format parsing/rendering.

## REQ-ACHEM-120: Dose-response curve fitting / 用量反応曲線フィッティング
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests dose-response (concentration-response) curve fitting for paired `concentrations` and `responses` arrays, the system shall fit the four-parameter logistic (Hill) model `response = bottom + (top - bottom) / (1 + (concentration / ic50) ** hill_slope)` to the data via nonlinear least squares (`scipy.optimize.curve_fit`, initial guess `p0 = [max(responses), min(responses), median(concentrations), 1.0]`, `maxfev=10000`) and report `{top, bottom, ic50, hill_slope, r_squared}`, where `r_squared = 1 - sum((responses - predicted) ** 2) / sum((responses - mean(responses)) ** 2)`.
Acceptance: For `concentrations = [0.001, 0.01, 0.1, 1.0, 10.0, 100.0]` and `responses` generated exactly from `top=100.0`, `bottom=0.0`, `ic50=1.0`, `hill_slope=1.0` (`responses = [99.90009990009992, 99.00990099009901, 90.9090909090909, 50.0, 9.090909090909092, 0.9900990099009901]`), the fitted result has `top`, `bottom`, `ic50`, and `hill_slope` each within absolute tolerance `1e-3` of `100.0`, `0.0`, `1.0`, and `1.0` respectively, and `r_squared >= 0.999999`. A request with fewer than 4 points, any non-finite value, any `concentrations` entry `<= 0`, or `len(concentrations) != len(responses)` is rejected before any fit is attempted, naming the offending parameter and its constraint. A request where every `responses` value is identical, or where every `concentrations` value is identical, is additionally rejected before any fit is attempted, naming `responses`/`concentrations` and the constraint "must contain at least 2 distinct values". A request for which `scipy.optimize.curve_fit` raises (fails to converge within `maxfev`) is rejected with `ValueError` naming `concentrations`/`responses` and the constraint "fit did not converge", without returning a result object; a fit that does converge but yields a non-finite `top`/`bottom`/`ic50`/`hill_slope`, or a finite `ic50 <= 0`, is rejected identically, naming the constraint "fitted parameters must be finite with ic50 > 0".
Constraints: `concentrations` must be a list of finite floats, all `> 0`, length `>= 4`, containing at least 2 distinct values; `responses` must be a list of finite floats of the same length as `concentrations`, containing at least 2 distinct values (rejected naming `concentrations`/`responses` and the constraint "must be a list of finite floats", "length must match concentrations and be >= 4", or "must contain at least 2 distinct values" as applicable). A `curve_fit` convergence failure, or a converged-but-nonphysical result (non-finite fitted parameter, or `ic50 <= 0`), is rejected per Acceptance rather than returned as a partial or nonphysical result. This is a standard 4-parameter logistic regression over user-supplied numeric data only — no external database lookup, no network call, and no assay-specific correction (e.g. no background subtraction); the module reports the fitted curve parameters only.

## REQ-ACHEM-130: Pharmacokinetic non-compartmental analysis / 薬物動態ノンコンパートメント解析
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests pharmacokinetic (PK) non-compartmental analysis for paired `times` and `concentrations` arrays plus a `dose`, the system shall compute `cmax = max(concentrations)`, `tmax = times[argmax(concentrations)]` (the first/lowest index attaining the maximum when tied), `auc_last` via the linear trapezoidal rule over all `(times, concentrations)` pairs, the terminal elimination rate constant `k_el = -slope` of an ordinary-least-squares fit of `ln(concentrations)` against `times` over the last `n_terminal` points (default `3`), `half_life = ln(2) / k_el`, `auc_inf = auc_last + concentrations[-1] / k_el`, `clearance = dose / auc_inf`, and `volume_of_distribution = clearance / k_el`, reporting `{cmax, tmax, auc_last, auc_inf, k_el, half_life, clearance, volume_of_distribution}`.
Acceptance: For `times = [0.5, 1.0, 2.0, 4.0, 8.0, 12.0]`, `concentrations = [45.241870901797974, 40.936537653899094, 33.51600230178197, 22.466448205861077, 10.094825899732768, 4.535897664470624]` (an exact `C0=50.0, k=0.2` exponential decay), `dose = 500.0`, and `n_terminal = 3` (default), the reported result is `cmax = 45.241870901797974`, `tmax = 0.5`, `auc_last = 209.13731796400234`, `k_el = 0.2` (within `1e-6`), `half_life = 3.465735902799724`, `auc_inf = 231.81680628635544`, `clearance = 2.156875543278631`, and `volume_of_distribution = 10.784377716393147`, each float field within absolute tolerance `1e-6`. A request with fewer than 4 points, non-strictly-increasing `times`, any non-finite or non-positive `concentrations` value, `dose <= 0`, or `n_terminal` outside `[2, len(times)]` is rejected before any computation, naming the offending parameter and its constraint. A request whose terminal-slope fit yields a non-finite `k_el` or `k_el <= 0` (e.g. the last `n_terminal` `concentrations` are flat or increasing) is rejected with `ValueError` naming `concentrations`/`n_terminal` and the constraint "terminal concentrations must yield a positive elimination rate constant", without returning a result object.
Constraints: `times` must be a list of strictly increasing finite floats, length `>= 4`; `concentrations` must be a list of finite floats `> 0` of the same length as `times`; `dose` must be a finite float `> 0`; `n_terminal` must be an integer in the closed interval `[2, len(times)]` (default `3`). A terminal-slope fit that does not yield a finite `k_el > 0` is rejected per Acceptance rather than propagated into `half_life`/`auc_inf`/`clearance`/`volume_of_distribution` as a non-finite or negative value. This is a standard non-compartmental PK calculation over user-supplied concentration-time data only — no external database lookup, no network call, and no compartmental model fitting (that is a documented limitation, not a design gap).

## REQ-ACHEM-140: Michaelis-Menten enzyme kinetics / Michaelis-Menten酵素反応速度論
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests enzyme kinetics analysis for paired `substrate_concentrations` and `velocities` arrays, the system shall fit the Michaelis-Menten model `velocity = vmax * substrate_concentration / (km + substrate_concentration)` via nonlinear least squares (`scipy.optimize.curve_fit`, initial guess `p0 = [max(velocities), median(substrate_concentrations)]`) and report `{vmax, km, r_squared}`, where `r_squared` is computed identically to REQ-ACHEM-120.
Acceptance: For `substrate_concentrations = [0.5, 1.0, 2.0, 5.0, 10.0, 20.0]` and `velocities` generated exactly from `vmax=10.0`, `km=2.0` (`velocities = [2.0, 3.3333333333333335, 5.0, 7.142857142857143, 8.333333333333334, 9.090909090909092]`), the fitted result has `vmax` and `km` each within absolute tolerance `1e-3` of `10.0` and `2.0` respectively, and `r_squared >= 0.999999`. A request with fewer than 3 points, any non-finite value, any `substrate_concentrations` entry `<= 0`, or `len(substrate_concentrations) != len(velocities)` is rejected before any fit is attempted, naming the offending parameter and its constraint. A request where every `velocities` value is identical, or where every `substrate_concentrations` value is identical, is additionally rejected before any fit is attempted, naming `velocities`/`substrate_concentrations` and the constraint "must contain at least 2 distinct values". A request for which `scipy.optimize.curve_fit` raises (fails to converge) is rejected with `ValueError` naming `substrate_concentrations`/`velocities` and the constraint "fit did not converge", without returning a result object; a fit that does converge but yields a non-finite `vmax`/`km`, or a finite `vmax <= 0` or `km <= 0`, is rejected identically, naming the constraint "fitted parameters must be finite with vmax > 0 and km > 0".
Constraints: `substrate_concentrations` must be a list of finite floats, all `> 0`, length `>= 3`, containing at least 2 distinct values; `velocities` must be a list of finite floats of the same length as `substrate_concentrations`, containing at least 2 distinct values (rejected naming `substrate_concentrations`/`velocities` and the constraint "must be a list of finite floats", "length must match substrate_concentrations and be >= 3", or "must contain at least 2 distinct values" as applicable). A `curve_fit` convergence failure, or a converged-but-nonphysical result (non-finite fitted parameter, `vmax <= 0`, or `km <= 0`), is rejected per Acceptance rather than returned as a partial or nonphysical result. This is a standard 2-parameter Michaelis-Menten regression over user-supplied numeric data only — no external database lookup, no network call, and no substrate-inhibition or cooperativity (Hill) extension; the module reports the fitted `vmax`/`km` only.

## Review record (second increment) / レビュー記録(第2増分)
REQ-ACHEM-060/070/080/090 (this second increment) passed `musubix3
requirements validate` and `musubix3 constitution validate`. An independent
native `rubber-duck` review found 3 issues on the first pass (REQ-ACHEM-080's
result shape conflicting with the REQ-ACHEM-004 `RunRecord` envelope, missing
float tolerances on REQ-ACHEM-060/090 fixtures, and inaccurate
"non-overlapping" wording in REQ-ACHEM-060); all 3 were fixed, and a second
review round plus a final cross-file consistency check confirmed zero
remaining issues. 本増分（REQ-ACHEM-060/070/080/090）は `musubix3 requirements
validate` と `musubix3 constitution validate` に合格した。独立した native
`rubber-duck` レビューは初回パスで 3 件の指摘（REQ-ACHEM-080 の結果形状が
REQ-ACHEM-004 の `RunRecord` エンベロープと矛盾、REQ-ACHEM-060/090
フィクスチャの浮動小数点許容誤差欠落、REQ-ACHEM-060 の「重複なし」という
不正確な記述）を検出し、すべて修正した上で、2 回目のレビューおよび最終
クロスファイル整合性チェックで残存課題ゼロを確認した。

## Review record (third increment) / レビュー記録(第3増分)
REQ-ACHEM-100/110 (this third increment) passed `musubix3 requirements
validate` and `musubix3 constitution validate`. An independent native
`rubber-duck` review found 3 blocking issues on the first pass (missing
empty-SMILES/dummy-atom rejection domain on both new requirements, an
underspecified fragment-ordering tie-break rule, and an overclaimed
"lossless round trip" statement in REQ-ACHEM-110) plus non-blocking issues
(REQ-ACHEM-004's determinism list not yet covering the 2 new modules, and a
tautologically-described rather than literally-embedded Molblock fixture);
all were fixed (dummy-atom/empty-input rejection now reuses the shared
`parse_smiles` domain already used by REQ-ACHEM-010/080/090; the fragment
sort key is now the explicit `(-heavy_atom_count, canonical_smiles)` with a
3-fragment tie fixture added; the round-trip claim was narrowed to
"canonical structural round-trip equivalence for this fixture"; the
ethanol Molblock fixture is now embedded literally; REQ-ACHEM-004's
Constraints now explicitly list fragment selection and format
conversion), and a second review round confirmed zero remaining issues.
本増分（REQ-ACHEM-100/110）は `musubix3 requirements validate` と
`musubix3 constitution validate` に合格した。独立した native `rubber-duck`
レビューは初回パスで 3 件のブロッキング指摘（両新規要求の空SMILES・
ダミー原子拒否ドメインの欠落、フラグメント順序付けのタイブレーク規則の
未規定、REQ-ACHEM-110 の「ロスレスラウンドトリップ」の過大主張）および
非ブロッキング指摘（REQ-ACHEM-004 の決定性一覧が新規2モジュールを
網羅していない点、Molblock フィクスチャが生成方法の説明のみでリテラル
埋め込みでなかった点）を検出し、すべて修正した上で、2回目のレビューで
残存課題ゼロを確認した。

## Review record (fourth increment) / レビュー記録(第4増分)
REQ-ACHEM-120/130/140 (this fourth increment) passed `musubix3 requirements
validate` and `musubix3 constitution validate`. An independent native
`rubber-duck` review found 2 blocking issues on the first pass (REQ-ACHEM-130
allowed a non-positive terminal elimination rate constant `k_el`, making
`half_life`/`auc_inf`/`clearance`/`volume_of_distribution` undefined for
otherwise-valid input; REQ-ACHEM-120/140 permitted degenerate constant-input
data and unhandled `scipy.optimize.curve_fit` convergence failure to produce
undefined or nonphysical fitted-parameter results) plus non-blocking issues
(no explicit domain for a converged-but-nonphysical `ic50<=0` or
`vmax<=0`/`km<=0` fit); all were fixed (REQ-ACHEM-130 now requires a finite
`k_el > 0`, rejecting otherwise with an explicit `ValueError`, and clarifies
`tmax` tie-breaking as first/lowest index; REQ-ACHEM-120/140 now reject
constant-only `responses`/`concentrations` or `velocities`/
`substrate_concentrations` before fitting, and reject both convergence
failure and a converged-but-nonphysical fit with explicit `ValueError`
constraints). A second review pass confirmed zero remaining issues.
