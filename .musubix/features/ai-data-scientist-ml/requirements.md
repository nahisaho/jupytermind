---
schemaVersion: 1
feature: ai-data-scientist-ml
---
# Requirements / 要求 (ML Extension)

Feature: Advanced modeling and analytics extension of the "AI Data Scientist"
skill, built on top of the `ai-data-scientist` MVP (project notebook
lifecycle, ingestion, cleaning, EDA, statistics, visualization, evidence-
backed insights). This extension adds supervised/unsupervised modeling, time
series, tuning/AutoML, explainability, experimentation, NLP, dashboards, and
report export as an independently versioned increment, per rubber-duck
review guidance to avoid a single monolithic skill boundary.

All requirements in this file inherit REQ-AIDS-003 (Jupyter MCP execution
backend) and REQ-AIDS-009/010 (insight evidence rules) from the
`ai-data-scientist` MVP feature; every markdown interpretation produced by a
requirement below is subject to those evidence rules.

## REQ-AIDS-008: ML modeling support / 機械学習モデリング支援
Priority: should
Type: functional
Pattern: event-driven
Statement: When a user requests a classification or regression model, the system shall execute notebook cells that split the data, train the requested model, and report evaluation metrics for that model type.
Acceptance: A classification request on a labeled sample dataset produces accuracy, precision and recall, or RMSE and R2 for regression, in cell output, using a held-out test split with non-overlapping train and test row indices.

## REQ-AIDS-015: Feature engineering / 特徴量エンジニアリング
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests feature engineering, the system shall execute a notebook code cell that applies the requested encoding, scaling, feature selection, row-wise aggregation, categorical interaction, missing-value flagging, or explicit-edge binning transformation and reports the resulting feature set as a structured mapping from each added column name to a non-empty definition string naming the operation and source column(s).
Acceptance: A one-hot encoding request on a categorical column produces new dummy columns matching the pandas get_dummies reference output, listed in the cell output. An aggregation request naming one aggregate function (`mean`, `sum`, or `count_eq` with an explicit comparison value), a group-by column, and one or more source columns produces exactly one new column per requested aggregate, equal to the matching `pandas.DataFrame.groupby(group_col)[source_col].transform(...)` reference computation (nulls excluded from `mean`/`sum`, counted as non-matching for `count_eq`). A categorical interaction request over two named columns produces a new column equal to `df[col_a].astype("string") + "__" + df[col_b].astype("string")`, with a null in either source column producing a null in the result. A missing-value-flag request on a column with injected nulls produces a boolean column equal to `df[col].isna()`. A binning request supplying explicit monotonically increasing bin edges produces a new column equal to the reference `pandas.cut(df[col], bins=edges, right=True, include_lowest=True)` output, including its handling of out-of-range values as null. Every added column's definition string is present and non-empty in the returned mapping. Existing calls to `engineer_features(df, operation="one_hot"|"scale", columns=...)` continue to return the same `FeatureResult` dataframe, `added_columns`, and `removed_columns` as before this change.

## REQ-AIDS-073: Leakage-safe fit/transform feature engineering API / リーク防止fit/transform API
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests a statistics-estimating feature engineering transformation, the system shall provide a `fit_features(df: pandas.DataFrame, operation: str, columns: list[str]) -> FittedFeatureState` call whose stored statistics were computed from only the supplied `df`, and a separate `transform_features(fitted_state: FittedFeatureState, df: pandas.DataFrame) -> FeatureResult` call that applies those already-stored statistics to any supplied `df` without recomputing them, returning a `FeatureResult` with the same index/row order as the input and the transformed columns replaced in place.
Acceptance: `fit_features(train_df, "scale", columns)` returns a fitted-state object whose stored mean/standard-deviation (or equivalent) for each column is bit-for-bit equal to `sklearn.preprocessing.StandardScaler().fit(train_df[columns]).mean_`/`.scale_`. Calling `transform_features(fitted_state, validation_df)` produces output equal to applying that same fitted `StandardScaler.transform` to `validation_df[columns]`, and is not equal to `StandardScaler().fit_transform(validation_df[columns])` on a fixture where the two frames' column means differ, proving validation-row statistics were never used to compute the fitted state. `transform_features(fitted_state, train_df)` (fit subset transformed by its own fitted state) reproduces the legacy single-call `engineer_features(train_df, "scale", columns)` dataframe output exactly.

