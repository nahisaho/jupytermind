## 実験04: Tips（Kaggle API取得失敗・関連分析は未実施）

**課題**: 「Kaggleの飲食店Tipsデータで、チップ額やチップ率に関係する特徴を調べてください。」

**初回プロンプト（全文・原文）**:

```text
Kaggleの飲食店Tipsデータで、チップ額やチップ率に関係する特徴を調べてください。分析方法は自分で選び、見やすい図表とともに、観察できた関係と因果とは言えない点を日本語で説明してください。AI Data Scientist SkillとJupyter MCPを使い、分析計画、コード、実行結果、根拠付きInsightをノートブックに記録し、再実行可能か確認してください。 Kaggle参照先: https://www.kaggle.com/datasets/jsphyg/tipping。インストール済みkaggle Python SDKを使い、NotebookのJupyter MCP実行セル内で`KaggleApi().authenticate()`、`dataset_list(search=...)`、`dataset_list_files(...)`、必要に応じて`dataset_download_file(...)`を呼び出し、Kaggle上の対応する公開データを検索・取得してください。外部CSVミラーは使用しないでください。owner/dataset slug、取得ファイル名、取得日、ファイルSHA-256をNotebookに記録してください。APIトークンをセル出力・Notebook・ログへ表示しないでください。分析・API取得コードの実行はJupyter MCPだけを使い、端末コマンド、subprocess、外部スクリプト起動、作業エージェントへの委譲は行わないでください。APIで対応するデータが見つからない場合は外部ソースにフォールバックせず、その実験を停止して理由を報告してください。保存先は benchmark/projects/kaggle-v020-kaggle-exp-04-tips/notebooks/kaggle-v020-kaggle-exp-04-tips.ipynb としてください。run_idは `v020-exp-04` です。長時間処理の開始前にlifecycle.register_runを呼び、実行・書込みフェーズを記録し、終了時にcompletedまたはfailedを記録してください。データ定義manifest、分析前提manifest、意味的な異常検査、妥当な範囲の感度分析を使い、適用できない機能は理由を記録してください。図表はvisual_audit=Trueで監査してください。Notebookには「使用したJupytermindモジュール」節を設け、直接import・呼び出したモジュール名、関数名、使用目的を記録してください。間接利用は使用済みに含めないでください。Jupytermindの不具合または機能不足が疑われた場合は「Jupytermind改善候補」節を設け、分類、再現条件、期待する挙動、実際の挙動、影響、回避策、関係するセルとログを記録してください。Copilot CLI、Kaggle API、ベンチマークランナーに固有の問題とは切り分け、候補がなければ「なし」と記録してください。初回分析後、自分で結果を読み直し、結論に実質的な影響を与える未解決点があれば自然言語の追加依頼文を作成し、Notebookの「反復依頼履歴」に原文のまま記録して実行してください。価値ある追加分析がなくなるまで最大3回繰り返し、各反復の選定理由・結果・証拠・残る限界を報告してください。最後に全コードセルを上から再実行し、notebook_auditとライフサイクル状態を記録してください。
```

**使用したJupytermindモジュール**: 対象Notebookのコードセルと「使用したJupytermindモジュール」節で確認できる直接利用を示します。制御Notebookで直接呼び出したと記録されている関数は、対象Notebook内の呼び出しと区別しています。表中のセルindexは0始まりです。

