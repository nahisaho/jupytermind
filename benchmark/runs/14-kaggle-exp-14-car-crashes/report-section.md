## 実験14: Car Crashes / Bad Drivers（分析完了・全セル再実行と最終監査の完了は未確認）

**課題**: 「Kaggleで扱われる米国州別の交通事故データから、事故率や死亡率に関係する特徴を探してください。」

**初回プロンプト（全文・原文）**: 「Kaggleで扱われる米国州別の交通事故データから、事故率や死亡率に関係する特徴を探してください。分析方法と図表を自分で選び、州間の比較可能性や相関から因果を主張できない点も含めて日本語で報告してください。AI Data Scientist SkillとJupyter MCPを使い、計画・コード・出力・根拠付きInsightを記録し、再実行を確認してください。 Kaggle参照先: https://www.kaggle.com/datasets?search=bad+drivers+car+crashes。インストール済みkaggle Python SDKを使い、NotebookのJupyter MCP実行セル内で`KaggleApi().authenticate()`、`dataset_list(search=...)`、`dataset_list_files(...)`、必要に応じて`dataset_download_file(...)`を呼び出し、Kaggle上の対応する公開データを検索・取得してください。外部CSVミラーは使用しないでください。owner/dataset slug、取得ファイル名、取得日、ファイルSHA-256をNotebookに記録してください。APIトークンをセル出力・Notebook・ログへ表示しないでください。分析・API取得コードの実行はJupyter MCPだけを使い、端末コマンド、subprocess、外部スクリプト起動、作業エージェントへの委譲は行わないでください。APIで対応するデータが見つからない場合は外部ソースにフォールバックせず、その実験を停止して理由を報告してください。保存先は benchmark/projects/kaggle-v020-kaggle-exp-14-car-crashes/notebooks/kaggle-v020-kaggle-exp-14-car-crashes.ipynb としてください。run_idは `v020-exp-14` です。長時間処理の開始前にlifecycle.register_runを呼び、実行・書込みフェーズを記録し、終了時にcompletedまたはfailedを記録してください。データ定義manifest、分析前提manifest、意味的な異常検査、妥当な範囲の感度分析を使い、適用できない機能は理由を記録してください。図表はvisual_audit=Trueで監査してください。Notebookには「使用したJupytermindモジュール」節を設け、直接import・呼び出したモジュール名、関数名、使用目的を記録してください。間接利用は使用済みに含めないでください。Jupytermindの不具合または機能不足が疑われた場合は「Jupytermind改善候補」節を設け、分類、再現条件、期待する挙動、実際の挙動、影響、回避策、関係するセルとログを記録してください。Copilot CLI、Kaggle API、ベンチマークランナーに固有の問題とは切り分け、候補がなければ「なし」と記録してください。初回分析後、自分で結果を読み直し、結論に実質的な影響を与える未解決点があれば自然言語の追加依頼文を作成し、Notebookの「反復依頼履歴」に原文のまま記録して実行してください。価値ある追加分析がなくなるまで最大3回繰り返し、各反復の選定理由・結果・証拠・残る限界を報告してください。最後に全コードセルを上から再実行し、notebook_auditとライフサイクル状態を記録してください。」

**使用したJupytermindモジュール**: 保存されたNotebookのコードで直接import・呼び出しを確認できるものを記載します。以下のセル番号は0始まりです。操作用bootstrapでの利用を述べたMarkdownだけでは、当該コードの直接実行を確認したとは扱いません。