## REQ-AIDS-079: Paired t-test experiment evaluation / 対応のあるt検定による実験評価
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests experiment evaluation with `test="paired_t"` on aligned control and treatment observations from the same rows or folds, the system shall require both paired series to have identical index order and only finite numeric values, then evaluate the treatment-minus-control difference with a paired t-test over those matched pairs and report the resulting statistic, p-value, and markdown interpretation.
Acceptance: On a fixed aligned numeric fixture, `evaluate_experiment(control, treatment, test="paired_t")` returns a statistic and p-value that each match `scipy.stats.ttest_rel(control, treatment)` within `1e-6`, and the returned p-value differs from `scipy.stats.ttest_ind(control, treatment)` on that same fixture, proving the paired test path was used instead of the legacy independent-samples path.

## REQ-AIDS-080: Wilcoxon signed-rank experiment evaluation / Wilcoxon符号付順位検定による実験評価
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests experiment evaluation with `test="wilcoxon"` on aligned control and treatment observations from the same rows or folds, the system shall require both paired series to have identical index order and only finite numeric values, then evaluate the matched-pair differences with a Wilcoxon signed-rank test and reject any call where the paired series lengths differ.
Acceptance: On a fixed aligned numeric fixture, `evaluate_experiment(control, treatment, test="wilcoxon")` returns a statistic and p-value that each match `scipy.stats.wilcoxon(control, treatment)` within `1e-6`. Calling the same API with unequal-length paired inputs raises `ValueError` mentioning that paired experiment tests require equal-length inputs.

## REQ-AIDS-081: Paired bootstrap experiment evaluation / 対応のあるブートストラップによる実験評価
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests experiment evaluation with `test="paired_bootstrap"` on aligned control and treatment predictions or aligned fold-level scores, the system shall require the paired inputs (and `y_true`, when provided) to have identical index order and only finite numeric values, then resample matched pairs with replacement, compute a treatment-minus-control difference using either a caller-supplied metric function over aligned `y_true` and predictions or the default mean difference over the paired numeric scores, and report the observed difference together with a confidence interval and markdown interpretation without claiming a bootstrap hypothesis-test p-value.
Acceptance: Given fixed `random_state`, `iterations`, and `confidence_level`, `evaluate_experiment(control_predictions, treatment_predictions, test="paired_bootstrap", y_true=labels, metric_fn=roc_auc_score, ...)` returns an observed difference and confidence interval matching a reference paired-bootstrap implementation on the same aligned rows within `1e-6`, returns `p_value=NaN`, and its interpretation states that the bootstrap path reports an interval estimate rather than a hypothesis-test p-value. Given aligned per-fold numeric scores and no `metric_fn`/`y_true`, the same API returns an observed difference equal to `mean(treatment - control)` and a confidence interval matching a reference paired resampling of those fold pairs within `1e-6`. Calling any paired path with a NaN or infinite value raises `ValueError` mentioning finite paired values.

## REQ-AIDS-090: Repeated multi-seed experiment comparison summary / 複数seed反復比較サマリ
Priority: must
Type: functional
Pattern: event-driven
Statement: When a caller requests a repeated experiment comparison across multiple split seeds (and optionally model seeds), the system shall rerun the same control-versus-treatment comparison once per requested seed, preserve the per-seed metric values and treatment-minus-control improvements, and report an aggregate summary containing the mean improvement, a seed-variability estimate, and fold-sign counts showing how many aligned comparisons were positive, zero, or negative.
Acceptance: Given three requested split seeds and a deterministic comparison callback that returns per-seed `(control_metric, treatment_metric)` pairs of `(0.812100, 0.812250)`, `(0.812040, 0.812126)`, and `(0.812080, 0.812166)`, the repeated-comparison API returns exactly those three per-seed results in seed order, per-seed improvements of `0.000150`, `0.000086`, and `0.000086` within `1e-9`, `mean_improvement == 0.00010733333333333333` within `1e-12`, `seed_variability == 0.000064` within `1e-12`, and sign counts indicating three positive paired comparisons and zero zero/negative paired comparisons.

