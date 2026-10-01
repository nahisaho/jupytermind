## 実験11: Anagrams（分析完了）

**課題**: 「Kaggleで見つかるAnagrams課題データを使い、課題条件や参加者によって回答の正確さがどう異なるか調べてください。」

**初回プロンプト（全文・原文）**:

> Kaggleで見つかるAnagrams課題データを使い、課題条件や参加者によって回答の正確さがどう異なるか調べてください。データの形を確認してから自分で計画・統計的比較・図表を選び、少数標本の限界も述べてください。AI Data Scientist SkillとJupyter MCPで実行し、計画、コード、出力、根拠付きInsightをノートブックに記録して再実行を確認してください。 Kaggle参照先: https://www.kaggle.com/datasets?search=anagrams。インストール済みkaggle Python SDKを使い、NotebookのJupyter MCP実行セル内で`KaggleApi().authenticate()`、`dataset_list(search=...)`、`dataset_list_files(...)`、必要に応じて`dataset_download_file(...)`を呼び出し、Kaggle上の対応する公開データを検索・取得してください。外部CSVミラーは使用しないでください。owner/dataset slug、取得ファイル名、取得日、ファイルSHA-256をNotebookに記録してください。APIトークンをセル出力・Notebook・ログへ表示しないでください。分析・API取得コードの実行はJupyter MCPだけを使い、端末コマンド、subprocess、外部スクリプト起動、作業エージェントへの委譲は行わないでください。APIで対応するデータが見つからない場合は外部ソースにフォールバックせず、その実験を停止して理由を報告してください。保存先は benchmark/projects/kaggle-v020-kaggle-exp-11-anagrams/notebooks/kaggle-v020-kaggle-exp-11-anagrams.ipynb としてください。run_idは `v020-exp-11` です。長時間処理の開始前にlifecycle.register_runを呼び、実行・書込みフェーズを記録し、終了時にcompletedまたはfailedを記録してください。データ定義manifest、分析前提manifest、意味的な異常検査、妥当な範囲の感度分析を使い、適用できない機能は理由を記録してください。図表はvisual_audit=Trueで監査してください。Notebookには「使用したJupytermindモジュール」節を設け、直接import・呼び出したモジュール名、関数名、使用目的を記録してください。間接利用は使用済みに含めないでください。Jupytermindの不具合または機能不足が疑われた場合は「Jupytermind改善候補」節を設け、分類、再現条件、期待する挙動、実際の挙動、影響、回避策、関係するセルとログを記録してください。Copilot CLI、Kaggle API、ベンチマークランナーに固有の問題とは切り分け、候補がなければ「なし」と記録してください。初回分析後、自分で結果を読み直し、結論に実質的な影響を与える未解決点があれば自然言語の追加依頼文を作成し、Notebookの「反復依頼履歴」に原文のまま記録して実行してください。価値ある追加分析がなくなるまで最大3回繰り返し、各反復の選定理由・結果・証拠・残る限界を報告してください。最後に全コードセルを上から再実行し、notebook_auditとライフサイクル状態を記録してください。

**使用したJupytermindモジュール**: 対象Notebookのコードセルで直接import・呼出しを確認したモジュールを示します。型・メソッドも、直接使用したものを併記しています。セル参照のindexは0始まりです。