| モジュール | 関数・型・メソッド | 使用目的・直接利用の場所 |
|---|---|---|
| `ai_data_scientist.project_manager` | `resolve_project`, `ensure_notebook`, `ensure_data_dir` | 対象Notebookのindex 1でプロジェクトと保存先を解決・準備 |
| `ai_data_scientist.project_manager` | `enqueue_write`, `ProjectHandle` | Notebookの利用記録にある制御Notebook側の直列保存と監査再現用ハンドル作成。対象Notebookの分析コード内の呼び出しとは区別 |
| `ai_data_scientist.language_router` | `detect_language` | index 1で日本語を選択 |
| `ai_data_scientist.lifecycle` | `register_run`, `mark_execution_start`, `mark_execution_end`, `is_cancel_requested`, `mark_failed`, `mark_completed`, `get_run_status`, `wait_for_quiescence` | 初回実験と再評価を別runとして登録し、実行フェーズ、失敗・完了、静止状態を管理 |
| `ai_data_scientist.lifecycle` | `mark_write_start`, `mark_write_end` | 書込みフェーズの管理。対象Notebookのフェーズ関数で参照し、制御側の保存フェーズでの直接利用をNotebookに記録 |
| `ai_data_scientist.data_definition` | `FieldValue`, `build_manifest`, `DataDefinitionManifest.unresolved_fields` | index 6で未取得ファイル・未確認定義をmanifest化し、index 13でも未解決項目を確認 |
| `ai_data_scientist.analysis_assumptions` | `Assumption`, `AnalysisAssumptionManifest`, `check_manifest` | index 6・13で取得前提の不成立、出所を置換しない条件、因果解釈の範囲を記録・検査 |
| `ai_data_scientist.insight_engine` | `extract_cited_value`, `record_insight` | 対象Notebookのindex 13でモジュールを直接import。関数呼び出しはNotebookに記録された制御セル側で行い、実出力のHTTPコードから根拠付き停止結論を保存 |
| `ai_data_scientist.notebook_audit` | `audit_notebook(visual_audit=True)` | index 11・13と制御側で、実行状態、証拠参照、図表を監査。見出し付き証拠の監査漏れの再現にも直接利用 |

実データを扱う `ingestion`, `cleaning`, `eda`, `stats_analysis`, `visualization`, `anomaly_detection`, `data_quality`, `sensitivity`, `dataset_validation` は未使用です。`mcp_gateway.run_and_record` も直接呼び出していません。Jupyter MCPを実行経路として使ったことを、Jupytermindの `mcp_gateway` 利用と読み替えません。Kaggle SDKやnbformatはJupytermindモジュールに含めません。

**初回指示**: 指定した `jsphyg/tipping` をKaggle Python SDKで検索・取得し、チップ額・チップ率と会計額、人数、曜日、時間帯などの関係を日本語で説明する依頼です。取得不能なら別ownerや外部CSVへ切り替えず停止すること、manifest、適用可能な異常検査・感度分析、根拠付きInsight、最大3回の自律的追加依頼、全セル再実行とライフサイクル記録が要求されました。

AIは、出所とハッシュの固定、欠損・型・範囲・カテゴリ・完全一致行の確認、`100 × tip / total_bill` によるチップ率、相関と群別図表、HC3頑健標準誤差付き回帰、仕様変更の感度分析を計画しました。会計ごとの平均率と金額加重率を区別し、率の分母共有、カテゴリ不均衡、未観測交絡を扱う方針も記録しています。これらは**分析計画であり、実施結果ではありません**。

### データ取得と初回結果

`initial.log` は、認証と一般検索が成功した一方、指定slugのファイル一覧APIがHTTP 403を返したため停止したと記録しています。対象Notebookの取得セルでは `KaggleApi()` の生成後に `authenticate()`、`dataset_list(search='tipping')`、`dataset_list(search='tips', user='jsphyg')`、`dataset_list_files('jsphyg/tipping')` を呼び出しています。一般検索の先頭20件だけで不存在と判断せず、owner限定検索と指定slugへの直接照会を追加しています。

最終保存された同セルの出力でも、認証は成功、一般検索は20件、owner限定検索は0件、ファイル一覧は `HTTPError`・HTTP 403でした。一般検索には別ownerのTips関連候補がありましたが、指定条件に従って採用していません。コードにはファイル取得後の `dataset_download_file(...)` とSHA-256算出が用意されているものの、ファイル一覧で停止しており、ダウンロード成功の証拠はありません。