| モジュール | 直接呼び出した関数・クラス | 使用目的 |
|---|---|---|
| `ai_data_scientist.project_manager` | `resolve_project`, `ensure_notebook`, `ensure_data_dir` | 分析プロジェクト、Notebook、取得データの保存先を準備（セル1）。 |
| `ai_data_scientist.language_router` | `detect_language` | 日本語の分析・解釈を選択（セル1）。 |
| `ai_data_scientist.lifecycle` | `register_run`, `mark_write_start`, `mark_write_end`, `is_cancel_requested`, `mark_execution_start`, `mark_execution_end`, `mark_failed`, `get_run_status` | run_id登録、実行・書込みフェーズ、中止・例外時の処理、状態表示（セル1と各分析セル）。例外分岐の実行回数は保存出力だけでは確定しない。 |
| `ai_data_scientist.ingestion` | `SourceSpec`, `ingest` | Kaggleから取得したローカルCSVを読み込み、行数上限による切り詰めがないことを確認（セル4）。 |
| `ai_data_scientist.cleaning` | `clean_dataset` | 重複除去操作の影響を記録。51行から51行で除去0行（セル6）。 |
| `ai_data_scientist.eda` | `explore` | 型、欠損、記述統計、州名の一意性を把握（セル6）。 |
| `ai_data_scientist.data_definition` | `FieldValue`, `build_manifest`, `DataDefinitionManifest.unresolved_fields` | 出典、単位、年、未確認・推測事項、派生率の定義を記録（セル6・17・22）。 |
| `ai_data_scientist.analysis_assumptions` | `Assumption`, `AnalysisAssumptionManifest`, `check_manifest` | 州間比較、異年指標、独立性、因果解釈の前提と未解決警告を記録（セル6）。 |
| `ai_data_scientist.data_quality` | `detect_anomalies` | 州キーの許容値・一意性・非欠損、割合の0～100%、率・金額の非負制約を検査（セル6）。 |
| `ai_data_scientist.stats_analysis` | `correlation` | 日本語解釈付きPearson相関を計算（セル8）。 |
| `ai_data_scientist.visualization` | `render_chart`, `build_image_output` | 初回の散布図描画と、初回・反復2のPNG出力を組み立て（セル9・17・22）。 |
| `ai_data_scientist.sensitivity` | `SensitivityPlan`, `run_sensitivity` | DC有無とPearson/Spearmanの4仕様を比較（セル14・17）。 |
| `ai_data_scientist.notebook_audit` | `audit_visual_outputs` | chartメタデータを持たないPNGの監査挙動を点検（セル22）。 |

最終セル25には、`ai_data_scientist.insight_engine.extract_cited_value` による根拠照合、`project_manager.enqueue_write` による参照更新、`notebook_audit.audit_notebook(..., visual_audit=True)`、`lifecycle.mark_completed` / `wait_for_quiescence` / `mark_failed` の直接呼び出しコードもあります。ただし、このセルはexecution_countがなく出力もないため、これらの最終処理の完了は未確認です。`insight_engine.record_insight` 等のbootstrap利用はNotebookの利用記録にはありますが、指定された証拠内では実コード・出力を確認できないため、上表の実行確認済み機能に加えていません。Spearman相関、BH補正、leave-one-out、ブートストラップ、共分散分解、置換実験、横棒図・3パネル図はSciPy・NumPy・Matplotlib等による分析コードであり、Jupytermindの提供機能として数えません。

**初回指示**: 分析手法と図表はAI自身に選ばせ、州間の比較可能性と相関・因果の違いを説明するよう求めました。Kaggle API限定の取得、来歴・SHA-256、定義と前提のmanifest、意味的品質検査、感度分析、根拠付きInsight、最大3回の自律的な追加依頼、全セル再実行、図表監査とライフサイクル記録を要求しています。Notebookは州別順位とPearson/Spearman相関を中心に計画し、死亡事故関与運転者率と一般事故率・人口当たり死亡率を区別しました。

**データ取得**: Notebookで `KaggleApi().authenticate()`、`dataset_list(search='bad drivers')` / `dataset_list(search='car crashes')`、`dataset_list_files(...)` を呼び出し、FiveThirtyEight名義の `fivethirtyeight/fivethirtyeight-bad-drivers-dataset` を選びました。ファイル一覧は `bad-drivers.csv`（2,575 bytes）と `README.md`（1,119 bytes）です。取得セルには `dataset_download_file(...)` と、再実行時に既取得ファイルのハッシュ・slug・ファイル名を確認する分岐があります。外部CSVミラーの利用は記録されていません。

