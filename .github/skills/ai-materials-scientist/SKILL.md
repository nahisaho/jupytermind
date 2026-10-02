---
name: ai-materials-scientist
description: "Use when a user asks, in Japanese or English, to run a materials-science simulation module: phase-field microstructure evolution, molecular dynamics, classical Monte Carlo, kinetic Monte Carlo, crystal plasticity, a simplified finite-element field solver, or a simplified binary CALPHAD phase diagram. 材料科学固有のシミュレーション（フェーズフィールド法、分子動力学、古典/速度論的モンテカルロ、結晶塑性、有限要素法、CALPHAD状態図）を実行する際に使用。"
---
# AI Materials Scientist / AI材料科学者

Respond in the user's input language (日本語 / English) for every user-facing
message (REQ-AIMS-001). Dispatch to exactly one of the 7 supported
simulation modules per request; never mix modules in a single run
(REQ-AIMS-002).

## Workflow / 手順
1. **Detect language and match the request** — call
   `ai_materials_scientist.dispatch.dispatch(request_text)`, which loads
   `.github/skills/ai-materials-scientist/manifest.json` and matches the
   request text against each module's registered English/Japanese
   name/synonym list.
   - Exactly one match → invoke that module's handler function.
   - Two or more distinct modules matched → ask a clarification question
     listing every matched candidate; invoke no module.
   - No match → return a rejection message; invoke no module.
2. **Validate parameters before any simulation step** — each module handler
   validates its own resolved parameters against its documented
   stability/physical-definedness domain (REQ-AIMS-003) before mutating any
   state; on violation it rejects the run naming the parameter and the
   violated constraint.
3. **Record reproducible run evidence** — every completed run returns a
   `RunRecord` with exactly `metadata`, `parameters`, and `arrays`
   (REQ-AIMS-004), using the unit system fixed for that module
   (REQ-AIMS-005).

## Supported modules / 対応モジュール
| Method | English | 日本語 |
| --- | --- | --- |
| Phase-field | phase-field | フェーズフィールド法 |
| Molecular dynamics | molecular dynamics | 分子動力学 |
| Classical Monte Carlo | classical monte carlo | 古典モンテカルロ |
| Kinetic Monte Carlo | kinetic monte carlo | 速度論的モンテカルロ |
| Crystal plasticity | crystal plasticity | 結晶塑性 |
| Finite element | finite element | 有限要素法 |
| CALPHAD | calphad / phase diagram | CALPHAD / 状態図 |

## Scope boundary / 対象外
Generic, domain-agnostic analysis (including Bayesian optimization for
next-experiment design) stays in `ai-data-scientist`; multi-phase research
orchestration stays in `ai-scientist`. This skill owns materials-science
simulation only, implemented with numpy/scipy/pandas/scikit-learn (no
external solver binaries, no network calls).

Traceability: REQ-AIMS-001 through REQ-AIMS-070, DES-AIMS-001 through
DES-AIMS-070 (`.musubix/features/ai-materials-scientist/`).
