---
schemaVersion: 1
feature: ai-genomics-scientist
---
# Design / 設計

Architecture blueprint for the new `ai-genomics-scientist` Copilot Agent
Skill. Mirrors `ai-chemistry-scientist`'s static-manifest dispatch
pattern: a single skill entrypoint loads a checked-in JSON manifest
mapping each method name to one module handler, then dispatches each
request to exactly one module. Every genomics module is a pure Python
implementation using only numpy/scipy plus the standard library; none
uses the network or external bioinformatics libraries such as
Biopython.

## DES-AGENOM-001: Method manifest & request dispatcher / 手法マニフェストと要求振り分け
Responsibilities: Load the static method-name-to-module manifest
(`.github/skills/ai-genomics-scientist/manifest.json`; each entry has
`modulePath`, `functionName`, and bilingual `names.en` / `names.ja`
lists matching REQ-AGENOM-002's fixed routing strings), detect the
request language (`"ja"` or `"en"`), normalize the request text and
every registered name/synonym with Unicode NFKC, perform a
case-insensitive substring match on the normalized forms, collapse
duplicate hits owned by the same method, and dispatch to exactly one
matched handler. On exactly one match, resolve the target
`modulePath`/`functionName` and invoke that handler wrapper with
`(request_text, language)`; on two or more distinct matched methods,
return a clarification question naming every matched candidate and
invoke no module; on no match, return a rejection message and invoke no
module. Each handler wrapper is responsible for extracting its own
structured `params` from `request_text` or accepting already-structured
keyword arguments from a calling context, then invoking DES-AGENOM-002
validation and its module's raw `run_*` function, and finally wrapping
the raw result with DES-AGENOM-003 `record_run`. DES-AGENOM-010 is the
sole per-item-validated module and therefore calls
`validate_batch_item` interleaved with per-sequence computation inside
its own `run_sequence_features`, rather than receiving a single
up-front atomic `validate_parameters` call.
Interfaces: `dispatch(request_text, language=None, manifest_path=None) ->
DispatchResult` where `DispatchResult` is one of
`{outcome: "dispatch", module, language, handler_result}`,
`{outcome: "clarification", candidates, language, clarification_question}`,
or `{outcome: "rejected", language, rejected_method}`. `handler_result`
is always a `ModuleOutcome`: either `{ok: true, run_record}` on
success, or `{ok: false, parameter, constraint, language}` on a module
validation failure. The manifest owns these 7 exact method keys:
`sequence-features`, `variant-effect-annotation`,
`splice-site-strength`, `gene-set-enrichment`,
`pairwise-sequence-alignment`, `differential-expression`, and
`variant-pathogenicity`.
Constraints: Must invoke at most one module per request; must apply
Unicode NFKC normalization before substring matching; must collapse
multiple matched strings that map to the same method before counting
distinct matched methods; and must render every user-facing prose
sentence in the detected request language, allowing only the technical
token exceptions that REQ-AGENOM-001 permits.
Requirements: REQ-AGENOM-001, REQ-AGENOM-002
ADRs: ADR-0033
Depends-On: none

## DES-AGENOM-002: Shared parameter & validity validator / 共通パラメータ・妥当性検証
Responsibilities: Validate each module's resolved input parameters
against that module's documented biological-validity,
alphabet-validity, or numerical-adequacy domain before any invalid
scope produces a result. Supports both validation granularities that
REQ-AGENOM-003 defines: atomic whole-run validation for
REQ-AGENOM-020/030/040/050/060/070, and per-item validation for
REQ-AGENOM-010's batch sequence input. Expose a shared validator
registry so each module registers its own documented validator at import
time.
Interfaces: `register_validator(module_name, validator) -> None`,
`validate_parameters(module_name, params) -> ValidationResult`,
`register_batch_item_validator(module_name, validator) -> None`, and
`validate_batch_item(module_name, item_params) -> ValidationResult`,
where `ValidationResult` is `{ok: true}` or `{ok: false, parameter,
constraint}`. Whole-run validators reject the entire request before any
module result is produced; per-item validators reject only the invalid
batch element while leaving other items computable.
Constraints: The validator registry is keyed by manifest method name.
Atomic validators cover REQ-AGENOM-020/030/040/050/060/070 and must reject the
entire run before any variant annotation, splice scoring,
hypergeometric p-value calculation, or dynamic-programming alignment is
performed. The per-item validator path is reserved for
`sequence-features`, which rejects an invalid `sequence` item with the
exact named constraint "must be a non-empty uppercase DNA string over
{A,C,G,T} with length >= 3" without aborting the rest of the batch.
Requirements: REQ-AGENOM-003, REQ-AGENOM-010, REQ-AGENOM-020, REQ-AGENOM-030, REQ-AGENOM-040, REQ-AGENOM-050, REQ-AGENOM-060, REQ-AGENOM-070
ADRs: ADR-0034
Depends-On: DES-AGENOM-001

## DES-AGENOM-003: Reproducible run-evidence recorder / 実行根拠記録
Responsibilities: Capture every successful module run as a JSON-safe
`RunRecord` with exactly three top-level keys: `metadata`,
`parameters`, and `result`. Called exactly once by each handler wrapper
after module validation succeeds and the raw `run_*` function returns.
The raw results of all 7 genomics modules are already JSON-safe
(scalars, strings, booleans, lists, and nested dicts of these), so no
array codec is needed.
Interfaces: `record_run(module_name, params, result, *, numpy_version,
scipy_version) -> RunRecord` where `RunRecord = {metadata,
parameters, result}` and `metadata` always contains at least `module`,
`schema_version`, `numpy_version`, and `scipy_version`, matching
REQ-AGENOM-004's acceptance that all 7 modules' run records carry
`scipy_version`. Every handler wrapper, including the 5 modules whose
own governing computation does not call any `scipy` function, supplies
the installed `scipy.__version__` string alongside `numpy_version`;
only `gene-set-enrichment`'s computation directly calls
`scipy.stats.hypergeom.sf` and `differential-expression`'s computation
directly calls `scipy.stats.ttest_ind`.
Constraints: Re-running with identical `parameters` against the same
installed numpy/scipy versions must reproduce equal results under
REQ-AGENOM-004's comparison rules; no random seed is recorded because
every module computation is deterministic. `record_run` is never called
on a validation-failure path.
Requirements: REQ-AGENOM-004
ADRs: ADR-0035
Depends-On: DES-AGENOM-001

Note on DES-AGENOM-010 through DES-AGENOM-070 below: each module's
`run_*(...)` function is the raw, unwrapped compute entry point. The 6
atomic-validation modules (DES-AGENOM-020/030/040/050/060/070) are invoked by
their handler wrappers only after DES-AGENOM-002
`validate_parameters(...)` succeeds, so those `run_*` functions receive
only already-validated parameters and perform no revalidation of their
own. DES-AGENOM-010 is the sole exception: its own
`run_sequence_features(...)` performs `validate_batch_item(...)`
interleaved with per-sequence computation to satisfy REQ-AGENOM-003's
per-item batch semantics.

## DES-AGENOM-010: Sequence feature analysis module / 配列特徴量解析モジュール
Responsibilities: For each input DNA `sequence`, validate the item via
`validate_batch_item`, then compute `length`, `gc_content`, the single
longest forward-frame ORF across frames 0, 1, and 2 only, and the
integer-count `codon_usage` dictionary for that longest ORF. ORF
scanning uses only forward frames, requires start codon `ATG`, closes at
the first following in-frame stop codon from `{TAA, TAG, TGA}`, includes
both start and stop codons in the reported ORF length, and applies the
fixed tie-break order of lowest `frame` then lowest `start_index`.
Interfaces: `run_sequence_features(sequences) -> list[SequenceFeatureResult
| RejectedItem]` where `SequenceFeatureResult = {length, gc_content,
longest_orf, codon_usage}` and `longest_orf` is either `null` or
`{frame, start_index, length}`; `RejectedItem = {sequence, ok: false,
parameter: "sequence", constraint}`. The returned list preserves input
order and contains exactly one element per input sequence.
Constraints: Each valid `sequence` must satisfy the exact named
constraint "must be a non-empty uppercase DNA string over {A,C,G,T}
with length >= 3". `length = len(sequence)` and `gc_content =
(count('G') + count('C')) / length`. If no ORF exists, `longest_orf` is
`null` and `codon_usage` is `{}`. This module alone uses per-item
validation and must not abort the rest of a batch because one item is
invalid.
Requirements: REQ-AGENOM-010
ADRs: ADR-0036
Depends-On: DES-AGENOM-001, DES-AGENOM-002, DES-AGENOM-003

## DES-AGENOM-020: Variant effect heuristic annotation module / バリアント効果ヒューリスティック注釈モジュール
Responsibilities: Receive already-validated `ref_codon`, `position`, and
`alt_base`, construct `alt_codon` by substituting `alt_base` at
`position`, translate both codons with the standard genetic code (NCBI
translation table 1), and classify `effect` exactly as
`"synonymous"`, `"nonsense"`, `"missense"`, or `"readthrough"`
according to REQ-AGENOM-020's fixed rules.
Interfaces: `run_variant_effect(ref_codon, position, alt_base) ->
VariantEffectResult` where `VariantEffectResult = {ref_codon, alt_codon,
ref_amino_acid, alt_amino_acid, effect}`.
Constraints: Validation is whole-run and atomic. `ref_codon` must be
exactly 3 uppercase DNA bases, `position` must be an integer in
`{0,1,2}`, and `alt_base` must be exactly 1 uppercase DNA base distinct
from `ref_codon[position]`; when `alt_base == ref_codon[position]`, the
request is rejected naming `alt_base` and the exact constraint "alt_base
must differ from the reference base at position". If `ref_codon` is a
stop codon, the request is rejected unless `alt_codon` translates to a
non-stop amino acid, naming `ref_codon` and the exact constraint
"stop-reference codons must mutate to a non-stop codon".
Requirements: REQ-AGENOM-020
ADRs: ADR-0037
Depends-On: DES-AGENOM-001, DES-AGENOM-002, DES-AGENOM-003

## DES-AGENOM-030: Splice-site strength heuristic module / スプライス部位強度ヒューリスティックモジュール
Responsibilities: Receive an already-validated 9-base `window` spanning
positions `-3..+5` around a candidate 5' donor site, require the
canonical `GT` dinucleotide at positions `0,+1`, and compute
`score_bits = sum(log2(freq(base_at_position, position) / 0.25))` over
all 9 positions using the fixed illustrative PFM from REQ-AGENOM-030:
`pos -3: A=0.30 C=0.20 G=0.25 T=0.25; pos -2: A=0.60 C=0.15 G=0.15
T=0.10; pos -1: A=0.15 C=0.15 G=0.60 T=0.10; pos 0: A=0.00 C=0.00
G=1.00 T=0.00; pos +1: A=0.00 C=0.00 G=0.00 T=1.00; pos +2: A=0.55
C=0.05 G=0.35 T=0.05; pos +3: A=0.70 C=0.10 G=0.10 T=0.10; pos +4:
A=0.08 C=0.05 G=0.80 T=0.07; pos +5: A=0.15 C=0.20 G=0.20 T=0.45`.
Interfaces: `run_splice_site_scoring(window) -> SpliceSiteResult` where
`SpliceSiteResult = {window, score_bits, canonical_site}` and
`canonical_site` is always `true` for a successful result.
Constraints: Validation is whole-run and atomic. `window` must satisfy
the exact named constraint "must be a non-empty uppercase DNA string
over {A,C,G,T}" plus the module-specific constraint of exactly 9
characters, and `window[3:5] == "GT"` (positions `0,+1`) before any
score computation; when that dinucleotide check fails, the request is
rejected naming `window` and the exact constraint "position 0,+1 must
be the canonical GT dinucleotide".
Canonical positions `0` and `+1` therefore always contribute
`log2(1.00 / 0.25) = 2.0` bits each after validation. Heuristic
limitation label text is fixed verbatim for documentation and user
guidance: English `"Heuristic only: a fixed illustrative position-weight
scoring scheme, not a validated splice-site predictor (not SpliceAI,
not based on real splice-site frequency data)."` and Japanese
`"ヒューリスティックのみ：これは固定された例示用の
position-weight スコアリング方式であり、検証済みのスプライス
部位予測器ではない（SpliceAI ではなく、実際のスプライス部位
頻度データにも基づかない）。"`; this text is documentation-level
guidance and does not add a new output field beyond
`{window, score_bits, canonical_site}`.
Requirements: REQ-AGENOM-030
ADRs: ADR-0038
Depends-On: DES-AGENOM-001, DES-AGENOM-002, DES-AGENOM-003

## DES-AGENOM-040: Gene-set enrichment heuristic module / 遺伝子セットエンリッチメント解析モジュール
Responsibilities: Receive already-validated `query_genes`, load the
bundled toy pathway dataset from
`src/ai_genomics_scientist/data/sample_gene_sets.csv`, compute
`background_size = 50`, `query_size = len(query_genes)`, `overlap =
|query_genes ∩ pathway_genes|`, and `p_value =
scipy.stats.hypergeom.sf(overlap - 1, background_size, pathway_size,
query_size)` for each of the 5 bundled pathways, then return the exact
5-entry result list sorted by ascending `p_value` and, on ties, by
ascending `pathway`.
Interfaces: `run_gene_set_enrichment(query_genes) ->
list[GeneSetEnrichmentResult]` where `GeneSetEnrichmentResult =
{pathway, overlap, pathway_size, p_value}` and the returned list always
has length 5.
Constraints: Validation is whole-run and atomic. `query_genes` must be
deduplicated, non-empty, and every gene symbol must belong to the fixed
toy universe `GENE01` through `GENE50`; a duplicate entry is rejected
naming `query_genes` and the exact constraint "must be deduplicated", an
empty list is rejected naming `query_genes` and the exact constraint
"must be non-empty", and an out-of-universe symbol is rejected by
naming `query_genes` and listing each invalid symbol. The module is a
toy statistical heuristic over a fixed toy universe, not a claim of
biological pathway validity and not an Enrichr reimplementation. The
bundled CSV content is fixed exactly as follows:

| pathway | genes |
| --- | --- |
| `cell_cycle` | `GENE01;GENE02;GENE03;GENE04;GENE05;GENE06;GENE07;GENE08` |
| `dna_repair` | `GENE05;GENE06;GENE07;GENE08;GENE09;GENE10;GENE11;GENE12` |
| `apoptosis` | `GENE13;GENE14;GENE15;GENE16;GENE17;GENE18` |
| `immune_response` | `GENE19;GENE20;GENE21;GENE22;GENE23;GENE24;GENE25;GENE26;GENE27` |
| `metabolism` | `GENE28;GENE29;GENE30;GENE31;GENE32;GENE33;GENE34;GENE35;GENE36;GENE37` |

Requirements: REQ-AGENOM-040
ADRs: ADR-0039
Depends-On: DES-AGENOM-001, DES-AGENOM-002, DES-AGENOM-003

## DES-AGENOM-050: Pairwise sequence alignment module / ペアワイズ配列アラインメントモジュール
Responsibilities: Receive already-validated DNA strings `seq1` and
`seq2`, build the full Needleman-Wunsch dynamic-programming matrix using
fixed scoring `match = +1`, `mismatch = -1`, and `gap = -2` per gap
character, perform traceback with globally fixed tie-break order
diagonal over up over left, and report the final aligned sequences,
alignment score, and identity fraction.
Interfaces: `run_sequence_alignment(seq1, seq2) -> AlignmentResult`
where `AlignmentResult = {aligned_seq1, aligned_seq2, score, identity}`
and `identity = (# aligned positions where both characters are equal and
neither is a gap) / (alignment length)`.
Constraints: Validation is whole-run and atomic. Both `seq1` and `seq2`
must satisfy the exact named constraint "must be a non-empty uppercase
DNA string over {A,C,G,T}" before a DP matrix cell is filled. The
traceback tie-break order is fixed globally as diagonal, then up, then
left.
Requirements: REQ-AGENOM-050
ADRs: ADR-0040
Depends-On: DES-AGENOM-001, DES-AGENOM-002, DES-AGENOM-003

## DES-AGENOM-060: Differential expression heuristic module / 差次発現解析ヒューリスティックモジュール
Responsibilities: Receive already-validated `counts` and
`sample_groups`, compute per-sample DESeq2-style median-of-ratios size
factors (geometric mean per gene across all samples as reference,
excluding any gene with a zero count in any sample from that
geometric-mean reference set, per-sample median of the
raw-count-to-gene-geometric-mean ratio over genes with a defined
nonzero reference), normalize every gene's counts by its sample's size
factor, compute
`base_mean` (mean normalized count across all samples), compute
`log2_fold_change = log2((mean_normalized_group2 + 1) /
(mean_normalized_group1 + 1))` with group order fixed as
`sorted(set(sample_groups))`, compute `p_value` via Welch's two-sample
t-test (`scipy.stats.ttest_ind(..., equal_var=False)`) on
`log2(normalized_count + 1)` values between the two groups (defining
`p_value = 1.0` instead of `NaN`, as a deliberate deterministic
heuristic convention rather than a claim of provably equal means, only
for the specific degenerate case where **both** groups have zero
variance in `log2(normalized_count + 1)` for that gene; a one-sided
zero-variance gene still runs the ordinary Welch's t-test per
ADR-0107), and Benjamini-Hochberg `padj` across all genes in the run,
then return exactly one result object per gene sorted by ascending
`padj` then ascending `gene_id`.
Interfaces: `run_differential_expression(counts, sample_groups) ->
list[DifferentialExpressionResult]` where
`DifferentialExpressionResult = {gene_id, base_mean, log2_fold_change,
p_value, padj}` and the returned list has exactly one entry per gene in
`counts`, in no case omitting or duplicating a gene.
Constraints: Validation is whole-run and atomic, per REQ-AGENOM-003's
module-specific granularity rule. `counts` must be a non-empty dict
whose keys are gene-ID strings and whose values are equal-length lists
of non-negative integers, each list's length must equal exactly
`len(sample_groups)`; `sample_groups` must contain exactly 2 distinct
string labels, each appearing at least twice (at least 2 replicate
samples per group); and at least one gene must have strictly positive
counts in every sample (the median-of-ratios reference-gene
precondition) before any size factor is computed. The
Benjamini-Hochberg correction is implemented in pure numpy (rank-based
step-up procedure, monotone non-decreasing from the largest p-value
down), matching ADR-0107's decision not to add a `statsmodels`
dependency.
Requirements: REQ-AGENOM-060
ADRs: ADR-0107
Depends-On: DES-AGENOM-001, DES-AGENOM-002, DES-AGENOM-003

## DES-AGENOM-070: Variant pathogenicity heuristic module / バリアント病原性予測ヒューリスティックモジュール
Responsibilities: Receive already-validated `ref_aa`, `alt_aa`,
`conservation_score`, and `in_functional_domain`, look up `blosum_score`
from a single embedded, hardcoded BLOSUM62 substitution matrix, compute
`dissimilarity = clip((3 - blosum_score) / 7, 0, 1)`, compute
`pathogenicity_score = clip(0.5 * dissimilarity + 0.35 *
conservation_score + (0.15 if in_functional_domain else 0.0), 0, 1)`,
classify the result into exactly one of the 5 fixed tiers (`benign` for
`score < 0.3`, `likely_benign` for `0.3 <= score < 0.5`,
`uncertain_significance` for `0.5 <= score < 0.7`, `likely_pathogenic`
for `0.7 <= score < 0.85`, `pathogenic` for `score >= 0.85`; every
tier boundary is lower-inclusive per ADR-0108), and report exactly the
keys `{ref_aa, alt_aa, blosum_score, pathogenicity_score,
classification}` with no `dissimilarity` key or any other key present.
Interfaces: `run_variant_pathogenicity(ref_aa, alt_aa,
conservation_score, in_functional_domain) ->
VariantPathogenicityResult` where `VariantPathogenicityResult =
{ref_aa, alt_aa, blosum_score, pathogenicity_score, classification}`.
Constraints: Validation is whole-run and atomic. `ref_aa` and `alt_aa`
must each be one of the 20 standard single-letter amino acid codes,
`alt_aa` must differ from `ref_aa`, `conservation_score` must be a
float in the closed interval `[0, 1]`, and `in_functional_domain` must
be a boolean; a non-boolean `in_functional_domain` is rejected naming
`in_functional_domain` and the exact constraint "must be a boolean".
The embedded BLOSUM62 matrix and the 3 fixed weights (`0.5`, `0.35`,
`0.15`) are frozen constants per ADR-0108; this module never calls a
network service or loads an external scoring model.
Requirements: REQ-AGENOM-070
ADRs: ADR-0108
Depends-On: DES-AGENOM-001, DES-AGENOM-002, DES-AGENOM-003

## Implementation file layout / 実装ファイル配置

The first implementation increment will create exactly this package
layout under `src/ai_genomics_scientist/`:

- `src/ai_genomics_scientist/__init__.py`
- `src/ai_genomics_scientist/dispatch.py`
- `src/ai_genomics_scientist/evidence.py`
- `src/ai_genomics_scientist/validation.py`
- `src/ai_genomics_scientist/sequence_features.py`
- `src/ai_genomics_scientist/variant_effect.py`
- `src/ai_genomics_scientist/splice_site_scoring.py`
- `src/ai_genomics_scientist/gene_set_enrichment.py`
- `src/ai_genomics_scientist/sequence_alignment.py`
- `src/ai_genomics_scientist/differential_expression.py`
- `src/ai_genomics_scientist/variant_pathogenicity.py`
- `src/ai_genomics_scientist/data/sample_gene_sets.csv`

## Traceability summary / 追跡可能性一覧

| Design component | Requirement(s) | ADR |
| --- | --- | --- |
| DES-AGENOM-001 | REQ-AGENOM-001, REQ-AGENOM-002 | ADR-0033 |
| DES-AGENOM-002 | REQ-AGENOM-003, REQ-AGENOM-010, REQ-AGENOM-020, REQ-AGENOM-030, REQ-AGENOM-040, REQ-AGENOM-050, REQ-AGENOM-060, REQ-AGENOM-070 | ADR-0034 |
| DES-AGENOM-003 | REQ-AGENOM-004 | ADR-0035 |
| DES-AGENOM-010 | REQ-AGENOM-010 | ADR-0036 |
| DES-AGENOM-020 | REQ-AGENOM-020 | ADR-0037 |
| DES-AGENOM-030 | REQ-AGENOM-030 | ADR-0038 |
| DES-AGENOM-040 | REQ-AGENOM-040 | ADR-0039 |
| DES-AGENOM-050 | REQ-AGENOM-050 | ADR-0040 |
| DES-AGENOM-060 | REQ-AGENOM-060 | ADR-0107 |
| DES-AGENOM-070 | REQ-AGENOM-070 | ADR-0108 |
| DES-AGENOM-080 | REQ-AGENOM-080 | ADR-0113 |

## Skill documentation deliverables / スキル文書成果物

`.github/skills/ai-genomics-scientist/manifest.json` and
`.github/skills/ai-genomics-scientist/SKILL.md` are required
implementation deliverables alongside the `src/ai_genomics_scientist/`
package. `SKILL.md` must mirror the workflow structure already used by
`ai-chemistry-scientist`, list the seven supported methods, repeat the
REQ-AGENOM-030 heuristic limitation label verbatim in both English and
Japanese, and document REQ-AGENOM-060's and REQ-AGENOM-070's heuristic
nature as the selected way to satisfy those 2 requirements' own
non-misrepresentation constraints (per ADR-0107 and ADR-0108: not a
DESeq2/edgeR replacement and not a validated clinical pathogenicity
predictor, respectively) — neither of those 2 newer modules has a
single fixed verbatim label string defined in requirements.md the way
REQ-AGENOM-030 does.

## DES-AGENOM-080: npm skill-package completeness guard / npmスキル同梱完全性ガード
Responsibilities: Preserve parity between the npm bootstrap package's
shipped ai-genomics-scientist skill payload and its importable Python
sources by asserting that `package.json` `files` contains both exact
entries `.github/skills/ai-genomics-scientist` and
`src/ai_genomics_scientist/**/*.py`, and by proving with an `npm pack
--dry-run --json` listing that the packed artifact contains
`.github/skills/ai-genomics-scientist/SKILL.md`,
`.github/skills/ai-genomics-scientist/manifest.json`, and every current
repository file matching `src/ai_genomics_scientist/**/*.py`.
Interfaces: The test reuses `src/ai_scientist/npm_packaging.py`'s
existing generic helpers — `load_package_files(package_json_path: str |
Path = "package.json") -> list[str]`, `load_npm_pack_dry_run_paths(
project_root: str | Path = ".") -> set[str]` (wraps `npm pack --dry-run
--json`), and `iter_skill_python_globs(package_files: Sequence[str]) ->
dict[str, str]` (maps each shipped `.github/skills/<slug>` entry to its
expected `src/<package>/**/*.py` glob) — rather than defining new
duplicate helper functions. The test-local assertion function composes
these in three steps: (1) `load_package_files()` contains both the
exact skill entry `.github/skills/ai-genomics-scientist` and the exact
glob entry `src/ai_genomics_scientist/**/*.py`; (2)
`iter_skill_python_globs(load_package_files())["\
.github/skills/ai-genomics-scientist"] ==
"src/ai_genomics_scientist/**/*.py"`; and (3) every current repository
file matching `src/ai_genomics_scientist/**/*.py` (resolved via Python
glob expansion, not the literal glob string) is a member of
`load_npm_pack_dry_run_paths()`, together with
`.github/skills/ai-genomics-scientist/SKILL.md` and
`.github/skills/ai-genomics-scientist/manifest.json`.
Constraints: The authoritative packaged-artifact proof is the dry-run
pack listing, not only static inspection of `package.json`. This guard
covers npm distribution completeness only; Python package discovery
continues to rely on existing `src/` layout conventions, unchanged by
this design. New tests must import and reuse
`src/ai_scientist/npm_packaging.py`'s helpers rather than redefining
equivalent logic.
Requirements: REQ-AGENOM-080
ADRs: ADR-0113
Depends-On: DES-AISCI-020