CSVは50州＋District of Columbia（DC）の51行・8列で、取得日時は `2026-10-01T17:16:15.810231+00:00`（日本時間2026年10月2日02:16:15）、SHA-256は `49cd87d45f9eb199f8115035e4828aefbc338663dfeb2467ad2956c4478a02c4` です。同梱READMEの内容もNotebook出力に保存され、SHA-256は `a0f673ae7c0afc8208bd3ee311c49c47913b5d39773383aabc59f7e3fd3d9c54` です。認証処理はSDKの標準出力・標準エラーを抑制しており、指定証拠にAPIトークンの表示は見当たりません。

READMEにより、対象の率は2012年の「死亡事故に関与した運転者数／走行10億マイル」と確認できました。飲酒・注意散漫でない・事故歴なしの割合も2012年ですが、速度超過割合は2009年、保険料は2011年、保険会社損失は2010年です。死亡者数や事故件数の率ではなく、割合も全運転者の曝露割合ではありません。割合間で同じ運転者が重なり得るため、足して100%にはしません。「注意散漫でない」「事故歴なし」の否定表現も保持しました。

**初回結果**: 州の網羅性、数値型・有限値、欠損、重複、意味的制約を検査し、欠損・重複・検出された制約違反はいずれもありませんでした。補完や外れ値除外は行っていません。率の州等重み平均は15.7902、中央値15.6、範囲5.9～23.9です。North DakotaとSouth Carolinaは23.9、West Virginiaは23.8で高く、DCは5.9、州だけではMassachusettsの8.2が最低でした。この平均は全国の走行距離加重率ではなく、順位も死亡者率や一般事故率の順位ではありません。

6特徴について相関を計算し、Pearson・Spearmanそれぞれ6比較にBH補正を適用しました。

| 特徴 | 観測年 | Pearson r | 未補正p | Spearman rho | Pearson BH q |
|---|---:|---:|---:|---:|---:|
| 速度超過割合 | 2009 | −0.0291 | 0.8395 | −0.0172 | 0.9457 |
| 飲酒割合 | 2012 | 0.1994 | 0.1606 | 0.0514 | 0.4818 |
| 注意散漫でない割合 | 2012 | 0.0098 | 0.9457 | 0.0930 | 0.9457 |
| 事故歴なし割合 | 2012 | −0.0179 | 0.9006 | 0.0193 | 0.9457 |
| 保険料 | 2011 | −0.1997 | 0.1600 | −0.1181 | 0.4818 |
| 保険会社損失 | 2010 | −0.0360 | 0.8019 | −0.000045 | 0.9457 |

最大の絶対値でも約0.20で、Pearsonの補正後qはすべて0.48を超え、Spearmanの補正後qも全特徴で約0.9997でした。ここでは明瞭な単変量の州間関連を検出していません。自動生成の「弱い正／負の相関」という文は方向と大きさの記述にとどめ、飲酒や速度超過に影響がないという結論には用いていません。根拠はセル8の `CORRELATIONS_JSON` / `RANGE_JSON` と、execution_count 14を参照する初回Insightです。

![死亡事故関与運転者率の上位10州](figures/exp-14-top-ten-state-fatal-driver-rates.png)

*2012年の走行10億マイル当たり死亡事故関与運転者率を上位10州で比較した横棒図。死亡者数や全事故件数の順位ではありません。Notebookセル9のPNG出力をそのまま抽出しました。*

![飲酒割合と死亡事故関与運転者率の散布図](figures/exp-14-alcohol-percentage-and-fatal-driver-rate.png)

*50州＋DCについて、死亡事故関与運転者中の飲酒割合と総運転者率を比較。両指標は2012年ですが、飲酒割合は全運転者の飲酒頻度を表しません。*

![保険料と死亡事故関与運転者率の散布図](figures/exp-14-insurance-premium-and-fatal-driver-rate.png)

*2011年の保険料と2012年の死亡事故関与運転者率。弱い負相関は、保険料を高くすると安全になるという因果効果の証拠ではありません。*

**AIが生成した追加依頼1 — DC・特定州・相関仕様への依存**

> 初回の相関が弱いという結論は、DCの特殊性、一部の州、直線性の仮定に依存していませんか。DCを除外し、PearsonとSpearmanを比較し、全州のleave-one-outと固定seedの州単位ブートストラップで不確実性を確認してください。弱い相関付近では相対偏差が大きくなる点も分けて説明してください。