| 出所・取得項目 | 確認できる状態 |
|---|---|
| 指定owner / dataset slug | `jsphyg` / `tipping`。ユーザー指定値であり、データ実体の取得確認ではない |
| 指定URL | `https://www.kaggle.com/datasets/jsphyg/tipping` |
| 初回再実行時の試行日時 | Notebook metadataに `2026-10-01T16:03:42.590835+00:00`。取得日時ではない |
| 追加確認を含む最終再実行時の試行日時 | `2026-10-01T16:10:16.802184+00:00`。取得日時ではない |
| 取得ファイル | 0件。初回の取得ファイル名は `null`、最終の取得ファイル一覧は空 |
| 取得日時・SHA-256 | いずれも `null`。未取得のため確認・算出不能 |
| 行数・列定義・単位・標本範囲 | 未確認。既知のTipsデータの数値で補完しない |

HTTP 403は**指定APIへのアクセス拒否を観測した証拠**です。データ削除、非公開化、権限制約のどれが原因かは特定できず、一般検索やowner限定検索の結果だけでデータ不存在とも断定できません。

初回結果は、チップ額・チップ率の相関や効果量ではなく、**原データを取得できず分析を停止したこと**です。データ定義manifestでは、想定する `total_bill`, `tip`, `sex`, `smoker`, `day`, `time`, `size` の定義・単位を `unknown` とし、標本数、観測単位、母集団、期間、ライセンスも未確認としています。7列が実在したという検証結果ではありません。

分析前提manifestでは、結論に必須の `target_available` が `rejected` となり、`unresolved_conclusion_critical_assumption` のwarningが1件あります。別owner・外部CSVへ置換しない条件は保持されました。データ読込み、クリーニング、EDA、相関・回帰、意味的異常検査、感度分析、独立データとの比較は、対象データがないため適用不能と記録されています。

**図表の扱い**: Notebookの出力に図表も `image/png` もありません。抽出できるPNGは0件のため、`benchmark/figures` に本実験の画像は保存しておらず、`figures/exp-04-...` の参照も設けていません。存在しない図や別経路のTips図表を掲載して取得成功を示すことはしません。

### AIが自律生成した追加依頼

初回の「反復依頼履歴」は0／最大3回です。原データ未取得のため初回分析結果の再評価による統計的な追加依頼はなく、ユーザーの停止条件を優先しています。これは「価値ある追加分析がなくなった」のではなく、「追加分析の対象がない」という停止です。

**追加依頼1（原文）— 指定データの取得可否を再確認**

> 指定Kaggle jsphyg/tippingについて、初回の取得失敗が現在も分析の結論を阻むか、同じ認証・owner限定検索・指定slugのファイルAPIを再実行して確認してください。別ownerや外部CSVへ置換しないでください。取得不能ならファイル名・取得日時・SHA-256を未取得として記録し、列定義、分析前提、異常値、感度、可視化、証拠manifestの適用不能と未解決点を区別してください。停止理由以外の統計的結論を生成せず、証拠参照とライフサイクルを検証してください。

**選定理由**: 問いに答えられないという結論を変え得る、操作可能な未解決点は、指定データの取得条件が回復したかどうかでした。再評価ではこの取得確認を保守的に追加依頼1回と数え、初回0回＋今回1回＝合計1／3回としています。取得に成功すれば停止結論を破棄して実ファイルから再計画し、失敗が続けば統計的結論を作らない、という停止条件も先に記録しました。

**結果・証拠**: Notebook metadata `followup.new_requests` によると、依頼文は `2026-10-01T16:09:12.737335+00:00` に記録され、index 3・13で実行されました。取得セルの `execution_count=2` はHTTP 403を返し、再評価セルの `execution_count=5` は取得ファイル・保存済みデータファイルがともに空であること、取得日時・SHA-256が `null` であることを確認しています。停止結論のevidenceも `execution_count=2`、引用値 `403` を指しています。

`followup.log` も、再取得でHTTP 403、チップ額・チップ率の問いは未回答、図表0件と報告しています。追加依頼は取得可否と証拠・状態の再評価を完了しましたが、統計分析を完了したわけではありません。