## REQ-AIDS-091: Seed-variability-based adoption threshold classification / seed揺れベース採用閾値分類
Priority: must
Type: functional
Pattern: event-driven
Statement: When a caller requests an adoption judgment from a repeated-comparison summary, the system shall compute an adoption threshold from the observed seed variability, record that threshold alongside the summary, and classify a candidate improvement as `adopt`, `within_seed_variability`, or `regression` according to whether the improvement is greater than the threshold, between zero and the threshold inclusive, or below zero.
Acceptance: Given a repeated-comparison summary whose observed `seed_variability` is `0.000064`, the threshold API returns `threshold == 0.000064` within `1e-12`, classifies `0.000021` and `0.000063` as `within_seed_variability`, classifies `0.000080` as `adopt`, and classifies `-0.000005` as `regression`.

## REQ-AIDS-092: Selection-bias holdout evaluation / 選択バイアスのホールドアウト評価
Priority: must
Type: functional
Pattern: event-driven
Statement: When a caller requests a holdout evaluation for configuration selection bias on labeled rows, the system shall split the input rows into mutually disjoint training, selection, and final-evaluation partitions with proportions `0.6`, `0.2`, and `0.2`, choose the winning configuration using only the selection partition, and report both the selection-time improvement and the final-evaluation improvement together with their difference as an optimism/selection-bias measure.
Acceptance: Given 10 labeled rows, `train_fraction=0.6`, `selection_fraction=0.2`, `evaluation_fraction=0.2`, and `split_seed=42`, the holdout-bias API passes one deterministic callback exactly three mutually disjoint index partitions whose lengths are `6`, `2`, and `2` and whose union equals the original 10-row index exactly once. On a fixed callback fixture where configuration `candidate_a` scores `+0.000224` versus baseline on the selection partition and `+0.000135` on the final-evaluation partition while every other candidate scores worse on selection, the API selects `candidate_a`, reports `selection_improvement == 0.000224` within `1e-12`, `evaluation_improvement == 0.000135` within `1e-12`, and `optimism == 0.000089` within `1e-12`.

## REQ-AIDS-016: Clustering and dimensionality reduction / クラスタリング・次元削減
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests clustering or segmentation or dimensionality reduction, the system shall execute a notebook code cell that fits the requested unsupervised model and reports cluster assignments or reduced component values.
Acceptance: A k-means clustering request on a sample dataset produces a cluster label column whose value counts sum to the original row count, shown in cell output.

## REQ-AIDS-017: Anomaly detection / 異常検知
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests anomaly or outlier detection, the system shall execute a notebook code cell that flags anomalous records using the requested method and reports the count of flagged records.
Acceptance: An anomaly detection request on a dataset with injected outliers flags at least the injected outlier rows, verified against the known injected indices.

## REQ-AIDS-018: Time series analysis and forecasting / 時系列分析・予測
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests time series analysis or forecasting, the system shall execute a notebook code cell that decomposes or forecasts the requested series and reports the resulting trend, seasonality, or forecast values.
Acceptance: A forecasting request on a synthetic seasonal series produces forecast values within a documented error tolerance of a reference statsmodels or Prophet forecast computed on the same input.

## REQ-AIDS-019: Hyperparameter tuning and model comparison / ハイパーパラメータ調整・モデル比較
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests hyperparameter tuning or model comparison, the system shall execute notebook cells that evaluate multiple parameter sets or model candidates and report the best performing configuration with its metric.
Acceptance: A tuning request over a defined parameter grid reports the selected best parameters and confirms its metric is the maximum or minimum among all evaluated candidates shown in the cell output.

## REQ-AIDS-020: Automated model selection / AutoMLによる自動モデル選定
Priority: should
Type: functional
Pattern: event-driven
Statement: When a user requests automatic model selection, the system shall execute notebook cells that train multiple candidate model types and report a ranked comparison of their evaluation metrics.
Acceptance: An AutoML request on a sample dataset produces a ranked table of at least three candidate models with a consistent evaluation metric column, verified sorted in the correct order.

