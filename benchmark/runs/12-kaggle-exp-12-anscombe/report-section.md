## 実験12: Anscombe's Quartet（分析完了）

**課題**: 「KaggleのAnscombe's Quartet例を調べ、要約統計が似ている複数群を同じ結論として扱ってよいか検証してください。」

**初回プロンプト（全文・原文）**: 「KaggleのAnscombe's Quartet例を調べ、要約統計が似ている複数群を同じ結論として扱ってよいか検証してください。どの可視化と比較が必要か自分で判断し、数値だけでは見えない違いを日本語で説明してください。AI Data Scientist SkillとJupyter MCPを使い、分析計画・実行コード・結果・根拠付きInsightを保存し、再実行を確かめてください。 Kaggle参照先: https://www.kaggle.com/code/tomarns/anscombe-s-quartet。インストール済みkaggle Python SDKを使い、NotebookのJupyter MCP実行セル内で`KaggleApi().authenticate()`、`dataset_list(search=...)`、`dataset_list_files(...)`、必要に応じて`dataset_download_file(...)`を呼び出し、Kaggle上の対応する公開データを検索・取得してください。外部CSVミラーは使用しないでください。owner/dataset slug、取得ファイル名、取得日、ファイルSHA-256をNotebookに記録してください。APIトークンをセル出力・Notebook・ログへ表示しないでください。分析・API取得コードの実行はJupyter MCPだけを使い、端末コマンド、subprocess、外部スクリプト起動、作業エージェントへの委譲は行わないでください。APIで対応するデータが見つからない場合は外部ソースにフォールバックせず、その実験を停止して理由を報告してください。保存先は benchmark/projects/kaggle-v020-kaggle-exp-12-anscombe/notebooks/kaggle-v020-kaggle-exp-12-anscombe.ipynb としてください。run_idは `v020-exp-12` です。長時間処理の開始前にlifecycle.register_runを呼び、実行・書込みフェーズを記録し、終了時にcompletedまたはfailedを記録してください。データ定義manifest、分析前提manifest、意味的な異常検査、妥当な範囲の感度分析を使い、適用できない機能は理由を記録してください。図表はvisual_audit=Trueで監査してください。Notebookには「使用したJupytermindモジュール」節を設け、直接import・呼び出したモジュール名、関数名、使用目的を記録してください。間接利用は使用済みに含めないでください。Jupytermindの不具合または機能不足が疑われた場合は「Jupytermind改善候補」節を設け、分類、再現条件、期待する挙動、実際の挙動、影響、回避策、関係するセルとログを記録してください。Copilot CLI、Kaggle API、ベンチマークランナーに固有の問題とは切り分け、候補がなければ「なし」と記録してください。初回分析後、自分で結果を読み直し、結論に実質的な影響を与える未解決点があれば自然言語の追加依頼文を作成し、Notebookの「反復依頼履歴」に原文のまま記録して実行してください。価値ある追加分析がなくなるまで最大3回繰り返し、各反復の選定理由・結果・証拠・残る限界を報告してください。最後に全コードセルを上から再実行し、notebook_auditとライフサイクル状態を記録してください。」

**使用したJupytermindモジュール**: Notebookのコードセルで直接import・呼び出したものだけを示します。関数名の記載は直接の利用を意味し、間接利用や単なる言及は含めません。

