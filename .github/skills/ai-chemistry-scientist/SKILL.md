---
name: ai-chemistry-scientist
description: "Use when a user asks, in Japanese or English, to run a cheminformatics module: molecular descriptor calculation, ADMET heuristic screening, QSAR linear-regression modeling, molecular similarity search, a simplified docking-score heuristic, drug-likeness rule screening, structural-alert screening, molecular formula/exact-mass calculation, or heuristic bioactivity classification. 化学情報学固有の処理（分子記述子計算、ADMETヒューリスティックスクリーニング、QSARモデリング、分子類似性検索、ドッキングスコアヒューリスティック、薬物らしさルールスクリーニング、構造アラートスクリーニング、分子式・正確質量計算、生物活性ヒューリスティック分類）を実行する際に使用。"
---
# AI Chemistry Scientist / AI化学科学者

Respond in the user's input language (日本語 / English) for every user-facing
message (REQ-ACHEM-001). Dispatch to exactly one of the 9 supported
cheminformatics modules per request; never mix modules in a single run
(REQ-ACHEM-002).

## Workflow / 手順
1. **Detect language and match the request** — call
   `ai_chemistry_scientist.dispatch.dispatch(request_text)`, which loads
   `.github/skills/ai-chemistry-scientist/manifest.json` and matches the
   request text against each module's registered English/Japanese
   name/synonym list.
   - Exactly one match → invoke that module's handler function.
   - Two or more distinct modules matched → ask a clarification question
     listing every matched candidate; invoke no module.
   - No match → return a rejection message; invoke no module.
2. **Validate parameters before any computation** — each module validates
   its resolved parameters (e.g. SMILES must parse to a valid RDKit
   molecule, training sets must have at least 5 compounds with a full-rank
   descriptor matrix, `k` must be an integer in `[1, 20]`) before running
   any computation (REQ-ACHEM-003); on violation it rejects the run naming
   the parameter and the violated constraint. `molecular-descriptors`
   instead validates and computes per-item, continuing past individual
   rejected entries rather than failing the whole batch.
3. **Record reproducible run evidence** — every completed run returns a
   `RunRecord` with exactly `metadata`, `parameters`, and `result`
   (REQ-ACHEM-004), including the RDKit version used (and the
   scikit-learn version for QSAR modeling).

## Supported modules / 対応モジュール
| Method | English | 日本語 |
| --- | --- | --- |
| Molecular descriptors | molecular descriptors / descriptor calculation | 分子記述子 / 記述子計算 |
| ADMET prediction | admet prediction / admet screening | ADMET予測 / ADMETスクリーニング |
| QSAR modeling | qsar modeling / qsar regression | QSARモデリング / QSAR回帰 |
| Molecular similarity | molecular similarity / similarity search | 分子類似性 / 類似性検索 |
| Docking score | docking score / docking simulation | ドッキングスコア / ドッキングシミュレーション |
| Drug-likeness rules | drug-likeness rules / drug-likeness screening | 薬物らしさルール / 薬物らしさルールスクリーニング |
| Structural alerts | structural alerts / structural alert screening | 構造アラート / 構造アラートスクリーニング |
| Formula & exact mass | molecular formula and exact mass / formula and exact mass | 分子式と正確質量 / 分子式・正確質量 |
| Bioactivity classification | target-class activity classification / bioactivity classification | 標的クラス活性分類 / 生物活性分類 |

## Important limitations / 重要な制限
ADMET prediction, docking-score, structural-alert, and bioactivity
classification results always carry a fixed, verbatim limitation label
stating they are heuristic approximations, not validated predictions,
full structural-alert catalogs, or physically accurate simulations:
- ADMET (en): "Heuristic only: not a physically or clinically validated
  ADMET prediction."
- ADMET (ja): "ヒューリスティックのみ: 物理的または臨床的に検証されたADMET
  予測ではありません。"
- Docking (en): "Heuristic only: not a physically accurate docking
  simulation (no 3D conformer generation, no energy function)."
- Docking (ja): "ヒューリスティックのみ: 物理的に正確なドッキングシミュレー
  ションではありません（3D配座生成・エネルギー関数なし）。"
- Structural alerts (en): "Heuristic only: a small fixed illustrative
  SMARTS alert list, not the validated PAINS/Brenk filter catalog."
- Structural alerts (ja): "ヒューリスティックのみ: 固定の小規模な例示用SMARTS
  アラート一覧であり、検証済みのPAINS/Brenkフィルタ・カタログではない。"
- Bioactivity classification (en): "Heuristic only: not a ChEMBL-trained
  or experimentally validated bioactivity classifier."
- Bioactivity classification (ja): "ヒューリスティックのみ:
  ChEMBLで学習済みでも実験的に検証済みでもない生物活性分類器ではない。"

## Scope boundary / 対象外
Generic, domain-agnostic analysis stays in `ai-data-scientist`; multi-phase
research orchestration stays in `ai-scientist`; materials-science
simulation stays in `ai-materials-scientist`. This skill owns
cheminformatics only, implemented with RDKit/numpy/scikit-learn (no
external docking engines, no 3D conformer generation, no network calls).

Traceability: REQ-ACHEM-001 through REQ-ACHEM-090, DES-ACHEM-001 through
DES-ACHEM-090 (`.musubix/features/ai-chemistry-scientist/`).
