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
Statement: When a user requests feature engineering, the system shall execute a notebook code cell that applies the requested encoding, scaling, or feature selection transformation and reports the resulting feature set.
Acceptance: A one-hot encoding request on a categorical column produces new dummy columns matching the pandas get_dummies reference output, listed in the cell output.

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
Statement: When a user requests an explanation of a trained model, the system shall execute a notebook code cell that computes feature importance or SHAP values and reports them alongside a markdown interpretation.
Acceptance: An explainability request on a trained classifier produces a feature importance ranking whose top feature matches the reference scikit-learn feature_importances_ or SHAP value ordering.

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
