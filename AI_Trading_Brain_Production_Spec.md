# AI Trading Brain — Production Spec

---

## 1 — High-level summary

The system ingests live & historical market data (stocks, indices, mutual funds, forex, crypto), computes institutional technical features and patterns, produces probabilistic predictions via an ensemble (XGBoost + LSTM), adjusts predictions with real-time sentiment, and resolves final trade signals via an Agentic Debate (DebateAgent). Signals (entry, SL, targets) are provided to the frontend and optional broker execution.

---

## 2 — Core modules (responsibilities)

### 2.1 Data Intake & Orchestration

* **Sources**: `yfinance` (stocks/indices/MF/forex), `ccxt` (crypto).
* **Real-time**: WebSocket streams where available; poll otherwise.
* **Persistence**: Time-series DB (ClickHouse/TimescaleDB) for tick/candle; Postgres for relational metadata.
* **Resilience**:

  * Health checks per provider.
  * Fallback chain: primary API → secondary API → web-scraper → cached snapshot.
  * Cache last-known-good and freeze execution on degraded data.
* **Contracts**: All price data normalized to: `{symbol, exchange, timeframe, ts, o,h,l,c,v}`.

### 2.2 FeatureEngineer

* Compute per-asset, per-timeframe features:

  * Trend: SMA/EMA(20,50,200), MACD.
  * Momentum: RSI(14), Stochastics.
  * Volatility: Bollinger Bands, ATR(14), realized vol.
  * Volume: VWAP, OBV, volume spikes (z-score).
  * Structure features: HH/HL/LH/LL flags, distance to EMA/MA.
  * Pattern flags: candle patterns, chart pattern detectors (peak/trough detection).
  * Time/market context: session (NY/London/Asia), holiday flags.
* Persist features into `features_table(asset, timeframe, ts, json_features)`.

### 2.3 RegimeAgent

* Classifies market regime (Trending / Ranging / HighVol / LowVol) using ADX, vol, slope metrics.
* Output used to dynamically choose models/weights and allowable strategies.

### 2.4 ML Models (EnsembleModel)

* **XGBoost** for tabular features → fast inference, interpretable feature importance.
* **LSTM** (or Transformer time-series) for sequence forecasting → captures temporal dependencies.
* **Meta-Model / Stacker**: blends model outputs to final probability.
* **Dynamic Weighting**: weights adapt by regime and recent performance (weight optimizer).

### 2.5 SentimentEngine

* Scrapes top-N headlines (Yahoo Finance / site list) per asset; extracts headlines text.
* NLP pipeline:

  * Clean → tokenize → score via lexicon + small transformer (FinBERT or distilled) for sentiment polarity.
  * Compute asset-level sentiment score [0..1], urgency score, event-impact tag.
* Apply time-decay and impact weighting (fresh news > old).

### 2.6 DebateAgent (Decision Resolution)

* Inputs: ensemble probabilities, sentiment score, liquidity, spread, macro flags, OI (for F&O), FII flows.
* Rules:

  * If model says BUY (>P threshold) but sentiment below negative threshold → downgrade confidence or veto.
  * If sentiment extremely positive + model weak → flag for manual review / increased scrutiny.
* Output: final `Signal {direction, entry, sl, targets[], confidence, reason_tags[]}`.

### 2.7 Risk & Execution Engine

* Position sizing: ATR-based + Kelly/percent risk + RL allocator (adaptive).
* Execution rules: limit vs market, slippage cap, order sizing safeguards.
* Broker connectors module with adapter for Zerodha, IB, Binance, MT4/5.
* Circuit breakers: daily loss caps, per-strategy exposure cap.

### 2.8 Feedback & Learning

* Every signal & executed trade is logged to `trades_log` with full context.
* Weekly evaluation job:

  * Performance per strategy, timeframe, regime.
  * Weight adjustment proposals or retraining proposals.
  * Regime-triggered tactical shifts (immediate).
* Retraining pipeline triggers only on threshold events or scheduled windows; governance approval required for full deploy.

### 2.9 Mutual Fund Module (added)

* NAV time-series ingestion, holdings snapshot parsing, AUM.
* Features: expense ratio, turnover, manager tenure, sector allocation, rolling returns.
* Models: XGBoost + LSTM + Prophet for NAV forecasting.
* Outputs: probability of beating benchmark, NAV forecast horizon (6/12/24m), allocation recommendations.

---

## 3 — Data model (core tables)

* `assets(id, symbol, market, exchange, meta_json)`
* `price_history(asset_id, timeframe, ts, o,h,l,c,v)`
* `features(asset_id, timeframe, ts, features_json)`
* `predictions(id, asset_id, model_version, ts, prob_up, expected_move, confidence, features_snapshot)`
* `sentiment(asset_id, ts, score, source, headlines_json)`
* `signals(id, asset_id, ts, mode, direction, entry, sl, targets_json, confidence, reason_tags)`
* `trades(id, signal_id, user_id, status, entry_ts, exit_ts, pnl, execution_meta)`
* `model_versions(version, params, train_window, metrics, registry_uri)`