| モジュール | 直接呼び出した関数・クラス・メソッド | 使用目的 |
|---|---|---|
| `ai_data_scientist.project_manager` | `resolve_project`、`ensure_notebook`、`ensure_data_dir`、`enqueue_write` | プロジェクト・Notebook・データ保存先の解決とNotebook書込みの直列化 |
| `ai_data_scientist.lifecycle` | `register_run`、`mark_execution_start`、`mark_execution_end`、`mark_write_start`、`mark_write_end`、`is_cancel_requested`、`mark_failed`、`mark_completed`、`get_run_status`、`wait_for_quiescence` | run_idの登録、実行・書込みフェーズ、取消確認、失敗時処理、完了・静止状態の記録 |
| `ai_data_scientist.language_router` | `detect_language` | 日本語の指示であることの判定 |
| `ai_data_scientist.ingestion` | `SourceSpec`、`ingest` | Kaggle APIで取得済みのCSV読込みと行上限確認 |
| `ai_data_scientist.cleaning` | `clean_dataset` | x・yの欠損除去による影響確認 |
| `ai_data_scientist.eda` | `explore` | 型、欠損、カテゴリ、基本統計の確認 |
| `ai_data_scientist.data_definition` | `FieldValue`、`build_manifest`、`DataDefinitionManifest.unresolved_fields` | 出典・変数定義と、verified／inferred／unknownの区別 |
| `ai_data_scientist.analysis_assumptions` | `Assumption`、`AnalysisAssumptionManifest`、`check_manifest` | 分析前提、結論に重要な未検証前提、関連分析の範囲の記録 |
| `ai_data_scientist.data_quality` | `detect_anomalies` | 群カテゴリ・行番号・キー一意性・欠損に関する意味的スキーマ検査 |
| `ai_data_scientist.stats_analysis` | `correlation` | 群ごとのPearson相関と日本語の係数解釈 |
| `ai_data_scientist.visualization` | `build_image_output` | Matplotlibで作った複合図をPNG MIME出力としてNotebookに記録 |
| `ai_data_scientist.sensitivity` | `SensitivityPlan`、`run_sensitivity` | 1点除去、モデル次数、影響点閾値、丸め幅・seedの感度分析とNaN入力の最小再現 |
| `ai_data_scientist.insight_engine` | `extract_cited_value`、`record_insight` | 保存済み出力から引用値を抽出し、実行カウント付きのEvidence manifestでInsightを保存 |
| `ai_data_scientist.notebook_audit` | `audit_notebook` | `visual_audit=True`による構造・証拠・図表の最終監査 |

`mark_failed`は失敗時分岐の呼出であり、正常終了した本実験がfailedになったことを意味しません。OLS・二次回帰、設計行列のランク、残差、レバレッジ、Cook距離、LOOCVはNotebook内のNumPy等によるコード、Theil–SenはSciPyで計算しています。これらをJupytermindの統計関数が提供した機能とは数えません。

**初回指示**: 手法を指定せず、同じ要約統計から同じ結論を導いてよいかを、AI自身が可視化と比較を選んで検証するよう依頼しました。Kaggle API限定の取得、取得元・ハッシュの記録、Jupyter MCPでの実行、manifest・意味的検査・感度分析、最大3回の自律的な追加依頼、全セル再実行と完了状態の記録を要求しました。

AIがNotebookに保存した計画は、4群を共通軸の散布図で比較し、OLS残差、影響度と1点除去、線形／二次モデルのLOOCV、観測されたxの配置を調べるものでした。外れた点や繰り返すxを自動削除せず、教材内の記述・関連分析に限定しています。独立した参照観測がないため外部データによる妥当性検証は非適用としました。また、呼出側のMCPClientがカーネルに公開されないため専用の実行記録ラッパーは直接利用せず、Jupyter MCPのセル実行と実際の出力保存を用いた、とNotebookに理由が記録されています。

**データ取得**: Notebookの実行カウント2〜4で、`KaggleApi().authenticate()`、`dataset_list(search='anscombe')`、`dataset_list_files(...)`、`dataset_download_file(...)`を実行しています。検索結果とファイル一覧を確認し、`carlmcbrideellis/data-anscombes-quartet` の `Anscombe_quartet_data.csv`を取得しました。同データセットにはQuintet用CSVもありましたが、分析対象にはしていません。

| 項目 | Notebookに残る取得・構造情報 |
|---|---|
| owner/dataset slug | `carlmcbrideellis/data-anscombes-quartet` |
| 取得ファイル | `Anscombe_quartet_data.csv` |
| 取得日時 | `2026-10-01T17:05:51.279178+00:00`（UTC。保存された再実行後の記録） |
| SHA-256 | `21dd4998e5985a2717e1ca154e3f90ac7657e8e71c6564096d92addf3c5a36b9` |
| 元データ | 11行・6列：`x123`、`y1`、`y2`、`y3`、`x4`、`y4` |
| 分析用データ | I〜IIIは`x123`と各y、IVは`x4`と`y4`を対応させ、各群11点、計44行の長形式へ変換 |