## REQ-AIDS-021: Model explainability / モデル説明性
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests the default global explanation of a trained model supported by the default explainability path, the system shall execute a notebook code cell that computes and reports a documented feature-importance artifact.
Acceptance: A default global explainability request on a trained supported model produces a feature-importance ranking whose top feature matches the reference scikit-learn `feature_importances_` ordering for tree-based models or the absolute-coefficient ordering defined by REQ-AIDS-082 for coefficient-based models.

## REQ-AIDS-082: Explainability method labeling and default compatibility / 説明手法ラベル付けと既定互換性
Priority: must
Type: functional
Pattern: event-driven
Statement: When a caller requests `explainability.explain_model` without opting into an alternate explainability method, the system shall stay on the legacy global feature-importance path for tree-based and single-output coefficient models, apply the documented multiclass coefficient aggregation rule for supported class-aligned multiclass coefficient models, and return that ranking together with a global-importance-kind label that distinguishes split-based importances from coefficient-magnitude importances.
Acceptance: Calling `explain_model(model, feature_names)` on a fitted random-forest classifier returns the same ranking and per-feature values as `model.feature_importances_`, plus `importance_kind == "split"`. Calling it on a fitted single-output linear or logistic-regression model returns per-feature absolute-coefficient values computed from `np.abs(model.coef_).reshape(-1)`, a ranking sorted from those values, and `importance_kind == "coefficient_magnitude"`. Calling it on a fitted multiclass class-aligned coefficient classifier such as `LogisticRegression`, whose `coef_` has one row per class, returns per-feature coefficient-magnitude values computed from `np.abs(model.coef_).mean(axis=0)` and a ranking sorted from those aggregated values, plus `importance_kind == "coefficient_magnitude"`.

## REQ-AIDS-083: Signed local contributions with additive consistency / 符号付き局所寄与と加法整合性
Priority: should
Type: functional
Pattern: event-driven
Statement: When a caller requests signed local contributions for a supported single-output regression or binary-classification model and supplies feature rows, the system shall return row-aligned signed per-feature contribution maps together with provider metadata and an additive-consistency report against the model's raw per-row output when such output is available.
Acceptance: Calling `explain_model(..., method="signed_contributions", x=rows)` on a fitted single-output logistic-regression model returns one signed contribution map per input row, `contribution_kind` equal to either `"shap"` or `"linear"` depending on the selected provider, `importance_kind == "mean_absolute_signed_contribution"`, and an `additivity_check` whose `max_abs_error` is at most `1e-6` when compared with the model's `decision_function(rows)`. The informative feature's mean absolute contribution ranks above an injected noise feature on the acceptance fixture.

## REQ-AIDS-084: Permutation importance with configurable scoring / スコア指定可能なpermutation importance
Priority: should
Type: functional
Pattern: event-driven
Statement: When a caller requests permutation importance and supplies feature rows and target labels, the system shall return permutation-importance values computed with the caller-selected scoring metric when provided, or the estimator's default score otherwise, labeled with the global-importance kind `permutation`.
Acceptance: Calling `explain_model(..., method="permutation", x=rows, y=labels, scoring="accuracy")` on an acceptance-fixture classifier returns `importance_kind == "permutation"` and ranks the informative feature above an injected noise feature using the mean permutation-importance values.

## REQ-AIDS-022: A/B testing and experiment evaluation / A/Bテスト・実験評価
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests evaluation of an A/B test or experiment, the system shall execute a notebook code cell that computes the statistical significance of the observed difference between groups and reports the result with a markdown interpretation.
Acceptance: An A/B test request on synthetic control and treatment groups with a known effect produces a p-value matching a reference two-sample test within 1e-6.

## REQ-AIDS-023: Japanese NLP and text analysis via GiNZA / GiNZAによる日本語NLP・テキスト分析
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests text analysis on Japanese text, the system shall execute a notebook code cell that uses the GiNZA Japanese NLP pipeline to perform the requested operation and reports the result.
Acceptance: A Japanese text analysis request on a fixed reference sentence produces GiNZA-based tokenization and part-of-speech tags matching the pinned ja_ginza model's output for that sentence.

