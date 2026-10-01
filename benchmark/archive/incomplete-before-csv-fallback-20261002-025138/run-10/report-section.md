## 実験10: Students Performance in Exams（Jupyter MCP実行ツール未公開により分析未実施）

**課題**: 「KaggleのStudents Performanceデータで、試験成績の差に結びつく要因を調べてください。」

**初回プロンプト（全文・原文）**: 「KaggleのStudents Performanceデータで、試験成績の差に結びつく要因を調べてください。分析計画、比較方法、図表は自分で決め、交絡や自己選択の可能性を含む限界を日本語で説明してください。AI Data Scientist SkillとJupyter MCPを使い、コード・結果・根拠付きInsightをノートブックに記録し、再実行可能か検証してください。 Kaggle参照先: https://www.kaggle.com/datasets/spscientist/students-performance-in-exams。インストール済みkaggle Python SDKを使い、NotebookのJupyter MCP実行セル内で`KaggleApi().authenticate()`、`dataset_list(search=...)`、`dataset_list_files(...)`、必要に応じて`dataset_download_file(...)`を呼び出し、Kaggle上の対応する公開データを検索・取得してください。外部CSVミラーは使用しないでください。owner/dataset slug、取得ファイル名、取得日、ファイルSHA-256をNotebookに記録してください。APIトークンをセル出力・Notebook・ログへ表示しないでください。分析・API取得コードの実行はJupyter MCPだけを使い、端末コマンド、subprocess、外部スクリプト起動、作業エージェントへの委譲は行わないでください。APIで対応するデータが見つからない場合は外部ソースにフォールバックせず、その実験を停止して理由を報告してください。保存先は benchmark/projects/kaggle-v020-kaggle-exp-10-students/notebooks/kaggle-v020-kaggle-exp-10-students.ipynb としてください。run_idは `v020-exp-10` です。長時間処理の開始前にlifecycle.register_runを呼び、実行・書込みフェーズを記録し、終了時にcompletedまたはfailedを記録してください。データ定義manifest、分析前提manifest、意味的な異常検査、妥当な範囲の感度分析を使い、適用できない機能は理由を記録してください。図表はvisual_audit=Trueで監査してください。Notebookには「使用したJupytermindモジュール」節を設け、直接import・呼び出したモジュール名、関数名、使用目的を記録してください。間接利用は使用済みに含めないでください。Jupytermindの不具合または機能不足が疑われた場合は「Jupytermind改善候補」節を設け、分類、再現条件、期待する挙動、実際の挙動、影響、回避策、関係するセルとログを記録してください。Copilot CLI、Kaggle API、ベンチマークランナーに固有の問題とは切り分け、候補がなければ「なし」と記録してください。初回分析後、自分で結果を読み直し、結論に実質的な影響を与える未解決点があれば自然言語の追加依頼文を作成し、Notebookの「反復依頼履歴」に原文のまま記録して実行してください。価値ある追加分析がなくなるまで最大3回繰り返し、各反復の選定理由・結果・証拠・残る限界を報告してください。最後に全コードセルを上から再実行し、notebook_auditとライフサイクル状態を記録してください。」

**使用したJupytermindモジュール**: Notebookが存在しないため、Notebookで直接import・呼び出しが確認できたモジュール・関数はありません。初回ログは `lifecycle.register_run` と `notebook_audit` の未実施を明記しています。前者は実行開始・フェーズ・終了状態の記録、後者はNotebook監査として依頼されたものですが、実際に使用した機能には含めません。

**初回指示**: 成績差に関係する要因を調べるため、分析計画・比較方法・図表の選択をAIに委ね、交絡と自己選択を含む限界の説明を求めました。取得経路はJupyter MCP上のKaggle Python SDKに限定し、出典・ファイル・取得日・SHA-256を記録する条件でした。さらに、データ定義・分析前提のmanifest、意味的な異常検査、感度分析、`visual_audit=True` による図表監査、最大3回の自律的な追加依頼、全コードセルの再実行と監査を要求しました。これらは要求事項であり、実施済みの処理ではありません。

