---
name: ai-structural-biology-scientist
description: "Use when a user asks, in Japanese or English, to run a structural-biology module: a secondary-structure heuristic, per-residue hydrophobicity/burial analysis, a protein-protein docking-score heuristic, structural similarity by RMSD after optimal superposition, or a residue contact-map heuristic. 構造生物学固有の処理（二次構造ヒューリスティック、残基ごとの疎水性・埋没度解析、タンパク質間ドッキングスコア・ヒューリスティック、最適重ね合わせ後RMSDによる構造類似性、残基コンタクトマップ・ヒューリスティック）を実行する際に使用。"
---
# AI Structural Biology Scientist / AI構造生物学科学者

Respond in the user's input language (日本語 / English) for every
user-facing message (REQ-ASTRUCT-001). Dispatch to exactly one of the 5
supported structural-biology modules per request; never mix modules in a
single run (REQ-ASTRUCT-002).

## Workflow / 手順
1. **Detect language and match the request** — call
   `ai_structural_biology_scientist.dispatch.dispatch(request_text)`,
   which loads
   `.github/skills/ai-structural-biology-scientist/manifest.json` and
   matches the request text against each module's registered
   English/Japanese name/synonym list.
   - Exactly one match → invoke that module's handler function.
   - Two or more distinct modules matched → ask a clarification question
     listing every matched candidate; invoke no module.
   - No match → return a rejection message; invoke no module.
2. **Validate parameters before any computation** — each module validates
   its resolved parameters before running any lookup, averaging,
   scoring, superposition, or contact calculation (REQ-ASTRUCT-003); on
   violation it rejects the run naming the parameter and the violated
   constraint. Sequence modules accept only non-empty uppercase sequences
   over `ACDEFGHIKLMNPQRSTVWY`; coordinate-based modules accept only
   finite numeric three-element coordinate sequences.
3. **Record reproducible run evidence** — every completed run returns a
   `RunRecord` with exactly `metadata`, `parameters`, and `result`
   (REQ-ASTRUCT-004), including the numpy version used.

## Supported modules / 対応モジュール
| Method | English | 日本語 |
| --- | --- | --- |
| Secondary structure heuristic | secondary structure / secondary-structure heuristic | 二次構造 / 二次構造ヒューリスティック |
| Hydrophobicity / burial heuristic | per-residue hydrophobicity / hydrophobicity burial heuristic | 残基ごとの疎水性・埋没度 / 疎水性・埋没度ヒューリスティック |
| Protein-protein docking score | protein-protein docking score / protein docking score | タンパク質間ドッキングスコア / タンパク質ドッキングスコア |
| Structural similarity RMSD | structural similarity rmsd / structural similarity | 構造類似性RMSD / 構造類似性 |
| Residue contact map | residue contact map / contact map | 残基コンタクトマップ / コンタクトマップ |

## Important limitations / 重要な制限
Secondary-structure and protein-protein docking-score results always
carry fixed, verbatim limitation labels stating they are heuristics, not
validated predictors or physically accurate simulations:
- Secondary structure (en): "Heuristic only: a fixed illustrative per-residue propensity lookup, not a validated secondary-structure predictor (no windowing, no real Chou-Fasman statistics)."
- Secondary structure (ja): "ヒューリスティックのみ：固定の説明用残基別 propensity lookup であり、検証済みの二次構造予測器ではない（windowing なし、実際の Chou-Fasman 統計なし）。"
- Protein docking (en): "Heuristic only: a fixed-formula geometric/compositional complementarity score, not a physically accurate protein-protein docking simulation (no 3D structure, no energy function)."
- Protein docking (ja): "ヒューリスティックのみ：固定式の幾何・組成補完性スコアであり、物理的に正確なタンパク質間ドッキングシミュレーションではない（3D 構造なし、エネルギー関数なし）。"

## Scope boundary / 対象外
Structural biology stays separate from neighboring skills:
- `ai-chemistry-scientist` owns cheminformatics and small-molecule
  analysis.
- `ai-genomics-scientist` owns sequence/genomics-specific analysis.
- `ai-data-scientist` owns generic, domain-agnostic data analysis.
- `ai-scientist` owns multi-phase research orchestration.

This skill owns only the 5 structural-biology heuristics documented
above, implemented offline with Python/numpy only: no network calls, no
Biopython or PyMOL, and no real PDB/mmCIF parsing beyond caller-supplied
inline coordinate lists.

Traceability: REQ-ASTRUCT-001 through REQ-ASTRUCT-050,
DES-ASTRUCT-001 through DES-ASTRUCT-050
(`.musubix/features/ai-structural-biology-scientist/`).