**選定理由**: 初回で弱い相関しか得られなかったため、DCや特定州、直線関係を仮定する手法によって結論が変わらないかを優先しました。仕様の安定性、係数の実質的な大きさ、不確実性を分けて評価する依頼です。

**結果・証拠**: 6特徴×DC有無×Pearson/Spearmanの24仕様で、点推定の最大絶対値は0.1997でした。DCを除くと飲酒のPearson相関は0.1758、保険料は−0.1047となりました。1地域ずつ除いたPearson相関の最大絶対値は0.2685で、飲酒の範囲は0.1218～0.2515、保険料は−0.2685～−0.1047です。Notebookで探索上の目安とした絶対値0.30に達する点推定はありませんでした。

州単位のブートストラップは各特徴・各対象で4,000回、seedは `20261002` です。DCを含む／除く全12区間が0を含みました。全地域での飲酒の95%区間は[−0.1629, 0.4781]、保険料は[−0.4551, 0.0913]です。弱い点推定は共通しますが、中程度の関連を完全に排除できるほど区間は狭くありません。

`run_sensitivity` の相対偏差20%基準では6特徴とも `stable=False`、最大相対偏差は特徴別に約0.408～15.367でした。基準値がゼロ付近では相対偏差が膨らむため、これをそのまま「強い関連がある」とも「効果ゼロが頑健」とも読みません。根拠はセル14の感度表、leave-one-out表、ブートストラップ表、`ITERATION1_SUMMARY` と、execution_count 20を参照するセル15のInsightです。残る限界は州の空間依存、小標本、道路・地域・記録方法等の未調整交絡です。区間は全国の運転者リスクの信頼区間ではありません。

**AIが生成した追加依頼2 — 派生率の数学的結合**

> 割合では相関が弱い一方、飲酒関与の死亡事故運転者率に変換すると強い相関が現れませんか。2012年の同年指標に限定して、総率×飲酒割合から派生率を作り、総率が両方に入る数学的結合を固定割合、共分散分解、割合の置換実験で点検してください。派生率の強い相関を飲酒の因果効果や独立した危険因子の証拠と誤解しない説明と図を追加してください。

**選定理由**: 割合の弱い相関と、部分率へ変換したときの強い相関が見かけ上矛盾し得るためです。目的変数である総率が派生指標にも含まれる問題は結論を大きく変え得ます。同年2012年の飲酒指標に限定し、置換を因果効果の検定ではなく数学的結合の診断として選びました。

**結果・証拠**: 2012年の3特徴だけでBH補正をやり直しても、最小qは0.4818でした。一方、飲酒の派生率を `総率×飲酒割合/100` とすると、総率とのPearson相関は0.8526へ強まりました。飲酒割合を全地域で平均割合に固定すると相関は1.0です。総率を固定したまま飲酒割合を州間で5,000回置換すると、相関の平均は0.8347、中央95%範囲は[0.7778, 0.8794]となり、観測値0.8526はその範囲内でした。seedは `20261003`、観測相関以上となる補正付き上側比率は0.2623です。この比率は飲酒の個人リスクについてのp値ではありません。

総率をR、飲酒割合を0～1のPとすると、共分散は `Cov(R, RP) = E[P]Var(R) + Cov(R, R(P−E[P]))` に分けられます。出力は総共分散5.9578、平均割合×総率分散の項5.1116、残差項0.8462で、構造項の比率は約85.8%でした。これは因果的な寄与割合やR²ではありません。DC有無×Pearson/Spearmanでは相関0.8400～0.8950、`stable=True`、最大相対偏差0.0497ですが、数値的安定性は独立した危険因子としての解釈を保証しません。

根拠はセル17の `ITERATION2_SUMMARY`、共分散一致の検算、派生率の感度出力、3パネル図と、execution_count 22を参照するセル18のInsightです。派生率は丸められた2列の積で、分子母集団・測定方法の完全一致は未確認としてmanifestに `inferred` を残しています。

![飲酒割合・派生率・置換分布による数学的結合の点検](figures/exp-14-derived-alcohol-rate-mathematical-coupling.png)

