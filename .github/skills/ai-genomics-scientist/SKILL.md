---
name: ai-genomics-scientist
description: "Use when a user asks, in Japanese or English, to run a computational-genomics module: sequence feature analysis, variant effect heuristic annotation, splice-site strength heuristic scoring, gene-set enrichment analysis, or pairwise sequence alignment. ゲノミクス固有の処理（配列特徴量解析、バリアント効果ヒューリスティック注釈、スプライス部位強度ヒューリスティック、遺伝子セットエンリッチメント解析、配列アラインメント）を実行する際に使用。"
---
# AI Genomics Scientist / AIゲノミクス科学者

Respond in the user's input language (日本語 / English) for every
user-facing message (REQ-AGENOM-001). Dispatch to exactly one of the 5
supported genomics modules per request; never mix modules in a single
run (REQ-AGENOM-002).

## Workflow / 手順
1. **Detect language and match the request** — call
   `ai_genomics_scientist.dispatch.dispatch(request_text)`, which loads
   `.github/skills/ai-genomics-scientist/manifest.json`, normalizes the
   request and manifest names with Unicode NFKC, and matches the request
   text against each module's registered English/Japanese
   name/synonym list.
   - Exactly one match → invoke that module's handler function.
   - Two or more distinct modules matched → ask a clarification question
     listing every matched candidate; invoke no module.
   - No match → return a rejection message; invoke no module.
2. **Validate parameters before any computation** — each module validates
   its resolved parameters before running any computation
   (REQ-AGENOM-003). `sequence-features` validates and computes
   per-item, continuing past individual rejected sequences rather than
   failing the whole batch. `variant-effect-annotation`,
   `splice-site-strength`, `gene-set-enrichment`, and
   `pairwise-sequence-alignment` validate atomically and reject the whole
   run on any invalid parameter.
3. **Record reproducible run evidence** — every completed run returns a
   `RunRecord` with exactly `metadata`, `parameters`, and `result`
   (REQ-AGENOM-004), including the numpy version used and the scipy
   version for the gene-set-enrichment module.

## Supported modules / 対応モジュール
| Method | English | 日本語 |
| --- | --- | --- |
| Sequence features | `sequence-features` / sequence feature analysis | `配列特徴量解析` |
| Variant effect annotation | `variant-effect-annotation` / variant effect heuristic annotation | `バリアント効果注釈` |
| Splice-site strength | `splice-site-strength` / splice-site strength heuristic | `スプライス部位強度` |
| Gene-set enrichment | `gene-set-enrichment` / gene set enrichment analysis | `遺伝子セットエンリッチメント` |
| Pairwise sequence alignment | `pairwise-sequence-alignment` / pairwise sequence alignment | `配列アラインメント` |

## Important limitations / 重要な制限
Splice-site strength results are governed by a fixed, illustrative
heuristic and must always be understood with this exact limitation
label:
- Splice-site heuristic (en): "Heuristic only: a fixed illustrative
  position-weight scoring scheme, not a validated splice-site predictor
  (not SpliceAI, not based on real splice-site frequency data)."
- Splice-site heuristic (ja): "ヒューリスティックのみ：これは固定された
  例示用の position-weight スコアリング方式であり、検証済みの
  スプライス部位予測器ではない（SpliceAI ではなく、実際の
  スプライス部位頻度データにも基づかない）。"

## Scope boundary / 対象外
Genomics stays separate from `ai-chemistry-scientist`,
`ai-structural-biology-scientist`, `ai-data-scientist`, and
`ai-scientist`. This skill owns offline computational genomics only,
implemented with numpy/scipy plus the standard library. It does not own
cheminformatics, structural-biology workflows, generic domain-agnostic
data analysis, or multi-phase research orchestration, and it does not
call the network or external bioinformatics libraries such as
Biopython.

Traceability: REQ-AGENOM-001 through REQ-AGENOM-050, DES-AGENOM-001
through DES-AGENOM-050
(`.musubix/features/ai-genomics-scientist/`).
