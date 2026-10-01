## 実験15: Dots（Jupyter MCP実行経路を利用できず分析未実施）

**課題**: 「Kaggle検索で見つかる知覚実験のDotsデータで、刺激条件と反応時間・判断の関係を調べてください。」

**初回プロンプト（全文・原文）**: 「Kaggle検索で見つかる知覚実験のDotsデータで、刺激条件と反応時間・判断の関係を調べてください。変数の意味と実験単位を自分で把握して計画し、適切な図表と統計を選び、解釈の限界を説明してください。AI Data Scientist SkillとJupyter MCPを用い、計画・コード・出力・根拠付きInsightを保存し、再実行してください。 Kaggle参照先: https://www.kaggle.com/datasets?search=dots+perception+experiment。インストール済みkaggle Python SDKを使い、NotebookのJupyter MCP実行セル内で`KaggleApi().authenticate()`、`dataset_list(search=...)`、`dataset_list_files(...)`、必要に応じて`dataset_download_file(...)`を呼び出し、Kaggle上の対応する公開データを検索・取得してください。外部CSVミラーは使用しないでください。owner/dataset slug、取得ファイル名、取得日、ファイルSHA-256をNotebookに記録してください。APIトークンをセル出力・Notebook・ログへ表示しないでください。分析・API取得コードの実行はJupyter MCPだけを使い、端末コマンド、subprocess、外部スクリプト起動、作業エージェントへの委譲は行わないでください。APIで対応するデータが見つからない場合は外部ソースにフォールバックせず、その実験を停止して理由を報告してください。保存先は benchmark/projects/kaggle-v020-kaggle-exp-15-dots/notebooks/kaggle-v020-kaggle-exp-15-dots.ipynb としてください。run_idは `v020-exp-15` です。長時間処理の開始前にlifecycle.register_runを呼び、実行・書込みフェーズを記録し、終了時にcompletedまたはfailedを記録してください。データ定義manifest、分析前提manifest、意味的な異常検査、妥当な範囲の感度分析を使い、適用できない機能は理由を記録してください。図表はvisual_audit=Trueで監査してください。Notebookには「使用したJupytermindモジュール」節を設け、直接import・呼び出したモジュール名、関数名、使用目的を記録してください。間接利用は使用済みに含めないでください。Jupytermindの不具合または機能不足が疑われた場合は「Jupytermind改善候補」節を設け、分類、再現条件、期待する挙動、実際の挙動、影響、回避策、関係するセルとログを記録してください。Copilot CLI、Kaggle API、ベンチマークランナーに固有の問題とは切り分け、候補がなければ「なし」と記録してください。初回分析後、自分で結果を読み直し、結論に実質的な影響を与える未解決点があれば自然言語の追加依頼文を作成し、Notebookの「反復依頼履歴」に原文のまま記録して実行してください。価値ある追加分析がなくなるまで最大3回繰り返し、各反復の選定理由・結果・証拠・残る限界を報告してください。最後に全コードセルを上から再実行し、notebook_auditとライフサイクル状態を記録してください。」

**使用したJupytermindモジュール**: Notebookで直接import・呼び出したモジュール名、関数名、使用目的を確認できる記録はありません。指定Notebookは存在せず、初回ログもNotebookを作成していないと報告しています。したがって、使用済みモジュールの一覧は作成できません。`lifecycle.register_run` と `notebook_audit` は初回指示に含まれる実行要件ですが、初回ログでは未実施とされています。要求された関数や間接的な利用を、直接使用したモジュールとして数えません。

**初回指示**: 刺激条件と反応時間・判断の関係を調べるにあたり、変数の意味と実験単位の把握、分析計画、図表、統計手法の選択をAIに委ねました。データ取得と分析コードの実行はJupyter MCPに限定し、Kaggle APIで検索・取得すること、外部CSVミラーを使わないこと、取得来歴とSHA-256をNotebookに保存することを求めています。さらに、データ定義・分析前提のmanifest、意味的な異常検査、感度分析、`visual_audit=True` の図表監査、ライフサイクル記録、最大3回の自律的な追加依頼、全コードセルの再実行と最終監査を指定しました。追加分析の内容そのものは事前に指定していません。

**データ取得**: 未実施です。初回ログはKaggleの認証・検索・取得をいずれも行っていないと報告しています。`KaggleApi().authenticate()`、`dataset_list(search=...)`、`dataset_list_files(...)`、`dataset_download_file(...)` の実行出力はなく、owner/dataset slug、取得ファイル名、取得日、SHA-256、行数・列数は確認できません。検索URLは課題の手がかりであり、取得済みデータの出典ではありません。Kaggle APIのエラーや検索結果もないため、「対応する公開データが存在しない」「認証に失敗した」とは判定できません。初回ログでは、外部CSVミラーへの切替とAPIトークンの取得・表示を行わなかったと報告していますが、取得セルによる確認記録はありません。

**初回結果**: データ分析に入る前に停止しました。初回ログの停止理由は次のとおりです。

> Jupyter MCPの実行ツールがこのセッションに公開されていないため、分析は未実施です。

ログには、Jupyter MCPのツール検索を行ったが利用可能なツールは0件だったという報告があります。ただし、提示されたログに検索呼び出しと応答の詳細はなく、この件数はAIによる報告として扱います。同ログは、端末、subprocess、外部スクリプト、作業エージェントによる代替実行を行わず、指定Notebookも作成しなかったと明示しています。分析計画を具体化したNotebook、変数定義、実験単位の確認、統計結果、図表、根拠付きInsightはありません。