**残る限界・反復終了**: アクセス拒否の原因とデータ定義は依然として未確認です。原データなしで2・3回目の統計分析を追加しても根拠が得られないため、それらの依頼文は作成・実行されませんでした。再評価セルの埋込み文字列の改行escapeを修正して再実行した履歴もありますが、同じ依頼の修正検証であり、別の追加依頼には数えていません。

### 最終結論

**指定Kaggleデータのファイル一覧APIが初回・追加確認ともHTTP 403を返し、チップ額・チップ率に関係する特徴は検証できませんでした。** 相関の方向、大きさ、有意性、群間差、異常値の影響、因果関係に関する実データの結論はありません。別owner・外部CSVへの切替を行わず、出所条件と停止条件を守った実験として、取得失敗と未回答を報告します。

`status.json` の `analysis_complete=false`、`final_completion.ready=false`、Notebookの `analysis_completed=false` と未取得の内容が一致しています。`final_completion.requirements` では `has_chart_output=false` であり、構造監査や根拠付き停止記録などの条件を満たしていても、分析完了とはなっていません。再評価runの `completed` は再評価タスクの終了を表し、初回runの `failed` や実データ分析の未完了を覆しません。

### 監査・再現性

初回ログとNotebookに保持された初回metadataでは、カーネル再起動後に全4／4コードセルを上から再実行し、HTTP 403による停止を再現しています。初回の最終 `audit_notebook(visual_audit=True)` は `ok=True`、nbformat正常、未実行0、セルエラー0、証拠1件、図表0件、findings 0件、visual_findings 0件でした。初回run `v020-exp-04` は `failed` です。

追加確認後のNotebookは15セル、そのうちコードセルは5件です。metadata `reexecution` は、新規カーネルでindex 1 → 3 → 6 → 11 → 13をJupyter MCPの `execute_cell` で順番に実行し、実行カウント1～5を保存したと記録しています。再実行完了日時は `2026-10-01T16:11:34.816925+00:00` です。

| 最終保存時の確認項目 | 結果 |
|---|---|
| `audit_notebook(visual_audit=True)` | `ok=True`、`nbformat_valid=True` |
| コードセル実行 | 5／5、未実行0、セルエラー0 |
| 根拠付き停止結論 | 2件。全evidence fenceの実出力照合も2／2成功 |
| 図表・visual findings | 図表0件、visual_findings 0件。図の可読性を検証した結果ではない |
| 最終監査findings | 0件 |
| 分析前提の警告 | 取得前提不成立のwarning 1件を保持。Notebook監査のfindingsとは別 |
| 初回run | `v020-exp-04` は `failed` |
| 再評価run | `v020-exp-04-followup` は `completed` |
| 両runの静止状態 | 実行中セル、書込み待ち、保持ロックはいずれも0 |

index 13の実行中に行った自己監査には、末尾の監査セルがまだ実行中であるというwarningがあり、監査時点の実行済み数は4／5でした。上表はその途中出力ではなく、全セル終了後に制御側から行った最終監査metadataの値です。見出し付き証拠の監査漏れを補うため、見出しの有無にかかわらず全evidence fenceも別途照合されています。

外部実行プロセスについては、`status.json` の初回・追加確認とも終了コード0、terminationは `exited`、所要時間はそれぞれ578.6秒・386.7秒です。保存安定性も両方 `stable=true` です。これらはプロセス終了と成果物の安定性を示すだけで、データ取得や分析の成功を示しません。

再現できたのは**取得不能時の停止・manifest・証拠・監査状態**です。データファイルがなくSHA-256も存在しないため、データ内容や統計値の再現性は検証できません。また、将来APIの応答が変われば分析を再計画する必要があります。

### 失敗内容とJupytermind改善候補の切り分け

分析を阻んだ直接の失敗はKaggleの `dataset_list_files('jsphyg/tipping')` に対するHTTP 403です。認証や一般検索の失敗ではなく、Jupytermindの統計処理で発生した失敗でもありません。Copilot CLIまたは外部ベンチマークランナー固有の不具合を、提示された実ファイルから確定できる証拠はありません。

**Jupytermind改善候補は1件: 見出し付きevidenceの監査漏れ。** 初回ログは改善候補2件と報告していましたが、再評価では原因未分離の統合問題を除外し、単体再現した1件に絞っています。