| モジュール | 関数・型・メソッド | 使用目的 |
|---|---|---|
| `ai_data_scientist.project_manager` | `resolve_project`, `ensure_notebook`, `ensure_data_dir`, `ProjectHandle`, `enqueue_write` | プロジェクトと保存先・データ置場の解決、根拠照合用一時Notebookの作成と直列化書込み |
| `ai_data_scientist.language_router` | `detect_language` | 日本語での記録言語の判定 |
| `ai_data_scientist.lifecycle` | `register_run`, `is_cancel_requested`, `mark_execution_start`, `mark_execution_end`, `mark_write_start`, `mark_write_end`, `mark_completed`, `get_run_status`, `wait_for_quiescence` | run登録、実行・書込みフェーズ、完了・静止状態の確認 |
| `ai_data_scientist.ingestion` | `SourceSpec`, `ingest` | Kaggle SDKで取得したCSVの行数上限付き読込み |
| `ai_data_scientist.cleaning` | `clean_dataset` | 完全重複の検査。除去0行、欠損補完なし |
| `ai_data_scientist.eda` | `explore` | 型、欠損、要約統計、条件カテゴリの確認 |
| `ai_data_scientist.data_definition` | `FieldValue`, `build_manifest`, `DataDefinitionManifest.unresolved_fields` | 確認済みの出典と、未確認の測定定義・単位・分母の分離 |
| `ai_data_scientist.analysis_assumptions` | `Assumption`, `AnalysisAssumptionManifest`, `check_manifest` | 推論単位と分析前提、未検証の独立性・交換可能性などの明示 |
| `ai_data_scientist.data_quality` | `detect_anomalies` | 欠損、ID一意性、非負性、許容カテゴリの意味的制約検査 |
| `ai_data_scientist.sensitivity` | `SensitivityPlan`, `run_sensitivity` | 参加者除外・推定法変更による各66仕様の感度分析 |
| `ai_data_scientist.dataset_validation` | `compare_datasets` | 別Kaggle公開ファイルとのID・値の照合。独立標本検証には用いない |
| `ai_data_scientist.visualization` | `render_chart`, `build_image_output` | 条件別平均バー図、PNG出力の組立て、再描画診断 |
| `ai_data_scientist.insight_engine` | `record_insight` | 実際のprint出力を用いた根拠照合プローブ。拒否された結果を改善候補として記録 |
| `ai_data_scientist.notebook_audit` | `audit_notebook`, `audit_visual_outputs` | 実行・根拠・可視化の監査、metadata欠落時の診断 |

対象Notebookの失敗時分岐には `lifecycle.mark_failed` もありますが、最終再実行でその分岐が動いたとは扱いません。Notebookには別のJupyter MCP作業Notebookでの根拠抽出・Insight保存の記録もありますが、上表は対象Notebookの実行コードで確認できる呼出しに限定しました。`mcp_gateway.run_and_record` と `stats_analysis.correlation` は使用済みに数えません。推測統計はNumPy/SciPy、詳細図はMatplotlibで実装されており、これらとKaggle SDK・Jupyter MCPはJupytermindモジュールではありません。

**初回指示**: 手法を指定せず、データの形を確認してから比較・図表を自律的に選び、小標本の限界を述べるよう依頼しました。取得はKaggle API、分析実行はJupyter MCPに限定し、出典・ハッシュ、データ定義・分析前提manifest、意味的異常検査、感度分析、最大3回のAI生成追加依頼、全コードセル再実行、可視化監査、ライフサイクル状態まで記録する条件を与えました。

**データ取得**: Notebookの `KaggleApi` 実行セルで認証し、`dataset_list(search='anagrams')`、`dataset_list_files`、`dataset_download_file`、`dataset_metadata` を呼び出しています。検索結果は `sakshisatre/anagrams-dataset` と `abdoomoh/all-seaborn-built-in-datasets` の2件で、主分析には前者の `anagrams.csv` を採用しました。外部CSVミラーへの取得処理はありません。主ファイルは399バイト、20行・5列（`subidr`, `attnr`, `num1`, `num2`, `num3`）で、各参加者に3測定、`divided`・`focused` 各10人です。欠損0、完全重複による除去0行、ID重複0でした。

取得日時は最終Notebookに保存された再取得出力のUTC時刻です。初回取得時刻を推測して補っていません。

| 用途 | Kaggle owner/dataset slug | 取得ファイル名 | 取得日時（UTC） | SHA-256 |
|---|---|---|---|---|
| 主分析 | `sakshisatre/anagrams-dataset` | `anagrams.csv` | `2026-10-01T17:18:35.031000+00:00` | `5eda074c9bc1d1ffb0a3988e36713fae520591d3e221e186efe9988baa054fc8` |
| 反復1の照合 | `abdoomoh/all-seaborn-built-in-datasets` | `Seaborn All Built-in Datasets/anagrams.csv` | `2026-10-01T17:19:02.774457+00:00` | `17af9bb054e0c371779ec5bd364baae916a923fe747049271dab1f3bd592003a` |

**測定定義と分析計画**: Kaggleの説明には `timings` とあり、数値列の説明は `likely`、注意条件の説明も `possibly` とされています。正誤・出題数・単位・値の良い方向・測定順・難度は確認できません。ID 7の `num2=4.5` は単純な整数正答数という解釈に整合しませんが、入力誤りとは断定せず保持しました。設定した欠損・一意性・非負性・カテゴリ制約では異常所見0件です。ただし、上限不明の値を正常と保証した結果ではありません。