Kaggle参照Notebookも`kernels_pull('tomarns/anscombe-s-quartet', ...)`で取得し、コード2セル・Markdown1セル、seabornのAnscombeローダーと相関計算を含むことを確認しています。ただし`dataset_sources`は空です。**今回取得したCSVが参照Notebookの直接入力ファイルだったとは確認していません。** 参照Notebookのローダーを実行したり、外部CSVミラーへフォールバックしたりせず、別途Kaggleの公開CSVを取得して4群の構造を確認しています。認証時の標準出力・標準エラーは捕捉し、指定されたNotebook・ログにAPIトークンそのものの表示は見られません。

**データ定義・前提・意味的検査**: 欠損除去の確認は44行から44行、削除0行でした。x・yの有限値、各群11点、カテゴリ、行番号1〜11、群と行番号から作るキーの一意性を確認し、宣言したスキーマについて異常は0件でした。これは群IIIの影響点が誤記でないことや、測定過程の妥当性まで保証する結果ではありません。

データ定義manifestでは母集団、測定機構、x・yの物理単位を`unknown`、教材としての目的と説明側／応答側という役割を`inferred`と記録しています。初回の前提検査は、全群共通の線形性がまだ`assumed`であることを警告しました。最終段階では群別のモデル比較と識別可能性検査を`tested`として記録し、共通線形性を前提から外したことで、最終前提検査の指摘はありませんでした。

**初回結果**: 各群のx平均は9、標本分散は11で一致し、y平均、y標本分散、Pearson相関、OLS係数、R²もほぼ同じでした。分散は`ddof=1`です。保存された出力を丸めて示します。

| 群 | n | y平均 | y標本分散 | Pearson r | OLS傾き | OLS切片 | R² |
|---|---:|---:|---:|---:|---:|---:|---:|
| I | 11 | 7.500909 | 4.127269 | 0.816421 | 0.500091 | 3.000091 | 0.666542 |
| II | 11 | 7.500909 | 4.127629 | 0.816237 | 0.500000 | 3.000909 | 0.666242 |
| III | 11 | 7.500000 | 4.122620 | 0.816287 | 0.499727 | 3.002455 | 0.666324 |
| IV | 11 | 7.500909 | 4.123249 | 0.816521 | 0.499909 | 3.001727 | 0.666707 |

しかし、同じ`y≈3+0.5x`という直線から、同じ関係構造や予測の安定性を結論することはできませんでした。群Iには散らばりを伴う線形傾向、群IIには曲線性、群IIIには縦方向の影響点、群IVには1点に依存した傾きの識別という違いがあります。相関関数の「強い正の相関」という説明は係数の記述であり、線形性や頑健性の保証としては扱っていません。

![4群の散布図とOLS直線、群IIの二次曲線](figures/exp-12-anscombe-scatter-regression.png)

*同じ軸範囲で比較した4群の散布構造。赤いOLS直線はほぼ一致する一方、群IIの曲線、群IIIの第3点、群IVの第8点とxの集中は異なる。NotebookのPNG出力をそのまま抽出。*

![4群に線形モデルを当てたときの残差対x](figures/exp-12-anscombe-ols-residuals.png)

*群IIでは残差に曲率が残り、群IIIでは1点が大きく外れる。群IVのx=19の点は残差がほぼゼロでも、傾きの安定性を保証しない。*

初回から線形・二次モデルのLOOCV（一点ずつ除いた交差検証）も比較しています。群IIのRMSEは線形1.484648から二次0.001764へ低下しました。一方、群Iは1.367787から1.398117、群IIIは1.465390から1.762707となり、単に次数を増やせばよいわけではありません。群IVは二次モデルの設計行列がランク不足で、線形モデルでもx=19の1点を除いた1foldが識別不能になるため、全foldに基づくLOOCV RMSEを未定義としています。