### データ取得

**Kaggle APIによるデータ取得は未実施です。** `initial.log` は、Jupyter MCPの実行・Notebook操作ツールがセッションに公開されておらず、ツール検索でも見つからなかったと報告しています。指定された実行経路を確保できず、Kaggle API認証・検索・取得より前に停止しました。

参照先URLに含まれる `spscientist/students-performance-in-exams` は取得対象として指定されたslugであり、取得済みデータの来歴ではありません。ファイル一覧、取得ファイル名、取得日、SHA-256、行数・列数、欠損・重複の状態はいずれも確認できません。Kaggle上に対応データがないと判定したわけでも、認証エラーやダウンロードエラーを確認したわけでもありません。

初回ログは、端末・subprocess・外部スクリプト・作業エージェント・外部CSVミラーによる代替を行わず、APIトークンも参照・表示していないと報告しています。参照したログにトークン値は記載されていません。ただし、ログは実行者による結果報告であり、個々のツール呼び出しを検証できるトレースは含まれていません。

### 初回結果と失敗内容

**成績差についての分析結果はありません。** 初回ログの冒頭は、次のとおりです。

> **分析は未実行です。Jupyter MCPがこのセッションの利用可能なツールに公開されていないため、指定された実行経路を確保できませんでした。**

同ログは、Notebookを作成しておらず、分析、再実行検証、`notebook_audit`、`lifecycle.register_run` はいずれも未実施と説明しています。指定先のNotebookが存在しないことは、今回の実ファイル確認と `status.json` の `notebook_missing` 記録でも整合します。群間差、効果量、回帰係数、信頼区間、検定結果、根拠付きInsightは確認できず、成績差の要因について推定値を掲載できません。

`status.json` の初回プロセス記録は `initial_exit_code=0`、`initial_seconds=46.0`、`initial_termination="exited"` です。しかし、これは初回プロセスの終了を表すだけで、分析成功を意味しません。`analysis_complete=false`、`final_completion.ready=false` と成果物の不存在、初回ログの未実行宣言を併せて、**指定経路で分析を開始できなかった実験**と判断します。プロセスの異常終了や分析コードの計算エラーとは区別します。

### AIが生成した追加依頼

**追加依頼の原文・選定理由・結果は確認できません。** 初回ログには自然言語の追加分析依頼がなく、反復依頼履歴を記録するNotebookもありません。指定された `followup.log` は存在せず、`status.json` の `followup_exit_code`、`followup_seconds`、`followup_termination` はすべて `null` です。

したがって、追加依頼1〜3の原文や選定理由を補って掲載することはできません。これは「追加分析の価値がなくなったので終了した」という判断ではなく、初回分析が未実施で、結果に基づく反復の証拠がない状態です。初回ログ末尾の「このセッションへJupyter MCPのNotebook・セル実行ツールを公開すること」は実行環境の必要条件の説明であり、AIが生成・実行した追加分析依頼には数えません。

### 最終結論

**Students Performance in Examsの試験成績の差に結びつく要因は、本実験では評価できませんでした。** データを取得していないため、関連の有無や強さ、交絡調整後の差、自己選択の影響について結論を出せません。「要因と成績に関係がない」という結果でもありません。

確認できたのは、初回ログがJupyter MCP実行ツールの未公開を阻害理由として報告し、Notebookを作成しないまま終了したことです。`analysis_complete`、`final_completion`、Notebookの存在確認に基づく分析完了判定は未完了です。プロセス終了コード0のみで、データ分析や再現性確認の成功を判定できないことも示しています。

### 監査・再現性