`status.json` の `initial_exit_code` は `0`、`initial_seconds` は `48.0`、`initial_termination` は `exited` です。これは初回プロセスが終了した記録であり、データ取得や分析の成功を意味しません。実際、`initial_stability.exists=false` と `initial_audit.error="notebook_missing"` が記録されています。

**AIが生成した追加依頼 — 原文・選定理由・結果**: 確認できる追加分析の依頼文はありません。指定された `followup.log` は存在せず、Notebookの「反復依頼履歴」も確認できません。`status.json` の `followup_exit_code`、`followup_seconds`、`followup_termination` はすべて `null` です。したがって、追加依頼の原文、選定理由、実行結果、証拠、各反復で残った限界を記載する根拠はありません。これは「初回結果を検討した結果、価値ある追加分析がなくなった」という判断ではなく、初回分析そのものを実施できなかった状態です。

**図表**: 指定Notebookが存在しないため、Notebook内のPNG出力を抽出できませんでした。`benchmark/figures` に本実験の画像は新規保存しておらず、対応する `figures/exp-15-...` 参照やキャプションも設けていません。別バージョンの実験や他のNotebookの図表で補うことはしていません。

**最終結論**: Jupytermind v0.2.0の実験15は、指定されたJupyter MCP実行経路を利用できないという初回ログの報告により、分析未実施で終了しました。`status.json` の `analysis_complete=false`、`final_completion.ready=false`、指定Notebookの不在が、この判断を裏付けます。刺激条件と反応時間・判断の関係について、関連の有無、効果の大きさ、統計的有意性を結論づける根拠はありません。「関連がない」という分析結果でも、Jupytermindによる分析能力が実証された結果でもありません。

**監査・再現性**: 最終状態は次のように記録されています。

| 確認対象 | 記録・確認できた状態 | 解釈 |
|---|---|---|
| 指定Notebook | 実ファイルなし。`final_stability.exists=false`、`stable=false` | 分析コード・出力を検査、再実行できない |
| 最終監査 | `final_audit.exists=false`、`error="notebook_missing"` | Notebook不在の検出であり、Notebookに対する監査合格ではない |
| 完了判定 | `analysis_complete=false`、`final_completion.ready=false` | 分析は未完了 |
| 完了要件 | 構造監査、最低実行コードセル数、図表出力、根拠付きInsight、反復履歴、モジュール使用記録、改善候補記録、Notebook監査呼び出しの8項目がすべて `false` | 成果物に基づく完了条件を満たしていない |
| ライフサイクル | 初回ログで `lifecycle.register_run("v020-exp-15")` は未実施と報告 | 登録・フェーズ遷移・終了状態の実行記録は確認できない |
| 全セル再実行 | 初回ログで未実施と報告。Notebookなし | データ取得・統計値・図表の再現性は未検証 |
| manifest・意味的検査・感度分析・図表監査 | Notebook内のコード・出力なし | 実行済みとも、適用できないと評価済みとも扱えない |

初回プロンプト、初回ログ、監査状態は、それぞれ `benchmark/runs/15-kaggle-exp-15-dots/initial-prompt.md`、`initial.log`、`status.json` に保存されています。指定されたNotebookのパスは `benchmark/projects/kaggle-v020-kaggle-exp-15-dots/notebooks/kaggle-v020-kaggle-exp-15-dots.ipynb`、追加確認ログのパスは `benchmark/runs/15-kaggle-exp-15-dots/followup.log` ですが、どちらも本節作成時には存在しませんでした。監査状態の `completed_at` は `2026-10-01T17:20:11.433153+00:00` です。この時刻は状態記録の値であり、データ取得日や分析完了日時とはみなしません。

**失敗内容と責任範囲の切り分け**: 確認できる失敗は、指定実行経路を利用できず、要求された分析成果物を生成できなかったことです。初回ログが報告する問題は、Copilot CLIセッションにおけるJupyter MCPツールの公開・接続という実行環境上の制約です。ただし、外部ランナーの設定、CLIのツール探索、MCPサーバーの接続のどこに原因があるかを特定する詳細証拠はありません。Kaggle APIは呼び出されていないため、API障害やデータ不存在には帰属させません。Jupytermindモジュールの直接呼び出しや例外記録もないため、Jupytermind本体の不具合とは判定しません。

**Jupytermind改善候補**: この実験の証拠から登録できる候補はありません。Notebook不在や実行経路の制約だけを、Jupytermindモジュールの機能不足に置き換えることはできません。`benchmark/runs/15-kaggle-exp-15-dots/issue-candidate.json` にはJSONの `null` を保存します。これはJupytermindに不具合がないという保証ではなく、本実験では候補を裏付ける直接実行の証拠が得られなかったという判断です。

**残る限界**: データを取得していないため、Dotsという名称から行動実験データか集約神経活動データかを推定しません。変数の意味、時刻・反応時間の区別、参加者・試行・集約系列という実験単位、標本数、欠損、反復測定構造、交絡、統計手法の適否はすべて未確認です。参照した `white-paper2.md` は節の書式と詳細度を合わせるためだけに用い、その別バージョンの取得元、数値、図表、成功状態を本実験の証拠に流用していません。本実験から評価できるのは、分析未実施であることを報告して終了したという範囲までであり、分析の妥当性、可視化の有用性、反復の有効性、結果の再現性は評価できません。