群IIIの第3点（x=13、y=12.74）のCook距離は1.392849で、閾値`4/11`と1の両方を超えました。この点を診断目的で除くと、OLS傾きは0.499727から0.345390へ変わり、相関は約0.999997になります。群IVの第8点（x=19、y=12.50）はレバレッジが数値誤差の範囲で1であり、Cook距離の分母が退化するため未定義です。除去後は全点x=8となり、傾き・相関は「ゼロ」ではなく識別不能です。

![レバレッジとOLS残差による影響点診断](figures/exp-12-anscombe-influence-diagnostics.png)

*点の大きさは定義可能なCook距離を表す。群IVのレバレッジ1の点は赤い×で未定義を明示し、残差の小ささだけでは影響点を見抜けないことを示す。*

**初回の感度分析**: 全点の結果を基準に各1点を除いた場合、傾きの最大相対変化は群Iが18.29%、IIが25.35%、IIIが30.88%でした。許容幅20%でIは`stable=True`、II・IIIは`False`です。ただし20%は便宜的な判定幅であり、統計的な同等性検定ではありません。群IVは識別可能な11仕様に限れば最大変化3.72%で`stable=True`ですが、第8点除去の無効仕様1件を別記しています。**無効仕様を除いた安定判定を、全仕様に対する頑健性とは解釈していません。** 点の除去は影響診断であり、元データの削除や誤記認定ではありません。

**AIが生成した追加依頼1 — 丸め幅と頑健推定への依存**

> 丸め誤差や推定法の選択によって、群IIの曲線性と群IIIの単一点への依存という解釈が変わるか確認してください。yを記録精度に相当する±0.005の範囲で変動させ、OLSとTheil–Senを比較し、群IVで頑健推定を使っても識別問題が解決しない理由を説明してください。

**選定理由**: 初回の曲線性と影響点依存が、yの小数2桁の記録精度やOLSの選択だけで生じたものかが未確認だったためです。

**結果**: 丸め幅0／0.005とseed12〜61の組合せ100仕様で検査しました。群IIの二次モデルによるLOOCV RMSE改善率は最低99.6369%、群IIIの第3点除去による傾きの相対変化は最低30.7908%で、主要な違いは消えませんでした。改善率の感度判定は許容1%に対して`stable=True`、最大相対変化0.002446でした。これは改善率という指標の安定性であり、群IIIのOLS傾きまで安定という意味ではありません。

Theil–Sen傾きは、Iが0.501667、IIが0.500000、IIIが0.345556、IVが0.503182でした。群IIIでは第3点除去後のOLS傾き0.345390と整合し、全点OLSの0.499727とは異なります。群IVでは頑健推定でもx=19の同じ1点との組合せに依存するため、推定法を変えても観測支持範囲の不足は解消しません。

**証拠・限界**: Notebookの実行カウント10の`iteration1_evidence`と対応するInsightに数値が保存されています。±0.005は記録桁から設定したシナリオで、真の測定誤差分布を推定したものではありません。100仕様はすべての摂動を網羅する保証ではなく、Theil–Senの区間を母集団推論には使っていません。

**AIが生成した追加依頼2 — 正相関と局所方向、予測を支える観測範囲**

> 群IIの正の相関を「xが増えるほど常にyが増える」と誤読できないよう、観測範囲内の二次曲線の頂点と局所傾き、隣接点の変化を比較してください。群IVについてはxの支持範囲と未観測区間を明示し、同じ回帰直線を同じ予測根拠として使えるか検証してください。

**選定理由**: 正の相関を全域の単調増加と取り違えたり、共通の直線式を同じ予測根拠と扱ったりする余地が残ったためです。

**結果**: 群IIの二次曲線の頂点はx=10.972958、x=14の局所傾きは−0.767133でした。実際の観測値もx=11のy=9.26からx=14の8.10へ低下しており、正のPearson相関は全域の単調増加を意味しません。