AIは20人を推論単位とし、60個の独立観測として扱わない計画を立てました。各測定列と参加者の3列平均についてfocused−divided差、Hedges g、参加者単位の20,000回bootstrapによる点別95%区間、全184,756通りの群ラベル置換による両側p値を計算し、4比較にHolm補正しています。乱数seedは `20261002` です。さらに、参加者内の列間差の2次元プロフィール、対応t比較、補助的Friedman検定、個人線・群差区間・ID別平均を選びました。データ確認後の探索的計画であり、事前登録ではありません。

**初回結果**: 初回ログはnum1・num2の条件差とnum3の不確実性を報告しています。以下はその報告を最終Notebookの再実行出力 `GROUP_RESULTS` で照合した値です。

| 測定 | divided平均 | focused平均 | 差（focused−divided） | 点別bootstrap 95%区間 | Hedges g | 正確置換p値 | Holm補正p値（4比較） |
|---|---:|---:|---:|---|---:|---:|---:|
| num1 | 4.00 | 6.70 | 2.70 | 1.70〜3.70 | 2.070 | 0.000281 | 0.001126 |
| num2 | 4.95 | 7.00 | 2.05 | 0.90〜3.15 | 1.467 | 0.006040 | 0.012081 |
| num3 | 6.40 | 6.70 | 0.30 | −0.60〜1.20 | 0.257 | 0.692708 | 0.692708 |
| 参加者の3列平均 | 5.1167 | 6.8000 | 1.6833 | 0.9500〜2.4333 | 1.797 | 0.001018 | 0.003053 |

num1・num2ではfocused条件の記録値が高く、num3では区間が0を含みます。参加者平均の群差もありますが、**「高い記録値」を「正確な回答」と読み替えることはできません**。得点なら高い値が有利となる可能性がある一方、所要時間なら解釈の方向は逆になります。

![Anagramsの注意条件別に比較した参加者の3測定平均](figures/exp-11-anagrams-condition-means.png)

*注意条件別の参加者平均。dividedは5.1167、focusedは6.8000ですが、測定尺度の意味は未検証です。バー図だけでは不確実性や測定列ごとの差は分からないため、次の図と統計表を併せて読みます。Notebookの保存済みPNG出力をそのまま抽出しました。*

プロフィール比較では、`num3−num1` の平均はdividedで2.40、focusedで0.00、その群差は−2.40（参加者bootstrap 95%区間 −3.70〜−1.00）でした。`num2−num1` と `num3−num1` をまとめた2次元プロフィールの全ラベル置換p値は0.000103です。このp値を `num3−num1` 単独の検定値と同一視しません。群によって列間のパターンは異なりますが、時間順・難度が不明なので学習効果や注意の因果効果とは呼びません。

参加者の3列平均は4.00〜8.33、各参加者の3列の最大値−最小値は1.00〜5.00でした。IDは識別子であり能力順位ではありません。個人ごとの3値から能力・課題特異性・測定誤差を十分に分離することはできません。

![Anagramsの参加者別プロフィール、測定列ごとの条件差と区間、参加者平均](figures/exp-11-anagrams-participant-profiles.png)

*左は同一参加者を結ぶ細線と条件別平均の太線、中央はfocused−divided差と点別95%bootstrap区間、右は参加者ID別の3測定平均です。num3の区間は0をまたぎます。測定列の順序は時間順とは確認されておらず、右のID順も能力順位ではありません。Notebookの保存済みPNG出力をそのまま抽出しました。*

**AIが生成した追加依頼1 — 測定定義と同源コピーの照合**

> Kaggle説明の「所要時間」と正確さという目的の不整合を再検討してください。同じ検索で見つかった別のKaggle公開データのanagramsファイルと説明をAPIから取得し、値と参加者IDを照合してください。コピーの一致を独立標本による再現と扱わず、正答率の結論が可能か判断してください。

**選定理由**: `SOURCE_DEFINITION` と `NONINTEGER_VALUES` を受け、測定の意味を取り違えると群差の良し悪しまで逆になることをAIが重視しました。

**結果・証拠・限界**: 別Kaggle公開データの420バイトのCSVをAPIで取得し、`compare_datasets` で照合しました。20 IDすべてが対応し、`attnr` と数値3列の値は各列100%一致、片側だけのID・値不一致は0でした。一方、SHA-256は異なりバイト同一ではありません。両公開データはSeaborn由来を示す同源コピーで、標本数は増えず独立再現でもありません。別公開説明にも正答率定義はなく、正確さの結論は依然出せません。採用判断は「正答率は算出せず、記録値の条件差に限定」です。証拠はセルindex=14の `CANDIDATE_PROVENANCE`, `DATASET_COMPARISON`, `ITERATION1_RESULT` と、反復1の根拠manifestです。