*左は元の飲酒割合との弱い関連、中央は総率を掛けた派生率との強い関連、右は数学的結合を残した5,000回の割合置換分布。赤線の観測相関は分布内にあり、強い派生相関だけで飲酒の因果効果を説明できないことを示します。*

**反復の終了判断**: AIが生成した分析上の追加依頼は上記2件です。3回目は、同年の人口・走行距離・道路条件・全運転者の曝露・記録方法を含む独立データが必要で、現CSVのモデルや検定を増やしても重要な識別問題が解消しないため実施しませんでした。`followup.log` は、この2回の反復を再確認し、未実行の最終監査セルとMCP接続問題への対応を述べています。新たな3回目の分析依頼や結果は保存されていません。

**最終結論**: `status.json` の `analysis_complete=true`、`final_completion.ready=true` と、Notebookの初回分析・2回の反復・日本語結論・4件の根拠付きInsightから、探索分析の成果物は完成したと判断します。このデータでは6特徴の明瞭な単変量の州間関連は検出されず、点推定の弱さはDC除外・順位相関・単一地域除外でも大きくは変わりません。ただし区間は広く、「関連なし」や「飲酒・速度超過は安全」とは結論できません。

最も重要な追加成果は、飲酒割合を派生率に変えるだけで強い相関が生じ、その大部分が総率の共用による数学的結合で説明できることを点検した点です。州差を説明する独立した危険因子や因果効果は特定していません。分析完了と、全コードセル再実行・最終監査・ライフサイクル完了の確認は別であり、後者の成功は以下の証拠からは確認できません。

**監査・再現性**: Notebookの保存先は `benchmark/projects/kaggle-v020-kaggle-exp-14-car-crashes/notebooks/kaggle-v020-kaggle-exp-14-car-crashes.ipynb`、run_idは `v020-exp-14` です。保存済みコードセルは12、execution_count付きは11で、エラー出力はありません。図表はセル9に3枚、セル17に1枚の計4 PNG、Insightは4件です。各Insightの引用値とexecution_countは該当保存出力に対応しています。

| 確認対象 | 指定ファイルから確認できた状態 |
|---|---|
| 構造監査 | `status.json` の初回・最終auditに `nbformat_valid=true`、`error_cells=[]`、図表セル[9, 17]、`visual_findings=[]`。未実行一覧は空だが、監査中の末尾セル25を除外した警告がある。 |
| 全セル再実行 | Notebookは再実行計画を記すが、セル24の実出力とNotebookメタデータは `verification_mode=baseline_recorded`。`replay_matched` の出力はなく、独立カーネルでの全セル一致を確認したとは言えない。 |
| ベースライン | セル24はデータハッシュ、行数、欠損、相関、感度、置換、ブートストラップ、leave-one-outをまとめた初回ベースライン記録を出力。snapshot SHA-256は `c1309984f32de17835a0d55a42c2063c9dbeed65733469cac68bf5a45f5be49d`。別ファイルの実在・内容は今回の指定証拠の対象外。 |
| 最終Notebook監査 | セル25に `audit_notebook(..., visual_audit=True)` はあるが、execution_countはnull、outputsは空。`NOTEBOOK_AUDIT` の実出力はない。外部auditの結果とNotebook内最終監査の完了を同一視しない。 |
| ライフサイクル | セル1は登録後の `state=running` と、実行・書込み・ロック各カウンタ0を出力。最終セルの `FINAL_LIFECYCLE` 出力はなく、`completed` と静穏状態の検証完了は未確認。 |
| 図表 | セル9・17にchartメタデータ、初回図ごとのラベル情報、`missing_glyphs=[]` が保存されている。メタデータなしの監査が空結果になる再現もあり、警告なしを図表品質の全面保証とは扱わない。 |
| 外部ランナー | 初回773.0秒、追加確認92.5秒、両exit_codeは0、終了理由はともに `artifact_complete_cutoff`。両ログ末尾は「Notebook remained stable and passed semantic audit」を理由にプロセス群を停止した旨を記録。正常終了コードだけで最終セル完了は主張しない。 |