I〜IIIのxは4〜14の11水準、隣接する観測xの最大間隔は1です。一方、群IVはx=8に10点、x=19に1点の2水準しかなく、その間の幅11の区間に観測がありません。したがって、同じ回帰式でも補間や新規xでの予測を支える点の配置は異なります。

![群IIの局所傾き、群IIIの1点除去、群IVの観測支持範囲](figures/exp-12-anscombe-local-slope-and-support.png)

*左は群IIの局所傾きが正から負へ変わる位置、中央は群IIIの全点OLSと第3点除去後の直線、右は群IVのx別観測数と未観測区間。正相関・共通直線式だけでは説明できない違いをまとめている。*

**証拠・限界**: Notebookの実行カウント11の`iteration2_evidence`、隣接点変化・支持範囲の表、上のPNG、対応するInsightに記録があります。群IIIの影響点の真偽や群IVの未観測区間の関係は、追加データなしには確定できません。

**反復の停止と追加確認**: Notebookは、2回で主要な未解決点を確認し、残る問題は追加観測・外部妥当性の問題なので、同じ教材内で第3回を行っても価値がないと判断しています。なお、保存されたコードでは追加依頼2件の文面は初回レビューセルでまとめて定義・記録されています。「各回の結果を読んで次の文面を新たに作成した」という逐次的な生成過程までは、この成果物から確認できません。

`followup.log`も既存の初回分析と反復2回で元の問いに答えているとして、追加分析は不要と述べています。同ログの「証拠の対応付けと再評価記録を補強する」は方針の表明です。`status.json`では初回・最終のNotebookサイズがともに778005 bytes、mtimeも同じであり、この追加確認によってNotebookが更新・再実行されたとは断定しません。

**最終結論**: **要約統計が似ていても、4群を同じ結論として扱うことはできません。** 共通なのは、平均・標本分散・Pearson相関・OLS係数など指定した要約値の近似的一致です。群Iは観測範囲の線形近似が比較的妥当、IIは曲線性、IIIは縦方向の影響点への依存、IVは高レバレッジ点とx支持範囲の欠如が本質的に異なります。共通軸の散布図、残差対x、レバレッジ・Cook距離と1点除去、線形／二次モデルのLOOCV、xの頻度と空白区間を合わせて比較する必要があります。数値要約だけから線形性・単調性・予測頑健性・因果を結論することはできません。

**監査・再現性**: 分析完了の判断は`status.json`の`analysis_complete=true`、`final_completion.ready=true`とNotebookの内容に基づきます。生成前の文書化状態を分析の成否には用いていません。

| 確認項目 | 保存された証拠 |
|---|---|
| Notebook | `benchmark/projects/kaggle-v020-kaggle-exp-12-anscombe/notebooks/kaggle-v020-kaggle-exp-12-anscombe.ipynb` |
| 初回実行 | `initial_exit_code=0`、825.6秒、終了理由`exited` |
| 再実行 | 初回ログはカーネル再起動後の全セル再実行を報告。Notebookの実行カウントは1〜13、最終出力とmetadataは`replay_status=matched-baseline` |
| 比較内容 | 保存セルのコードは取得ファイルSHA-256、要約統計、モデル、診断、除去結果、丸め結果、反復結果とコードソースSHA-256の基準照合を実装 |
| 最終Notebook監査 | `nbformat_valid=true`、13コードセル／13実行済み、未実行・エラー・findings・visual_findingsなし、`ok=true` |
| 図表・Insight | PNGを含むセルは0始まりインデックス7・12、PNG出力は計4枚、Evidence manifest付きInsightは6件 |
| lifecycle | `v020-exp-12`は`completed`。最終出力で実行中セル0、保留書込み0、保持ロック0 |
| 追加確認の終了 | 92.9秒、`followup_exit_code=0`、終了理由`artifact_complete_cutoff`。ログはNotebookの安定・監査通過を理由とするランナーによる停止を記録 |