**AIが生成した追加依頼2 — 参加者・推定法への依存**

> 各群10人という少数標本で見えた群差とプロフィール差が、1人の参加者や非整数値、平均という推定法だけに依存していないか調べてください。1人ずつの除外、ID 7の除外、中央値と10%トリム平均を感度分析し、順位ベースの群間比較と参加者内の符号検定も補助的に実行してください。方向の安定性と効果量の安定性を分けて報告してください。

**選定理由**: 初回の `GROUP_RESULTS`, `PROFILE_INTERACTION` は差を示しましたが、各群10人しかなく、非整数値の意味も未解決でした。定義照合で解決できない点とは分けて、特定参加者や平均という推定法への依存を調べました。

**結果・証拠・限界**: 全標本、ID 7除外、20人それぞれの1人除外という22指定と、平均・中央値・10%トリム平均の3推定法を組み合わせ、参加者平均差と `num3−num1` の群差に各66回適用しました。

| 対象 | 基準値 | 感度分析の最小〜最大 | 最大相対偏差 | 方向 | 25%診断基準による判定 |
|---|---:|---|---:|---|---|
| 参加者平均の群差 | 1.6833 | 1.4167〜1.8634 | 15.84% | 全仕様で正 | `stable=True` |
| num3−num1の群差 | −2.4000 | −3.5000〜−2.1111 | 45.83% | 全仕様で負 | `stable=False` |

参加者平均差は設定した基準内で安定しましたが、プロフィール差は方向のみ安定し、大きさは不安定でした。25%は分析上の診断基準で、科学的な同等性閾値ではありません。また、`exclude_7` と `leave_7` は同じ標本なので、66実行は重複を除くと63種類の標本・推定法の組合せです。1人除外後のn=9の群では10%トリムは0人除去になります。各num1・num2列について66仕様を実行した結果ではありません。

順位ベースの群間比較でも、Holm補正p値はnum1で0.001126、num2で0.005391、num3で0.600619、参加者平均で0.002825でした。ただし順位分布差と平均差は異なる推定対象です。全20人のnum2−num1・num3−num1は対応t比較のHolm補正p値がともに約0.046でしたが、符号検定ではそれぞれ0.355・0.420でした。平均差と差の正負比は帰無仮説が異なるため単純な矛盾ではありませんが、全員が一様に増加するとは主張しません。dividedのnum3−num1は正8人・負0人・差0が2人で、符号検定の補正p値は0.0234でした。focusedには一貫した方向の証拠がありません。証拠はセルindex=16の `SENSITIVITY_SUMMARY`, `RANK_COMPARISON`, `SIGN_COMPARISON`, `ITERATION2_LIMITS` です。これらの感度分析も測定定義・独立性を検証するものではありません。

**AIが生成した追加依頼3 — 非有意と同等性、推定精度**

> num3で有意な群差がなかったことを「同じ正確さ」と誤読しないように、Welchの信頼区間と仮の同等性マージン0.5・1・2記録値単位によるTOSTを示してください。閾値の科学的根拠がないこと、少数標本でどの程度の差が見逃されうるか、符号検定と対応t検定が一致しなかった参加者内の結果も踏まえて、結論の強さを調整してください。

**選定理由**: 初回のnum3の区間が0を含み、順位比較も非有意でした。「差を検出できない」と「同等である」を区別し、方法依存の参加者内結果についても解釈を弱める必要がありました。

**結果・証拠・限界**: num3の平均差0.30に対するWelch 95%区間は−0.751〜1.351、90%区間は−0.567〜1.167でした。仮のマージンを使ったTOSTは次の結果です。

| 仮の同等性幅（記録値単位） | TOST p値 | 5%水準での条件付き判定 |
|---|---:|---|
| ±0.5 | 0.346945 | 同等性を示せない |
| ±1 | 0.089305 | 同等性を示せない |
| ±2 | 0.001606 | この仮定幅では同等性を示す |

±2で通ることは、科学的な実用同等性や「同じ正確さ」の証明ではありません。測定単位・意味・実用閾値が未確認で、TOSTは多重性未補正の探索的感度確認です。観測SDを固定した80%検出差の近似目安は約1.47記録値単位であり、小〜中程度の差を見逃す可能性があります。これは精度の目安で、事後検出力ではありません。証拠はセルindex=18の `PRECISION_RESULT`, `ITERATION3_RESULT` です。測定定義・募集・割付情報は追加計算では復元できないため、3回で停止しました。