| 項目 | 実ファイルに基づく記録 |
|---|---|
| 分類・対象 | 証拠監査の対象検出不足。`ai_data_scientist.notebook_audit.audit_notebook` |
| 再現手順 | 実行済みコードの出力が403の一時Notebookに、`execution_count=1`・引用値999の不一致evidenceを持つMarkdownを置いて監査する。Markdown先頭を見出しと太字に変え、他の条件を同じにして比較する |
| 期待する挙動 | 明示的evidenceがあれば先頭記法にかかわらず検査し、実出力にない999の引用を不合格にする |
| 実際の挙動 | 見出し先頭は `ok=True`、`insight_cell_count=0`、findings 0件。太字先頭は `ok=False`、`insight_cell_count=1`、引用999が出力に存在しないというerror 1件 |
| 影響 | 見出し付き結論の古い・誤った引用が監査を通過し得る。今回のKaggle取得失敗の原因ではない |
| 証拠 | Notebook「Jupytermind改善候補」節、metadata `followup.heading_reproduction.heading` / `.bold`、`followup.log`。KaggleやMCP同期を介さない一時Notebookでの比較結果を記録 |
| 回避策 | 実際の停止結論は太字先頭で記録し、全evidence fenceも別途実出力へ照合 |
| 受け入れ条件 | 見出し・太字・通常文で同数の明示evidenceを検査。一致引用は合格、不一致値・不存在実行カウント・不正JSON・必須キー欠落は全形式で不合格。証拠のない計画見出しは結論と誤認せず、既存の非見出し検査とvisual_auditを維持 |

この比較で実測されたのは「不一致引用」の見出し／太字差です。不正JSONや必須キー欠落などは、既に確認された不具合としてではなく、修正後に満たすべき受け入れ条件として扱います。実際の停止結論が誤っていたことを示すものでもありません。

旧候補の「実行中Notebookの自己書込みとMCP出力同期」は、Notebook metadataに観測が残っていますが、Jupytermind単体再現がなく、外部MCPの保存競合でも説明できるため、確定的な製品改善候補から除外しました。対象セル終了後に別の制御Notebookから保存する運用上の回避は記録されています。未作成親ディレクトリへのMCP作成拒否は外部ツール制約、検索先頭ページだけによる未発見は実行手順の問題であり、同じ候補には含めません。追加セルの改行escape修正も、生成したNotebookコードの修正履歴であってJupytermind本体の不具合とは認定しません。

改善候補の分類、再現手順、期待・実際の挙動、影響、証拠、受け入れ条件は、本実験runディレクトリの `issue-candidate.json` に保存しています。製品ソースの修正やGitHub Issue登録を実施したという記録ではありません。

### 残る限界

原データの行数、実在する列、通貨、会計額へのチップの包含、人数の意味、店舗・地域・期間・標本設計は未確認です。異常値、完全一致行、独立性、カテゴリ構成、相関・回帰の安定性、図表の可読性を検証済みとは扱えません。Notebookの計画にある正の会計額、非負のチップ、正の整数人数、率の極端値や重複の検査、Pearson／SpearmanやHC3モデルの比較は未実施です。

仮に取得できても、非無作為抽出、未観測の店舗・担当者・顧客差、反復観測の可能性、チップ率の分母共有、曜日と時間帯の構成差を別途検討する必要があります。これらは現時点で実データから確認された性質ではなく、分析再開時に残る検証課題です。監査合格は統計的妥当性、因果識別、取得成功の保証ではありません。

**証拠範囲**: 本節の実験結果は、指定Notebook、`initial-prompt.md`、`initial.log`、`followup.log`、`status.json` のみを根拠としています。`white-paper2.md` は節の詳細度と書式の参照に限り、旧版のGitHub CSV再実験・統計値・図表は流用していません。`status.json` の文書化状態を示す `documentation_complete`、トップレベルの `semantic_complete`、`report_exit_code` は、分析の見出し・結論・失敗判定に用いていません。