Notebookの最終保存セルは、`audit_notebook(..., visual_audit=True)`で監査し、監査合格後に`mark_completed`と`wait_for_quiescence`を実行しています。タイトル・軸・凡例・グリフ・可読性を確認した旨も最終出力にあります。PNGはセル出力から抽出したもので、分析や描画の再実行による作り直しではありません。

再現性について確認できるのは、保存コードの比較処理と`matched-baseline`という実行結果、および初回ログの再起動・再実行報告です。この節の作成時にはKaggle API取得やNotebook全セルの再実行を新たには行っていません。また、ログは要約された実行記録であり、Jupyter MCPの全呼出履歴や独立した第三者環境での再現を示すものではありません。Notebookが保存したmanifest等の別ファイルは、本節の独立した証拠には使用していません。

**失敗内容・Jupytermind改善候補**: 最終Notebookに分析セルのエラーや未実行セルはなく、分析の停止・取得失敗としては記録されていません。ただし、分析本体と分離した直接関数呼出で、次の2件の候補を記録しています。

| 分類 | 再現・実際の挙動 | 期待する挙動・影響・回避策 |
|---|---|---|
| `sensitivity`：非有限値入力の不具合候補 | 2仕様の返り値を1.0とNaNにすると、`stable=True`、`max_relative_deviation=0.0` | 非有限値を拒否するか、未評価・不安定を明示すべき。未定義仕様を含む結果を頑健と誤読し得る。本分析はランク・有限値を別検査し、群IVの無効仕様を別記してNaNを安定判定に渡していない |
| `data_definition`：確実性集約の機能不足候補 | `inferred`だけのmanifestで`unresolved_fields()`を呼ぶと0件 | 任意の機能として`unknown`と`inferred`を区別して注意点に集約できるとよい。推定を確認済みと誤読するリスクがあるため、本分析はstatusを別走査して両者を保存。Notebook自身が仕様どおりの挙動としており、不具合とは断定しない |

証拠はNotebookの0始まりセル13、実行カウント12の最小再現出力です。`nan_input_values=[1.0, NaN]`、`nan_input_report_stable=true`、`nan_input_max_relative_deviation=0.0`、`inferred_only_unresolved_fields_count=0`が残っています。この再現処理はKaggle APIやCLI・外部ランナーを呼ばず、Jupytermind関数を直接呼んでいます。分類、再現手順、期待・実際の挙動、影響、証拠、受け入れ条件を`benchmark/runs/12-kaggle-exp-12-anscombe/issue-candidate.json`に保存しました。ソース修正やGitHub Issue登録は行っていません。

**外部ツール・統合上の事象との切り分け**: Notebookの改善候補節には、実行中のNotebookを自身のセルから`enqueue_write`で変更した際、MCPは`COMPLETED`でも出力やexecution_countが保持されず、初回報告セルが`Count=N/A`になったという観測が記録されています。ファイル書込みとJupyter MCP側の結果保存の競合とされ、Jupytermind単体の不具合とは断定していません。回避コードは実際のIPython入力履歴番号と生成出力を明示保存し、最終監査では全セルの実行情報が残っています。指定ログに元のMCP応答の詳細はないため、原因の独立確認はできず、上の2件とは別扱いです。Kaggle認証・検索・取得はNotebook出力で成功を確認でき、追加確認の打切りは外部ランナーの動作であって、Jupytermindの分析失敗としては扱いません。

**残る限界**: 各群11点の固定教材であり、実母集団の独立同分布標本・因果効果としての解釈や、実世界への一般化は行っていません。母集団・測定機構・単位は不明で、公開CSVと参照Notebook入力のバイト単位同一性も未確認です。小標本のLOOCVと便宜的な感度許容幅だけでモデルの正しさを保証できず、群IVではそもそも定義できない比較があります。群IIIの点の真偽、群IVの未観測区間、外部妥当性は追加観測を要します。監査の指摘なしは保存状態と実装された検査条件についての結果であり、科学的妥当性やすべての主張を独立に保証するものではありません。