**追加確認ログでの再評価**: `followup.log` とNotebookのフォローアップ節は、データ定義、分析前提、異常値、感度、可視化、根拠manifestの6観点を再評価したと記録しています。既存の3件の依頼に回答できた範囲と情報不足を確認し、追加の自然言語分析依頼は0件、合計3件のままです。第4回の分析を生成したとは扱いません。対象Notebookの既存セルIDを保持し、新カーネルで再実行・根拠再結合・保存後監査を行った検証は、追加分析の反復とは区別します。

**最終結論**: **focused条件ではnum1・num2と参加者平均の記録値が高い一方、「回答がより正確」とは結論できません。** num3の非有意結果から同じ正確さとも判断できません。条件別プロフィールの差は方向を保ちましたが、その大きさは感度分析で不安定でした。参加者の記録値にも幅がありますが、個人の能力順位・有意な能力差は推定していません。数値差の探索的分析と再実行は完了しており、正確さ・学習・課題難度・注意の因果効果への回答は、必要な定義・設計情報がないため保留です。

**監査・再現性**: `status.json` の `analysis_complete=true`、`final_completion.ready=true` と、その8項目の要件充足を、実行済みNotebook内容と併せて分析完了の根拠にしました。初回・追加確認のプロセスはともにexit code 0で通常終了、所要時間はそれぞれ1,494.0秒・389.4秒です。これらはランナーの実行時間であり、統計計算だけの所要時間ではありません。

Notebookには12コードセルがあり、最終保存状態の実行番号は上から1〜12、エラー出力はありません。metadataの `verified_reexecution` は新カーネルでの順次再実行、報告された全数値の初回一致、8件の根拠付きInsight、採用PNG 2枚の目視確認を記録しています。これは保存された検証記録の報告であり、本節作成時にKaggle再取得や分析を再実行したものではありません。

最終コードセルの `audit_notebook(..., visual_audit=True)` 出力、metadataの `post_save_audit`、statusの `final_audit` は、nbformat妥当、全12コードセル実行済み、未実行・エラー・監査所見・visual所見0件を記録しています。フォローアップrun `v020-exp-11-followup` は `completed`、実行中セル・未処理書込み・保持ロックはいずれも0です。初回run `v020-exp-11` の完了は初回ログにも記録されています。監査合格は測定定義・統計仮定・科学的妥当性や、以下の製品側改善候補の解消を保証しません。

再現にはKaggle認証、対応公開ファイル、Jupyter MCPとNotebookが直接使用するライブラリが必要です。保存済み出力のNumPyは2.5.3、pandasは3.0.6、SciPyは1.18.1です。主CSVには固定SHA-256のassertがあり、公開ファイルが更新されれば停止する設計です。認証時の標準出力・標準エラーは抑制し、出力された来歴に認証情報は含まれていません。証拠manifestはセルIDから最新実行番号へ再結合され、引用値の存在を追跡しますが、それだけで主張の妥当性を証明するものではありません。

**失敗内容とJupytermind改善候補**: 最終分析の未完了・未実行セル・未解決エラーは記録されていません。ただし、途中で回避した問題と、診断で再現した機能不足があります。Jupytermind側の候補は次の4件です。受け入れ条件は提案であり、修正実装・達成検証・GitHub Issue登録は行っていません。