---

## 4 — API surface (representative)

* `GET /asset/{symbol}/history?tf=1h&from=&to=` → OHLCV
* `GET /asset/{symbol}/features?tf=1h&ts=` → features
* `GET /asset/{symbol}/prediction?tf=1h` → ensemble output
* `POST /signal/generate` (admin/testing)
* `POST /broker/execute` → executes order via configured adapter
* `GET /portfolio/summary`
* `GET /ml/model-versions`
* `POST /ml/propose-retrain`
* `GET /admin/learning/report?period=week`

---

## 5 — Inference & serving

* Serve XGBoost via fast, stateless microservice (FastAPI + joblib/pkl).
* Serve LSTM via TF/ONNX in GPU-enabled inference pods when high throughput required.
* Use Redis for feature cache and low-latency lookups.
* Model registry: MLflow; every model has metadata and reproducible pipeline (DVC + dataset snapshot).

---

## 6 — Training, retraining & CI/CD

* Data versioning (DVC) & dataset snapshots.
* CI for model training: reproducible notebooks → training container → test holdout → backtest → Monte Carlo stress → register model.
* Governance: generate **Model Change Proposal** with backtest report for human approval. Use blue/green or canary deployment.
* Automated tests: unit tests for features; integration tests for pipeline; synthetic stress tests for execution.

---

## 7 — Monitoring & observability

* Metrics: latency, API error rate, signal frequency, model drift (distribution divergence), daily P&L, Sharpe, drawdown per strategy.
* Tools: Prometheus + Grafana, ELK stack for logs.
* Alerts: model drift exceed threshold, data gap, provider health failure, trading anomalies.

---

## 8 — Safety, governance & rollback

* Minimum sample thresholds before model weight changes.
* Max weight delta per cycle (eg. ≤10%).
* Retrain limited to cadence + conditional triggers.
* Governance panel: propose / review / approve / rollback flows; all changes logged immutably.

---

## 9 — UX integration notes

* Frontend receives `signals` and shows: symbol, mode, entry, SL, targets, R:R, confidence, and explanation from `reason_tags` (e.g., "Trend:Up, Sentiment:Neutral, Liquidity:OK, Regime:Trending").
* Multi-timeframe chart overlay: show indicators, S/R zones, predicted move band, and signal marker.
* Mutual fund pages: show NAV forecast band, Monte Carlo simulated wealth curve, and probability of beating benchmark.

---

## 10 — Enhancements to boost robustness & accuracy (summary)

* **Data fallback** and scraping backup (already discussed).
* **Feature diversity**: add order-book features for crypto, OI & PCR for F&O, intraday microstructure (tick-level) features for scalping.
* **Ensemble diversity**: add LightGBM and shallow RandomForest for more robustness; consider temporal fusion transformer for multi-horizon forecasting.
* **Explainability**: SHAP value snapshots per prediction for transparency.
* **Online learning**: allow incremental updates for XGBoost/LightGBM where safe; LSTM retrain periodically.
* **Synthetic RL simulator**: train RL allocator in simulated regimes to learn defensive sizing.
* **Adversarial tests**: run stressed market scenarios (flash crashes) in sandbox to validate circuit breakers.
* **Human-in-the-loop**: provide suggested edits to rules and accept manual overrides; capture human corrections as training signal.

---

## 11 — Security & compliance highlights

* TLS everywhere; secrets in K8s secrets / HashiVault.
* RBAC and audit logs for all governance actions.
* For live fund management (RIA/PMS/AIF), ensure recordkeeping, client approvals, disclosures, and regulatory reporting pipelines (SEBI-specific compliance design required).

---

## 12 — Acceptance criteria & success metrics

* Data integrity: < 15s lag for intraday, < 1% missing ticks.
* Model performance: backtested Sharpe > target; live sample: sustained edge (positive expectancy).
* Production stability: 99.9% uptime for core API; alert responses < 15min.
* Safety: zero unapproved model deployments; automated circuit breaker triggers functioning.

---

## 13 — Suggested next engineering tasks (immediate roadmap)

1. Implement Data Orchestrator + feature store (0–2 weeks).
2. Implement FeatureEngineer for 1 timeframe + XGBoost prototype (2–4 weeks).
3. Build SentimentEngine prototype + scraper (2–3 weeks).
4. Wire DebateAgent to combine XGBoost/LSTM + sentiment (2 weeks).
5. Implement signal schema + frontend mockups for signal display (2 weeks).
6. Add trade logging and simple risk engine; connect a paper-broker adapter (2–3 weeks).
7. Add weekly evaluator job + model registry (4 weeks).
8. Run thorough backtest + Monte Carlo; produce governance panel proposal (2 weeks).