## REQ-AIDS-024: Interactive dashboard visualization / 簡易ダッシュボード
Priority: should
Type: functional
Pattern: event-driven
Statement: When a user requests an interactive dashboard, the system shall execute a notebook code cell that renders an interactive widget or chart embedded in the notebook output.
Acceptance: A dashboard request produces a cell output containing an interactive HTML or widget MIME bundle in the saved ipynb JSON.

## REQ-AIDS-025: Automated report export / レポート自動生成・エクスポート
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests a report export, the system shall generate a PDF, HTML, or slide file derived from the current notebook content and save it alongside the project notebook.
Acceptance: A report export request produces a file at projects/<project_name>/reports/<name> whose content includes the markdown insight cells and referenced chart images from the source notebook.

## REQ-AIDS-026: Non-Japanese text analysis / 日本語以外のテキスト分析
Priority: should
Type: functional
Pattern: event-driven
Statement: When a user requests text analysis on non-Japanese text, the system shall execute a notebook code cell that performs the requested natural language processing operation using a configured non-Japanese NLP pipeline and reports the result.
Acceptance: A sentiment analysis request on a labeled sample of English texts produces sentiment scores whose polarity direction matches the expected label for at least 80 percent of the sample.

## REQ-AIDS-033: Non-MCP export mechanism boundary / MCP外Export機構の境界
Priority: must
Type: non-functional
Pattern: ubiquitous
Statement: The system shall perform PDF, HTML, or slide export using a locally configured conversion tool outside the Jupyter MCP execution path, restricted to read-only rendering of already-executed notebook content.
Acceptance: A test asserts the report export operation invokes only the configured conversion tool process and issues no additional Jupyter MCP code-execution calls, verified by comparing MCP call counts before and after export.

## REQ-AIDS-074: Reusable cross-validation split strategies / 再利用可能な交差検証分割戦略
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests supervised modeling with a supported cross-validation strategy, the system shall return a reusable fold plan containing the exact train/test row indices for each of the requested `n_splits` folds.
Acceptance: A classification request on an imbalanced labeled dataset with `cv_strategy="StratifiedKFold"` and `n_splits=4` returns exactly 4 fold scores and 4 fold split pairs, every fold test set is disjoint from its own train set, every fold test set contains both classes, and the union of all fold test indices equals the full input index exactly once. A request with `cv_strategy="GroupKFold"`, `n_splits=3`, and repeated group labels returns fold splits where no group label appears in both the train and test side of the same fold. Passing a previously returned fold plan into a second call reuses the identical train/test row indices instead of generating a different split.

## REQ-AIDS-075: Probability-aware configurable supervised scoring / 確率対応の教師あり学習スコア指定
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests supervised modeling with a supported `scoring` value, the system shall return scoring artifacts computed from held-out predictions, including fold-level scores plus out-of-fold predictions and, whenever cross-validation is used with an estimator that implements `predict_proba` or with a probability-based scoring mode, out-of-fold `predict_proba` probabilities aligned to the original input rows.
Acceptance: A binary classification request with `cv_strategy="StratifiedKFold"` and `scoring="roc_auc"` returns an `oof_probabilities` artifact whose positive-class column reproduces `sklearn.metrics.roc_auc_score(y_true, y_score)` within 1e-9 and whose row index matches the input row order exactly. A request with `scoring="log_loss"` returns a metric equal to `sklearn.metrics.log_loss` on the returned out-of-fold class probabilities and is compared in lower-is-better direction. A cross-validation request using a non-probabilistic estimator with a non-probabilistic scoring mode may leave `oof_probabilities` unset while still returning aligned out-of-fold class predictions. A legacy `train_model(...)` call that omits `scoring` and `cv_strategy` continues to expose the existing classification metric keys (`accuracy`, `precision`, `recall`) or regression metric keys (`rmse`, `r2`).