| 候補・分類 | 再現条件と期待する挙動 | 実際の挙動・影響・回避策 | 証拠と受け入れ条件 |
|---|---|---|---|
| C1 可視化レイアウト不具合候補 | `render_chart(kind='bar', x='attnr', y='participant_mean')` を日本語ラベル・既定保存条件で描画。目盛・軸ラベルが枠内に収まることを期待 | 初回画像で下端のラベルが欠け、Notebookのフォローアップ記録では日本語フォントを明示しても再現。条件を誤読しうるが数値計算は不変。採用図は `savefig.bbox='tight'`、詳細図は `constrained_layout=True` で回避 | セルindex=20の `RENDERER_DIAGNOSTIC`、セルindex=24のC1と再現結果。英語・日本語の長いラベル・回転目盛・凡例を既定設定でも画像内に収める |
| C2 可視化監査の機能不足候補 | 実PNGセルのコピーでmetadataを空にし `audit_visual_outputs` を呼出し。未検査のタイトル・軸・glyph記録を警告することを期待 | PNG 2枚のmetadataを除去しても所見0件。未検査の図を監査済みと誤認する可能性。採用セルにmetadataを明示し、画像を目視確認して回避 | セルindex=20の `VISUAL_METADATA_PROBE`。PNGごとのmetadata・glyph検査記録の欠落を報告し、必要なラベル・凡例を検査。凡例不要の明示は許容する |
| C3 根拠追跡の出力形式対応不足 | 実行番号の一致するprintの `stream.text` にある `timings` を `record_insight` で引用。標準Jupyter出力として受理することを期待 | 値が存在しても `EvidenceMissingError`。有効な実行証拠を保存できない。実計算結果を `display_data` の `text/plain` に出す `emit` で回避 | セルindex=20の `STREAM_EVIDENCE_PROBE`、初回ログの拒否報告。Insight保存・監査がstreamも照合し、実行番号・値の不一致は従来どおり拒否する |
| C4 再描画時の日本語glyph不具合候補 | 新カーネルで `rc_context` 内の初回 `render_chart` 後、context外で再描画。毎回日本語が読めることを期待 | context復帰後の診断図でDejaVu Sansのglyph警告35件。繰返し描画で日本語が欠落する可能性。採用図は新カーネル初回描画とglyph警告検査で確認 | セルindex=12の `CHART_PROVENANCE`、セルindex=20の警告、セルindex=24のC4。context・style変更の内外で再描画してもglyph欠落せず、外側のrcParamsを不用意に変更しない |

C1の切れとC4の文字欠落は区別しています。採用PNG 2枚は日本語ラベルが読める状態で保存されており、不具合診断用画像はNotebookのPNG出力として表示されていません。診断画像や別JSONへのパスはNotebookに記録されていますが、今回それら別ファイルを追加の証拠として読み込んではいません。特にC1の再現結果はNotebook内の観察記録に基づく候補として扱います。

**外部ツール・呼出し側との切り分け**: Notebookは、保存先作成前のJupyter MCPによる作成拒否、Filesystem MCPの許可範囲、Kaggle SDKの `dataset_list(page_size=...)` 非対応、比較関数のrelationship指定・sampling項目不足などを記録しています。これらは環境・SDK差・呼出し側の誤りとして修正され、Jupytermind側の4候補に含めません。実行中の同一Notebookを `enqueue_write` で変更するとMCP返却出力が0件、末尾の実行番号が未保存となった件は、Jupyter MCPの結果保存と外部更新の統合競合として記録されています。自己書換えを除去し、別作業Notebookから更新、対象Notebookは読取り専用監査とした後に再実行しています。Jupytermindコアの確定不具合には数えません。Copilot CLI・外部ベンチマークランナー固有の不具合は、指定証拠では報告されていません。

**残る限界**: 各条件10人・1人3値という小標本で、募集・無作為割付・参加者間独立性・群ラベル交換可能性・列間の尺度比較可能性は未検証です。全置換を列挙しても交絡は消えず、母集団一般化や因果推論はできません。bootstrapは小標本percentile法の近似かつ点別区間で、同時区間ではありません。Friedmanは同順位を含む小標本での漸近検定として補助的に扱いました。Holm補正は明記した比較群内に限られ、全探索・全反復を横断する多重性は補正していません。追加分析もデータ閲覧後の探索です。

正答率・二項モデルは正誤と分母がなく、学習・難度の評価は列定義と実施順がなく、個人能力検定は観測不足で適用していません。IDとの相関も名義尺度のため非適用です。独立参照標本がないので同源コピー照合を独立検証とはせず、`validate_anomalies` による独立検証も行っていません。分布・単位の根拠が弱いため標準z-score異常検知は主分析で採用せず、確認できる意味的制約を検査しました。`mcp_gateway.run_and_record` は本接続で必要なPython MCPClient実装が渡されないため非適用とし、Jupyter MCPのセル実行と直列化書込みを直接利用しています。

**証拠範囲と保存物**: 分析上の証拠は、指定のNotebook、`initial-prompt.md`、`initial.log`、`followup.log`、`status.json` に限定しました。参考記事 `white-paper2.md` は書式・詳細度の参考にのみ使い、旧実験の数値・図・監査結果は転用していません。Notebookは `benchmark/projects/kaggle-v020-kaggle-exp-11-anagrams/notebooks/kaggle-v020-kaggle-exp-11-anagrams.ipynb`、抽出図は `benchmark/figures/exp-11-anagrams-condition-means.png` と `benchmark/figures/exp-11-anagrams-participant-profiles.png` です。改善候補の分類・再現手順・期待と実際・影響・証拠・受け入れ条件は、同実験runディレクトリの `issue-candidate.json` に保存しました。