| 確認項目 | 実ファイルで確認できた状態 |
|---|---|
| 実験識別子 | `run_id="v020-exp-10"`。初回プロンプトと `status.json` に記録されています。 |
| Notebook | `benchmark/projects/kaggle-v020-kaggle-exp-10-students/notebooks/kaggle-v020-kaggle-exp-10-students.ipynb` は存在しません。 |
| データ来歴 | 認証・検索・取得は初回ログ上で未実施。取得ファイル・取得日・SHA-256の記録はありません。 |
| 実行コード・出力・Insight | Notebookがなく、分析の実行証拠はありません。 |
| manifest・意味的な異常検査・感度分析 | 実施を示すNotebookセル・結果はありません。 |
| ライフサイクル | 初回ログは `lifecycle.register_run` 未実施と報告。実行・書込みフェーズと `completed` / `failed` の記録は確認できません。 |
| 全コードセルの上からの再実行 | 初回ログで未実施と報告されています。 |
| `notebook_audit`・図表監査 | 初回ログでNotebook監査は未実施。`visual_audit=True` の実行結果もありません。 |
| 外部の成果物確認 | `initial_audit`、`final_audit` はともに `exists=false`、`error="notebook_missing"`。Jupytermindの監査を実行した結果とは区別します。 |
| 完了条件 | `final_completion.requirements` の構造監査、最低実行コードセル数、図表出力、根拠付きInsight、反復履歴、モジュール使用記録、改善候補記録、Notebook監査呼び出しの8条件はすべて `false` です。 |

**図表**: Notebookが存在しないため、抽出できるPNG出力はありません。`benchmark/figures` への `exp-10-` で始まる画像の保存や、節内の画像参照は行っていません。別実験の図表や再生成図で代用すると、この実験の出力と誤認されるためです。

証拠は `benchmark/runs/10-kaggle-exp-10-students/initial-prompt.md`、`initial.log`、`status.json` と、指定されたNotebookおよび `followup.log` の不存在確認です。既存の白書は節の書式・詳細度の参考に限り、そこに記載された別バージョンの分析数値・図表・成功状態は本実験の証拠として使用していません。再実行可能性は未検証であり、この節の作成によって分析が完了したことにはなりません。

### Jupytermind改善候補と外部要因の切り分け

**今回の証拠から登録できるJupytermind固有の改善候補はありません。** NotebookでJupytermindモジュールを直接実行した証拠がなく、関数の不具合や機能不足を再現した記録もありません。候補ファイル `benchmark/runs/10-kaggle-exp-10-students/issue-candidate.json` にはJSONの `null` を保存します。これは不具合が存在しないことの証明ではなく、この実験で候補を裏付ける証拠がないという意味です。

| 切り分け対象 | 証拠に基づく判断 |
|---|---|
| Jupytermind | モジュール実行が確認できず、分析機能の不具合とは判断できません。 |
| Copilot CLI・MCP公開設定などの実行環境 | 初回ログはセッションへのJupyter MCPツール未公開を報告。設定内容やサーバーの診断記録がないため、具体的な原因や責任箇所は特定できません。 |
| Kaggle API | 認証・検索・取得より前に停止しており、API障害、権限不足、対象データの不存在は確認していません。 |
| 外部ベンチマークランナー | プロセス終了コード0を記録する一方、`analysis_complete=false` と `final_completion.ready=false` も記録しています。終了コードのみを成功扱いする解釈は不適切ですが、ランナーが分析成功と誤判定した証拠はありません。 |

### 限界

最大の限界は、対象データと分析成果物を確認できないことです。標本構成、変数定義、抽出地域・時点、成績の尺度、欠損、交絡、自己選択は実証的に検討できていません。これらを一般的な注意点として挙げることはできても、当該データで確認された問題とは扱えません。

また、初回ログは最終報告文であり、ツール検索やMCP接続の詳細トレースはありません。ツール未公開という報告以上に、サーバー停止、プロトコル不一致、CLIの不具合、設定ミスなどの原因を推測できません。追加確認ログもないため、環境復旧や再試行の結果は評価対象に含められません。本実験は分析計画・統計手法・反復分析の能力を測る段階に到達しておらず、Jupytermind v0.2.0の分析能力全体への評価には一般化できません。