## REQ-AIDS-076: Shared-fold tuning and model comparison / 共通foldを使うチューニング・モデル比較
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests hyperparameter tuning or model comparison with a supported `scoring` value and/or a reusable fold plan, the system shall evaluate every candidate on that same fold plan, report each candidate's fold-level scores and returned modeling artifacts, and select the best candidate using the correct optimization direction for the requested scoring metric.
Acceptance: A classification tuning request with two parameter sets, `scoring="roc_auc"`, and a shared `StratifiedKFold` fold plan returns candidate records whose fold splits are identical to one another and to the supplied plan, and whose `best_metric` equals the maximum candidate metric. A corresponding request with `scoring="log_loss"` returns `best_metric` equal to the minimum candidate metric. Each candidate record includes its fold scores and the reusable modeling result needed to inspect out-of-fold probabilities.

## REQ-AIDS-077: Shared-fold AutoML ranking / 共通foldを使うAutoML順位付け
Priority: should
Type: functional
Pattern: event-driven
Statement: When a user requests automatic model selection with a supported `scoring` value and/or a reusable fold plan, the system shall evaluate every candidate model on that same fold plan and return a ranked comparison whose sort direction matches the requested scoring metric and whose candidate records expose fold-level scores plus the underlying modeling artifacts.
Acceptance: An AutoML classification request with at least three candidate models, `cv_strategy="StratifiedKFold"`, and `scoring="roc_auc"` returns a ranked candidate list sorted in descending metric order, with every candidate referencing the same fold plan. A corresponding request with `scoring="log_loss"` returns the ranked candidate list sorted in ascending metric order. Every candidate record includes its fold scores and the underlying modeling result carrying the out-of-fold probability predictions.

## REQ-AIDS-078: Pluggable sklearn-compatible estimators with backward compatibility / 後方互換性を保つ差し替え可能な推定器
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user supplies an external sklearn-compatible estimator or candidate-estimator mapping, the system shall fit and evaluate that estimator through the existing supervised modeling, tuning, and AutoML entry points while preserving the prior default behavior for calls that omit the new estimator and cross-validation options.
Acceptance: `train_model(..., estimator=<custom estimator>)` fits successfully and returns the requested scoring artifacts, `tune_or_compare(..., grid=[..., {"estimator": <custom estimator>, ...}])` evaluates the supplied estimator on the same scoring path as built-in models, and `run_automl(..., candidate_estimators={"custom": <custom estimator>})` ranks the supplied candidate alongside the built-in models on the same scoring path. Existing calls to `train_model`, `tune_or_compare`, and `run_automl` that omit `estimator`, `candidate_estimators`, `cv_strategy`, `cv_splits`, and `scoring` continue to use the current built-in model defaults, current train/test split behavior, and current legacy metric keys/sort direction.

