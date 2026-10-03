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

All modules are implemented with RDKit (required dependency) plus
numpy/scikit-learn already present in this repository; no other external
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
Statement: When a user's request text contains one of the module manifest's registered name/synonym strings for a supported method, the system shall dispatch the request to exactly that method's module handler and execute no other module, where the supported methods are molecular-descriptors, admet-prediction, qsar-modeling, molecular-similarity, and docking-score, each with both an English and a Japanese registered name/synonym list in the manifest.
Acceptance: For each of the 5 methods, a fixture request using its registered English name and a separate fixture request using its registered Japanese name each dispatch to exactly that method's handler and no other; a fixture request containing two different methods' registered names yields a clarification question listing both candidates with no module invoked; a fixture request containing none of the registered names yields a rejection message with no module invoked.

## REQ-ACHEM-003: Input and parameter validation / 入力・パラメータ検証
Priority: must
Type: functional
Pattern: unwanted-behavior
Statement: If a requested module's input parameters fail that module's own documented chemical-validity or numerical-adequacy domain, then the system shall reject the run and report which parameter violated which named constraint, before performing any descriptor computation, model fit, or similarity/score calculation.
Acceptance: A single-SMILES request whose `smiles` parameter fails RDKit's `Chem.MolFromSmiles` parse (returns `None`) — for example the malformed string `"C1CC"` (unclosed ring) — is rejected with a message naming the `smiles` parameter and the constraint "must parse to a valid RDKit molecule"; no descriptor, score, or model computation is performed for that run. For a batch-capable module (REQ-ACHEM-010), a multi-SMILES request validates and rejects each input item independently: an invalid item is reported as a per-item rejection naming the `smiles` parameter and the violated constraint, while every other item in the same batch is still computed. The same per-run-or-per-item pattern (reject before computation, name the parameter and constraint) applies to every module's documented domain, including each module-specific domain listed in its own requirement below.
Constraints: This requirement's "chemical-validity or numerical-adequacy domain" is defined per module by REQ-ACHEM-010/020/030/040/050; it does not itself define a single universal validity test applicable across all five modules. Validation granularity is per module: REQ-ACHEM-010 (batch descriptor calculation) validates and rejects each SMILES item independently without aborting the rest of the batch; REQ-ACHEM-020/030/040/050 (single-ligand/model/query modules) validate the whole run atomically and reject the entire run with no partial computation when any parameter is invalid.

## REQ-ACHEM-004: Reproducible run evidence / 再現可能な実行根拠
Priority: must
Type: functional
Pattern: event-driven
Statement: When a module run completes, the system shall record a deterministic result (produced without any random seed) with exactly three top-level keys: `metadata` (a JSON-safe dict containing at least `module`, `schema_version`, and `rdkit_version`), `parameters` (a JSON-safe dict of the resolved input parameters), and `result` (a JSON-safe dict or list of the module's output values).
Acceptance: For each of the 5 modules, two runs with identical `parameters` against the same installed RDKit/scikit-learn versions produce `result` values that compare exactly equal (numeric fields equal via `==` for integers and within `1e-9` absolute tolerance for floats); `metadata.rdkit_version` matches the installed `rdkit.__version__` string, and for the QSAR module (REQ-ACHEM-030) `metadata.scikit_learn_version` matches the installed `sklearn.__version__` string.
Constraints: "Deterministic" means every module's governing computation (RDKit descriptor calculation, scikit-learn `LinearRegression` least-squares fit, fingerprint similarity, or the fixed arithmetic docking-score formula) is a pure function of `parameters` and the installed RDKit/scikit-learn version, with no stochastic step and therefore no seed to record.

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