**実行上の失敗・未完了部分**: Notebookセル3は、初回にKaggle SDKの `dataset_list` へ `page_size` を渡してTypeErrorになり、公開シグネチャを確認して `search` のみへ修正したと記録しています。保存済みセル2は修正後の検索結果を出力しており、この失敗は取得を最終的に妨げていません。元の例外tracebackは指定ログにはなく、発生経緯はNotebookの記述に基づきます。これは外部SDKの引数互換性の問題で、Jupytermindの改善候補には含めません。

親ディレクトリなしでのJupyter MCPのNotebook作成についても、Notebookは `project_manager.ensure_notebook` を使うbootstrapで解消したと記述していますが、その操作ログは指定証拠にはありません。追加確認ログは「MCPの接続にプロトコル不一致があるため、リポジトリの互換版クライアントで接続し直す」と述べるものの、接続回復・再実行完了の出力はありません。これをJupytermind内部の不具合と断定しません。また、外部ランナーは成果物の安定とauditを条件に打ち切っています。打ち切りと未完了セルはともに確認できますが、最終セル未完了の直接原因を特定する詳細ログはありません。分析そのものの失敗ではなく、要求された再実行・最終監査・完了状態の記録について証拠が不足した状態です。

**Jupytermindの改善候補**: Notebookの候補記録と直接APIの診断に基づき、3件を `issue-candidate.json` に保存しました。実装を修正した、または不具合を確定したという意味ではありません。

| 分類 | 候補・観測された挙動 | 影響・回避策・証拠の限界 |
|---|---|---|
| 可視化のレイアウト機能不足 | 長い州名の縦棒図でラベル下端が切れたとセル20に記録。セル22で表示した `render_chart` の公開シグネチャにfigsize・余白調整引数はない。 | 最終セル9はMatplotlibの横棒図、`tight_layout`、`bbox_inches='tight'` で回避。修正前のPNG自体は指定Notebookに残っておらず、切れの発生は履歴記述に基づく候補。 |
| データ定義の未検証項目抽出の仕様不足 | `unresolved_fields()` がunknownだけを返し、inferredの走行距離分母が漏れる。セル22は `INFERRED_NOT_RETURNED ['variables.fatal_driver_rate.exposure_denominator']` を出力。 | 推測した前提を未解決一覧だけから追跡できない。セル6でinferredを別途列挙して回避。Notebookは仕様どおりの可能性を明記しており、契約違反とは断定しない。 |
| 図表監査のメタデータ欠如の見逃し | 非空PNGにchartメタデータを付けず `audit_visual_outputs` を実行すると、セル22で `NO_METADATA_VISUAL_FINDINGS []`、`NO_METADATA_PRESENT {}`。 | 監査用情報がないことと、監査して問題がないことを区別できない。実図ではchartメタデータと文字警告記録を付けて回避。画像内のラベル欠損そのものをこのprobeが証明したわけではない。 |

上記はJupytermindの可視化・定義・監査APIの候補です。Kaggle SDKのTypeError、MCP接続のプロトコル不一致、外部ランナーの成果物条件による停止は別枠です。`mcp_gateway.run_and_record` は同一カーネルへの再帰的なMCP接続を避けるため非適用と記録されており、Notebookは直接のJupyter MCP実行を採用しています。この環境上の適用制限も、それだけでJupytermindの不具合とは扱いません。

**残る限界**: 対象は2009～2012年の異年混在データであり、現在の交通安全状況ではありません。走行距離正規化は人口・交通量差の一部を調整しても、都市化、道路構造、天候、車種、救急アクセス、州別の認定・記録差を揃えません。`measurement` / `temporal` / `independence` の結論に重要な前提警告は未解決です。各列の詳細測定方法、走行距離の測定・車種範囲、派生率の母集団一致、ライセンスも十分に確認されていません。

死亡事故関与運転者だけを分母とする特徴割合には選択・構成比の問題があり、全運転者の飲酒・速度超過の曝露は不明です。州を等重みとする横断集計なので、生態学的誤謬、未調整交絡、逆因果、空間依存を排除できず、因果効果も全国の個人リスクも推定していません。独立した同年・同一定義の参照データがないため、独立検証・データセット比較は非適用としています。分析を深めるには追加の独立データが必要であり、本実験の図表・根拠記録の完成と、再実行・最終監査の未確認部分は区別して評価する必要があります。