## REQ-AIDS-111: t-SNE non-linear dimensionality-reduction method / t-SNE非線形次元削減手法
Priority: should
Type: functional
Pattern: event-driven
Statement: When a caller requests the t-SNE clustering method via `clustering.fit_unsupervised_model` for a 2D numeric `x` with `len(x) >= 4`, the system shall compute `sklearn.manifold.TSNE(n_components=n_components, random_state=random_state, perplexity=perplexity, init="pca").fit_transform(x)` using the call signature `fit_unsupervised_model(method="tsne", x, n_components=2, random_state=42, perplexity=30.0)` and report `{embedding}` (an `n_samples x n_components` list of lists).
Acceptance: For a fixed 30-point 2D dataset built from two well-separated Gaussian clusters of 15 points each (`numpy.random.default_rng(0)`, cluster centers `(0,0)` and `(20,20)`, scale `0.3`) with `perplexity=5`, the resulting `embedding` satisfies the structural invariant `mean(pairwise Euclidean distance within a cluster) < mean(pairwise Euclidean distance between the two clusters)` — verified empirically as `mean_within ≈ 6.889` and `mean_between ≈ 63.770` — rather than asserting literal embedding coordinates, since `pyproject.toml` pins `scikit-learn>=1.5` (not an exact version) and `TSNE`'s internal optimizer is not guaranteed bit-identical across minor/major `scikit-learn` releases. Calling with `perplexity=30` on a 4-sample `x` raises `ValueError` naming `perplexity` and the constraint "must be less than the number of samples".
Constraints: Calling with `method` outside the existing `_SUPPORTED_METHODS` set extended with `"tsne"` raises `ValueError` naming `method`; calling with `perplexity >= len(x)` raises `ValueError` naming `perplexity` (the underlying `TSNE` constraint that perplexity must be less than the number of samples). This acceptance criterion is intentionally a version-robust topological invariant (within-cluster vs. between-cluster mean embedding distance), not literal coordinate equality, because `TSNE` is a non-deterministic-across-versions stochastic optimization even with a fixed `random_state` (documented design decision, see this change's dedicated ADR). `sklearn.manifold.TSNE` is already available via the root `pyproject.toml` `scikit-learn>=1.5` dependency; no new dependency is introduced. Only 2D/3D Euclidean embeddings are supported in this increment (parameters beyond `n_components`/`random_state`/`perplexity` use the library defaults).

## REQ-AIDS-112: IsolationForest and Local Outlier Factor anomaly-detection methods / IsolationForestとLocal Outlier Factorによる異常検知手法
Priority: should
Type: functional
Pattern: event-driven
Statement: When a caller requests the isolation-forest or local-outlier-factor anomaly-detection method via `anomaly_detection.detect_anomalies` for a 2D numeric `x` with `len(x) >= 2`, the system shall compute `sklearn.ensemble.IsolationForest(n_estimators=50, random_state=42).fit_predict(x)` when `method="isolation_forest"` or `sklearn.neighbors.LocalOutlierFactor(n_neighbors=min(n_neighbors, len(x) - 1)).fit_predict(x)` (default `n_neighbors=20`) when `method="lof"`, extending the existing `_SUPPORTED_METHODS` set with `{"isolation_forest", "lof"}`, and report `{labels, is_outlier}` where `labels` is the raw per-sample `1`/`-1` prediction array and `is_outlier` is the equivalent boolean list (`True` where `labels == -1`).
Acceptance: For a fixed 20-point dataset (18 points from `numpy.random.default_rng(42).normal(loc=[0,0], scale=0.5, size=(18,2))` plus 2 far-outlier points `[[10,10],[-10,-10]]` appended last), `detect_anomalies("isolation_forest", x)` and `detect_anomalies("lof", x, n_neighbors=5)` each return `labels` as a length-20 list containing only `1`/`-1` values and `is_outlier` as the equivalent length-20 boolean list (`is_outlier[i] == (labels[i] == -1)` for every `i`); this shape/value-domain/boolean-equivalence invariant, plus indices 18 and 19 (the injected far outliers) being flagged `-1`/`True` by both methods, is the required, version-stable behavior (not pinned to one `scikit-learn` release, matching REQ-AIDS-111's structural-invariant approach). For the currently installed `scikit-learn>=1.5`, this fixture is additionally verified empirically to produce the exact arrays `labels = [1,1,-1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,-1,-1]` for `"isolation_forest"` and `labels = [1,1,-1,1,1,1,1,1,1,1,1,1,1,1,1,-1,1,1,-1,-1]` for `"lof"` with `n_neighbors=5`, but exact per-non-outlier-index agreement across arbitrary future `scikit-learn` versions is informative only, not a required pass/fail criterion. Calling with `method="dbscan"` raises `ValueError` naming `method`. Calling `"lof"` with `n_neighbors=0` raises `ValueError` naming `n_neighbors` and the constraint "must be >= 1".
Constraints: Calling with a `method` outside `{"isolation_forest", "lof"}` plus the pre-existing `_SUPPORTED_METHODS` raises `ValueError` naming `method`; calling `"lof"` with `n_neighbors < 1` raises `ValueError` naming `n_neighbors`. `x` must be a 2D list of finite numbers, `len(x) >= 2` (and `>= n_neighbors + 1` for `"lof"`, auto-capped at `len(x) - 1`). Both `sklearn.ensemble.IsolationForest` and `sklearn.neighbors.LocalOutlierFactor` are already available via the root `pyproject.toml` `scikit-learn>=1.5` dependency; no new dependency is introduced. `IsolationForest` results depend on its internal random sampling and are reproducible only for a fixed `random_state` (fixed at `42`, not caller-configurable in this increment); `LocalOutlierFactor` results are deterministic given fixed data and `n_neighbors`.
