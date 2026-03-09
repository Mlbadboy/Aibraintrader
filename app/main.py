from fastapi import FastAPI, HTTPException, BackgroundTasks
# from app.agents.data_agent import DataAgent
# from app.agents.failsafe_agent import FailsafeAgent
# from app.features.indicators import FeatureEngineer
# from app.agents.regime_agent import RegimeAgent
# from app.patterns.candle_patterns import CandlePatternEngine
# from app.patterns.chart_patterns import ChartPatternEngine
# from app.sentiment.news_scraper import SentimentEngine
# from app.agents.strategy_agent import StrategyAgent
# from app.models.ensemble import EnsembleModel
# from app.agents.debate_agent import DebateAgent
# from app.agents.risk_agent import RiskGuardian
# from app.agents.classification_agent import ClassificationAgent
# from app.agents.options_agent import OptionsAgent
# from app.execution.paper_broker import PaperBroker
# from app.feedback.loop import FeedbackLoop
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging
import pandas as pd
from datetime import datetime, timezone, timedelta
from app.journal.db import JournalDB
from app.security.gatekeeper import SecureCoreGuard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Market Hours Helper ───────────────────────────────────────────────────────
IST  = timezone(timedelta(hours=5, minutes=30))
EST  = timezone(timedelta(hours=-5))

def get_market_status() -> dict:
    """
    Returns real-time open/closed status for NSE, NYSE, and Crypto.
    NSE: Mon-Fri, 09:15-15:30 IST (excludes national holidays — basic check only)
    NYSE: Mon-Fri, 09:30-16:00 EST
    Crypto: Always open
    """
    now_ist  = datetime.now(IST)
    now_est  = datetime.now(EST)
    weekday  = now_ist.weekday()   # 0=Mon … 6=Sun

    def _time_in_range(now, start_h, start_m, end_h, end_m):
        t = now.hour * 60 + now.minute
        return (start_h * 60 + start_m) <= t <= (end_h * 60 + end_m)

    # NSE / BSE
    nse_open = (
        weekday < 5 and
        _time_in_range(now_ist, 9, 15, 15, 30)
    )
    nse_reason = (
        "Market open" if nse_open else
        "Weekend — NSE closed" if weekday >= 5 else
        "Pre-market" if now_ist.hour < 9 or (now_ist.hour == 9 and now_ist.minute < 15) else
        "After-hours — NSE closed (closes 15:30 IST)"
    )

    # NYSE
    nyse_wd   = now_est.weekday()
    nyse_open = (nyse_wd < 5 and _time_in_range(now_est, 9, 30, 16, 0))

    return {
        "NSE":    {"open": nse_open,  "reason": nse_reason,  "local_time": now_ist.strftime('%H:%M IST')},
        "NYSE":   {"open": nyse_open, "reason": "Open" if nyse_open else "Closed", "local_time": now_est.strftime('%H:%M EST')},
        "CRYPTO": {"open": True,      "reason": "24/7",      "local_time": now_ist.strftime('%H:%M IST')},
        "any_open": nse_open or nyse_open,
        "weekday": weekday,
        "generated_at": datetime.now(IST).isoformat(),
    }

import os

app_env = os.getenv("APP_ENV", "development")
is_debug = app_env == "development"

app = FastAPI(title="AI Stock & Crypto Analyzer", debug=is_debug)

# Configure CORS
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """System health monitor"""
    return {
        "status": "healthy",
        "env": app_env,
        "timestamp": datetime.now().isoformat()
    }

# Global placeholders for lazy loading
data_agent = None
failsafe_agent = None
feature_engineer = None
regime_agent = None
candle_engine = None
chart_engine = None
sentiment_engine = None
strategy_agent = None
ensemble_model = None
debate_agent = None
classification_agent = None
options_agent = None
risk_guardian = None
paper_broker = None

def init_engines():
    global data_agent, failsafe_agent, feature_engineer, regime_agent, candle_engine, chart_engine, sentiment_engine, strategy_agent, ensemble_model, debate_agent, classification_agent, options_agent, risk_guardian, paper_broker
    if data_agent is not None:
        return
    from app.agents.data_agent import DataAgent
    from app.agents.failsafe_agent import FailsafeAgent
    from app.features.indicators import FeatureEngineer
    from app.agents.regime_agent import RegimeAgent
    from app.patterns.candle_patterns import CandlePatternEngine
    from app.patterns.chart_patterns import ChartPatternEngine
    from app.sentiment.news_scraper import SentimentEngine
    from app.agents.strategy_agent import StrategyAgent
    from app.models.ensemble import EnsembleModel
    from app.agents.debate_agent import DebateAgent
    from app.agents.risk_agent import RiskGuardian
    from app.agents.classification_agent import ClassificationAgent
    from app.agents.options_agent import OptionsAgent
    from app.execution.paper_broker import PaperBroker
    
    data_agent = DataAgent()
    failsafe_agent = FailsafeAgent()
    feature_engineer = FeatureEngineer()
    regime_agent = RegimeAgent()
    candle_engine = CandlePatternEngine()
    chart_engine = ChartPatternEngine()
    sentiment_engine = SentimentEngine()
    strategy_agent = StrategyAgent()
    ensemble_model = EnsembleModel()
    debate_agent = DebateAgent()
    classification_agent = ClassificationAgent()
    options_agent = OptionsAgent()
    risk_guardian = RiskGuardian(max_risk_per_trade_pct=0.02)
    paper_broker = PaperBroker()

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Stock & Crypto Trading Brain API"}

@app.get("/market/status")
def market_status():
    """Returns real-time open/closed status for NSE, NYSE, and Crypto with local times."""
    return {"status": "success", "data": get_market_status()}

@SecureCoreGuard.wrap_orchestration
def _run_full_pipeline(symbol: str, df, asset_type: str = "stock"):
    """
    Orchestrates the agentic pipeline. 
    Wrapped by SecureCoreGuard to encrypt workflow details in public responses.
    """
    if df.empty:
        return {"error": "Insufficient data"}
        
    df = feature_engineer.add_technical_indicators(df)
    df = candle_engine.add_patterns(df)
    df = chart_engine.add_patterns(df)
    
    # Fill any NaNs that might have been introduced by indicators or missing data (e.g. index volume)
    df.fillna(0, inplace=True)
    
    # 1. Market Regime
    regime = regime_agent.analyze(df)
    
    # 2. Strategy Selection
    strategy = strategy_agent.select_strategy(regime)
    
    # 3. Sentiment Analysis
    sentiment_data = sentiment_engine.analyze_sentiment(symbol)
    
    # 4. ML Prediction
    ml_preds = ensemble_model.predict(df, regime)
    
    current_price = df['close'].iloc[-1]
    atr_val = df['atr'].iloc[-1]
    
    # 5. Debate Outcome (Signal Generation)
    final_decision = debate_agent.generate_signal(
        symbol=symbol,
        current_price=current_price,
        atr=atr_val,
        ml_bull_prob=ml_preds['bull_prob'],
        sentiment_score=sentiment_data['score']
    )
    
    # 6. Risk Assessment
    # Defaulting capital to 10k for demonstration in the API response
    risk_assessment = risk_guardian.assess_trade(
        decision=final_decision,
        current_price=current_price,
        atr=atr_val,
        capital=10000.0 
    )
    
    # Extract latest indicators
    latest = df.iloc[-1].to_dict()
    latest["timestamp"] = str(latest["timestamp"])
    
    payload = {
        "symbol": symbol,
        "tv_symbol": data_agent.get_tv_symbol(symbol), # Force frontend chart to match this exactly
        "regime": regime,
        "selected_strategy": strategy,
        "sentiment": sentiment_data,
        "ml_predictions": ml_preds,
        "trading_decision": final_decision,
        "risk_assessment": risk_assessment,
        "latest_indicators": latest
    }
    
    # 7. Classification
    classification = classification_agent.classify(payload, df)
    payload["classification"] = classification
    
    # 8. Options Protocol (F&O)
    # If the system classifies this as F&O (like NIFTY/BANKNIFTY) or we know it has derivatives
    fo_symbols = ["NIFTY", "BANKNIFTY", "SENSEX", "BANKEX", "FINNIFTY", "AAPL", "TSLA", "^NSEI", "^BSESN", "^NSEBANK", "BSE-BANK.BO", "NIFTY_FIN_SERVICE.NS"]
    
    # Explicitly bypass Crypto because yfinance strictly deadlocks when attempting to fetch options chains for crypto tickers
    if (classification == "F&O" or symbol in fo_symbols) and asset_type.lower() != "crypto":
        # We need the target price. The risk guardian outputs targets based on ATR.
        target_price = 0
        if "target_1" in risk_assessment.get("notes", ""):
            import re
            match = re.search(r'target_1:\s*([\d\.]+)', risk_assessment["notes"])
            if match:
                target_price = float(match.group(1))
        
        # If no target extracted, assume 1% move
        if not target_price:
            target_price = current_price * 1.01 if final_decision["decision"] == "BUY" else current_price * 0.99
            
        options_data = options_agent.select_strike(
            underlying_symbol=symbol,
            current_price=current_price,
            ai_decision=final_decision["decision"],
            target=target_price
        )
        payload["options_strategy"] = options_data
    
    # 9. Execution (Paper Trading)
    execution_result = paper_broker.execute_signal(final_decision)
    payload["execution_status"] = execution_result
    
    # 10. Self-Learning Feedback Loop (Log decision)
    from app.feedback.loop import FeedbackLoop
    FeedbackLoop.log_prediction(symbol, payload)
    
    return payload

def run_pipeline_for_asset(symbol: str, asset_type: str, interval: str="1h", period: str="3mo", limit: int=500):
    """Fetches data and runs the pipeline for any asset type."""
    init_engines()
    if asset_type == "crypto":
        formatted_symbol = symbol.upper()
        if '/' not in formatted_symbol:
            if formatted_symbol.endswith('USDT'):
                formatted_symbol = formatted_symbol[:-4] + '/USDT'
            elif formatted_symbol.endswith('USD'):
                formatted_symbol = formatted_symbol.replace('-USD', '').replace('USD', '') + '/USDT'
            else:
                formatted_symbol = f"{formatted_symbol}/USDT"
        
        df = data_agent.fetch_crypto_data(formatted_symbol, interval, limit=limit)
        sym_to_pass = formatted_symbol
    else:
        df = data_agent.fetch_stock_data(symbol, interval, period)
        sym_to_pass = symbol
        
    if df.empty:
        if asset_type == "stock":
             # Fallback
             scrape_data = failsafe_agent.scrape_yahoo_finance(symbol)
             if scrape_data:
                 return {"symbol": symbol, "current_price": scrape_data["price"], "status": "Fallback - Insufficient data for full pipeline", "error": "Insufficient data"}
        return {"error": "Insufficient data"}
        
    return _run_full_pipeline(sym_to_pass, df, asset_type)

@app.get("/analyze/stock/{symbol}")
def analyze_stock(symbol: str, interval: str = "1h", period: str = "3mo"):
    logger.info(f"Starting Full Pipeline for Stock: {symbol}")
    result = run_pipeline_for_asset(symbol, "stock", interval, period)
    if "error" in result and "Fallback" not in result.get("status", ""):
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/analyze/crypto/{symbol}")
def analyze_crypto(symbol: str, interval: str = "1h", limit: int = 500):
    logger.info(f"Starting Full Pipeline for Crypto: {symbol}")
    result = run_pipeline_for_asset(symbol, "crypto", interval, limit=limit)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

# --- Phase 6: Radar Endpoints ---
from app.radar.database import RadarDB
from app.radar.scheduler import RadarScheduler
from pydantic import BaseModel

class WatchlistRequest(BaseModel):
    asset_type: str = "stock"
    horizon: str = "SHORT"

from fastapi import BackgroundTasks

@app.post("/radar/watchlist/{symbol}")
def add_to_watchlist(symbol: str, req: WatchlistRequest, background_tasks: BackgroundTasks):
    success = RadarDB.add_to_watchlist(symbol, req.asset_type, req.horizon)
    if success:
        # Trigger immediate scan in background so UI updates "Awaiting Scan Cycle" quickly
        def immediate_scan_task(s, t, h):
            logger.info(f"Triggering immediate background scan for injected asset: {s}")
            # Map horizon to interval/period
            from app.radar.scheduler import HORIZON_MAP
            config = HORIZON_MAP.get(h.upper(), HORIZON_MAP["SHORT"])
            try:
                payload = run_pipeline_for_asset(
                    s, t, 
                    interval=config['interval'], 
                    period=config.get('period', '1mo'),
                    limit=config.get('limit', 500)
                )
                if payload and "error" not in payload:
                    RadarDB.update_result(s, h.upper(), payload)
                    logger.info(f"Immediate scan success for {s}")
                else:
                    logger.error(f"Immediate scan failed for {s}: {payload.get('error') if payload else 'No payload'}")
            except Exception as e:
                logger.error(f"Immediate scan failed for {s}: {e}")

        background_tasks.add_task(immediate_scan_task, symbol.upper(), req.asset_type, req.horizon)
        
        return {"status": "Added", "symbol": symbol, "type": req.asset_type, "horizon": req.horizon}
    return {"status": "Already Exists", "symbol": symbol}

@app.get("/radar/live")
def get_live_radar(horizon: str = None):
    """Returns the latest classification and analysis, optionally filtered by horizon."""
    results = RadarDB.get_all_results(horizon)
    return {"status": "success", "count": len(results), "data": results}

@app.get("/radar/signals")
def get_top_signals(horizon: str = None):
    """Returns high-confidence BUY/SELL signals with full trade details and target qualifier."""
    results = RadarDB.get_all_results(horizon)

    # Load all user profit targets once for the whole request
    try:
        user_targets = {t['symbol']: t for t in JournalDB.get_targets()}
    except Exception:
        user_targets = {}

    signals = []
    for r in results:
        decision = r.get('decision', 'HOLD')
        confidence = r.get('confidence', 0)
        raw = r.get('raw_payload', {}) or {}

        # Only surface actionable BUY or SELL with good confidence
        if decision in ('BUY', 'SELL') and confidence >= 0.55:
            risk = raw.get('risk_assessment', {}) or {}
            td   = raw.get('trading_decision', {}) or {}
            ml   = raw.get('ml_predictions', {}) or {}
            indicators = raw.get('latest_indicators', {}) or {}

            # Entry: live price first, fall back to what debate agent recorded
            entry_price = r.get('current_price', 0) or td.get('entry') or risk.get('entry_price', 0)

            # SL: try risk_assessment, then debate_agent's 'sl' key
            stop_loss   = risk.get('stop_loss') or td.get('sl', 0)

            # Target: try risk_assessment, then targets list from debate_agent
            targets_list = td.get('targets', [])
            take_profit = risk.get('take_profit') or (targets_list[1] if len(targets_list) > 1 else (targets_list[0] if targets_list else 0))

            # Final fallback: ATR-based levels (1.5x SL, 2.5x target)
            if entry_price and not stop_loss:
                atr = indicators.get('atr', entry_price * 0.01) or (entry_price * 0.01)
                stop_loss   = round(entry_price - (1.5 * atr), 4) if decision == 'BUY' else round(entry_price + (1.5 * atr), 4)
                take_profit = round(entry_price + (2.5 * atr), 4) if decision == 'BUY' else round(entry_price - (2.5 * atr), 4)

            # Risk:Reward ratio
            risk_reward = 0
            if stop_loss and take_profit and entry_price and abs(entry_price - stop_loss) > 0:
                reward = abs(take_profit - entry_price)
                risk_amt = abs(entry_price - stop_loss)
                risk_reward = round(reward / risk_amt, 2)

            # ── TARGET QUALIFIER (Option B) ────────────────────────────────────
            # Check if the predicted move (|TP - Entry|) meets the user's goal
            symbol_key = r.get('symbol', '').upper()
            tgt = user_targets.get(symbol_key)
            predicted_move = abs(float(take_profit or 0) - float(entry_price or 0))

            if tgt is None:
                target_status   = 'NO_TARGET'          # No goal set for this symbol
                target_label    = None
                target_gap      = None
            else:
                goal_pts  = tgt.get('target_points', 0)
                goal_pct  = tgt.get('target_pct', 0)
                goal_amt  = tgt.get('target_amount', 0)

                # Evaluate against whichever target type is set (points takes priority)
                if goal_pts and goal_pts > 0:
                    meets = predicted_move >= goal_pts
                    target_label  = f"{goal_pts} pts"
                    target_gap    = round(predicted_move - goal_pts, 2)
                elif goal_pct and goal_pct > 0 and entry_price:
                    predicted_pct = (predicted_move / float(entry_price)) * 100
                    meets = predicted_pct >= goal_pct
                    target_label  = f"{goal_pct}%"
                    target_gap    = round(predicted_pct - goal_pct, 2)
                elif goal_amt and goal_amt > 0:
                    lot = tgt.get('lot_size', 1) or 1
                    predicted_amt = predicted_move * lot
                    meets = predicted_amt >= goal_amt
                    target_label  = f"₹{goal_amt}"
                    target_gap    = round(predicted_amt - goal_amt, 2)
                else:
                    meets = False
                    target_label  = None
                    target_gap    = None

                target_status = 'MEETS_TARGET' if meets else 'BELOW_TARGET'

            signals.append({
                **r,
                'entry_price':    round(float(entry_price), 4)  if entry_price  else None,
                'stop_loss':      round(float(stop_loss), 4)     if stop_loss    else None,
                'take_profit':    round(float(take_profit), 4)   if take_profit  else None,
                'predicted_move': round(predicted_move, 4),
                'risk_reward':    risk_reward,
                'bull_prob':      round(ml.get('bull_prob', 0), 3),
                'bear_prob':      round(ml.get('bear_prob', 0), 3),
                'signal_strength': 'STRONG' if confidence >= 0.75 else 'MODERATE',
                'reason_tags':    td.get('reason_tags', []),
                # Target qualifier fields
                'target_status':  target_status,   # MEETS_TARGET | BELOW_TARGET | NO_TARGET
                'target_label':   target_label,    # e.g. "50 pts" or "2%"
                'target_gap':     target_gap,      # positive = exceeds target, negative = short
            })

    signals.sort(key=lambda x: x.get('confidence', 0), reverse=True)
    return {"status": "success", "data": signals[:15]}

@app.get("/radar/accuracy")
def get_radar_accuracy():
    """Computes real model accuracy, win rate, and trade statistics from the feedback loop database."""
    import sqlite3
    try:
        FEEDBACK_DB = "app/feedback/feedback.db"
        conn = sqlite3.connect(FEEDBACK_DB)
        cursor = conn.cursor()
        
        # Count resolved trades (WIN/LOSS)
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE outcome IN ('WIN', 'LOSS')")
        resolved = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE outcome = 'WIN'")
        wins = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE outcome = 'PENDING'")
        pending = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM predictions")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(actual_pnl) FROM predictions WHERE outcome = 'WIN'")
        gross_profit = cursor.fetchone()[0] or 0.0
        
        cursor.execute("SELECT SUM(actual_pnl) FROM predictions WHERE outcome = 'LOSS'")
        gross_loss = cursor.fetchone()[0] or 0.0

        # High confidence signal breakdown
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE confidence >= 0.75 AND outcome = 'WIN'")
        hc_wins = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE confidence >= 0.75 AND outcome IN ('WIN','LOSS')")
        hc_total = cursor.fetchone()[0]
        
        conn.close()
        
        win_rate = (wins / resolved * 100) if resolved > 0 else 0.0
        hc_accuracy = (hc_wins / hc_total * 100) if hc_total > 0 else 0.0
        profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else (1.0 if gross_profit == 0 else 9.99)
        
        return {
            "status": "success",
            "total_predictions": total,
            "resolved": resolved,
            "pending": pending,
            "wins": wins,
            "losses": resolved - wins,
            "win_rate": round(win_rate, 1),
            "high_confidence_accuracy": round(hc_accuracy, 1),
            "gross_profit": round(gross_profit, 2),
            "gross_loss": round(gross_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "data_note": "Win/Loss outcomes are evaluated when price hits SL or TP. Pending = awaiting resolution."
        }
    except Exception as e:
        return {"status": "error", "win_rate": 0.0, "error": str(e), "total_predictions": 0}

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 29: TRADE JOURNAL — FULL TARGET LIFECYCLE + REALTIME WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════════

class TargetRequest(BaseModel):
    asset_type:    Optional[str]   = 'stock'
    target_points: Optional[float] = 0.0
    target_amount: Optional[float] = 0.0
    target_pct:    Optional[float] = 0.0
    lot_size:      Optional[int]   = 1
    notes:         Optional[str]   = ''

@app.get("/journal/trades")
def get_journal_trades(
    date_from: str = None, date_to: str = None,
    symbol: str = None, outcome: str = None, limit: int = 200
):
    try:
        trades = JournalDB.get_trades(date_from=date_from, date_to=date_to,
                                      symbol=symbol, outcome=outcome, limit=limit)
        return {"status": "success", "count": len(trades), "data": trades}
    except Exception as e:
        return {"status": "error", "data": [], "error": str(e)}

@app.get("/journal/targets")
def get_profit_targets(status: str = 'ACTIVE'):
    """Returns targets filtered by status: ACTIVE | COMPLETED | FAILED | ALL"""
    try:
        return {"status": "success", "data": JournalDB.get_targets(status=status)}
    except Exception as e:
        return {"status": "error", "data": [], "error": str(e)}

@app.get("/journal/active-targets")
def get_active_targets_with_signals():
    """
    Returns ACTIVE targets enriched with their latest live radar signal.
    The signal includes entry/SL/TP/predicted_move/target_status.
    Called every 30s by the frontend for realtime updates.
    """
    try:
        # Get current radar signals (with target qualifiers already computed)
        from app.radar.database import RadarDB
        results = RadarDB.get_all_results(None)
        user_targets = {t['symbol']: t for t in JournalDB.get_targets('ACTIVE')}

        # Rebuild signal list with qualifier logic for active targets only
        signals_for_targets = []
        for r in results:
            sym = (r.get('symbol') or '').upper()
            if sym not in user_targets:
                continue
            decision   = r.get('decision', 'HOLD')
            confidence = r.get('confidence', 0)
            if decision not in ('BUY', 'SELL') or confidence < 0.50:
                continue

            raw  = r.get('raw_payload', {}) or {}
            risk = raw.get('risk_assessment', {}) or {}
            td   = raw.get('trading_decision', {}) or {}
            ml   = raw.get('ml_predictions', {}) or {}
            ind  = raw.get('latest_indicators', {}) or {}

            entry_price  = r.get('current_price', 0) or td.get('entry') or risk.get('entry_price', 0)
            stop_loss    = risk.get('stop_loss') or td.get('sl', 0)
            targets_list = td.get('targets', [])
            take_profit  = risk.get('take_profit') or (
                targets_list[1] if len(targets_list) > 1 else (targets_list[0] if targets_list else 0))

            if entry_price and not stop_loss:
                atr = ind.get('atr', entry_price * 0.01) or (entry_price * 0.01)
                stop_loss   = round(entry_price - 1.5*atr, 4) if decision == 'BUY' else round(entry_price + 1.5*atr, 4)
                take_profit = round(entry_price + 2.5*atr, 4) if decision == 'BUY' else round(entry_price - 2.5*atr, 4)

            predicted_move = abs(float(take_profit or 0) - float(entry_price or 0))
            tgt = user_targets.get(sym, {})

            goal_pts = tgt.get('target_points', 0) or 0
            goal_pct = tgt.get('target_pct', 0)    or 0
            goal_amt = tgt.get('target_amount', 0)  or 0
            lot      = tgt.get('lot_size', 1)        or 1

            if goal_pts > 0:
                meets = predicted_move >= goal_pts
                target_label = f"{goal_pts} pts"
                target_gap   = round(predicted_move - goal_pts, 2)
            elif goal_pct > 0 and entry_price:
                pct = (predicted_move / float(entry_price)) * 100
                meets = pct >= goal_pct
                target_label = f"{goal_pct}%"
                target_gap   = round(pct - goal_pct, 2)
            elif goal_amt > 0:
                predicted_amt = predicted_move * lot
                meets = predicted_amt >= goal_amt
                target_label = f"₹{goal_amt}"
                target_gap   = round(predicted_amt - goal_amt, 2)
            else:
                meets = True; target_label = None; target_gap = None

            signals_for_targets.append({
                'symbol':         sym,
                'horizon':        r.get('horizon'),
                'decision':       decision,
                'confidence':     round(confidence, 3),
                'entry_price':    round(float(entry_price), 4) if entry_price else None,
                'stop_loss':      round(float(stop_loss), 4) if stop_loss else None,
                'take_profit':    round(float(take_profit), 4) if take_profit else None,
                'predicted_move': round(predicted_move, 4),
                'bull_prob':      round(ml.get('bull_prob', 0), 3),
                'bear_prob':      round(ml.get('bear_prob', 0), 3),
                'target_status':  'MEETS_TARGET' if meets else 'BELOW_TARGET',
                'target_label':   target_label,
                'target_gap':     target_gap,
                'reason_tags':    td.get('reason_tags', []),
                'signal_strength': 'STRONG' if confidence >= 0.75 else 'MODERATE',
                # ── Staleness & market hours ──────────────────────────────────
                'signal_timestamp': r.get('timestamp'),   # when radar last scanned this
            })

        # Compute market status and signal staleness
        mkt = get_market_status()
        now_utc = datetime.now(timezone.utc)

        def _enrich_signal(sig):
            if not sig:
                return sig
            # ── Use the actual radar DB field name: 'last_scanned' (not 'timestamp') ──
            ts = sig.get('signal_timestamp') or sig.get('last_scanned')
            age_hours = None
            if ts:
                try:
                    dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    age_hours = round((now_utc - dt).total_seconds() / 3600, 1)
                except Exception:
                    age_hours = None

            sym_upper = (sig.get('symbol', '') or '').upper()
            is_crypto = any(c in sym_upper for c in ['BTC', 'ETH', 'USDT', 'BNB', 'DOGE', 'SOL', 'XRP', 'ADA', 'MATIC'])

            if is_crypto:
                market_open = True  # Crypto is always open 24/7
                # Crypto signals stay fresh for 24h (continuous market)
                is_fresh = age_hours is None or age_hours <= 24
            elif any(idx in sym_upper for idx in ['NIFTY', 'SENSEX', 'BANKNIFTY', 'NSEBANK', '.NS', '.BO']):
                market_open = mkt['NSE']['open']
                is_fresh = market_open and age_hours is not None and age_hours <= 4
            else:
                # Default: Indian market
                market_open = mkt['NSE']['open']
                is_fresh = market_open and age_hours is not None and age_hours <= 4

            return {
                **sig,
                'signal_age_hours': age_hours,
                'market_open':      market_open,
                'signal_fresh':     is_fresh,
                # If market closed or signal stale, override the qualifier to STALE
                'target_status': (sig['target_status'] if is_fresh else 'STALE'),
            }

        # Enrich targets
        sig_map   = {s['symbol']: _enrich_signal(s) for s in signals_for_targets}
        active    = JournalDB.get_targets('ACTIVE')
        enriched  = [{**t, 'live_signal': sig_map.get(t['symbol'])} for t in active]

        return {
            "status":        "success",
            "data":          enriched,
            "market_status": mkt,  # send full market status so frontend can show the banner
        }
    except Exception as e:
        logger.error(f"Active targets error: {e}")
        return {"status": "error", "data": [], "error": str(e)}

@app.post("/journal/targets/{symbol}")
def set_profit_target(symbol: str, req: TargetRequest):
    """Set a new ACTIVE profit target. Replaces any existing ACTIVE target for symbol."""
    try:
        result = JournalDB.set_target(
            symbol=symbol, asset_type=req.asset_type,
            target_points=req.target_points, target_amount=req.target_amount,
            target_pct=req.target_pct, lot_size=req.lot_size, notes=req.notes
        )
        return {"status": "success", "message": f"Target set for {symbol.upper()}", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/journal/targets/{symbol}")
def delete_profit_target(symbol: str):
    try:
        JournalDB.delete_target(symbol)
        return {"status": "success", "message": f"Target removed for {symbol.upper()}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/journal/resolve")
def resolve_targets():
    """
    Manually trigger target resolution check.
    (Also runs automatically after every feedback loop cycle.)
    """
    try:
        resolved = JournalDB.resolve_targets_from_feedback()
        return {"status": "success", "resolved": resolved, "count": len(resolved)}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/journal/eod-report")
def get_eod_report(date: str = None):
    try:
        report = JournalDB.generate_eod_report(report_date=date)
        return {"status": "success", "data": report}
    except Exception as e:
        return {"status": "error", "data": {}, "error": str(e)}

@app.get("/journal/eod-history")
def get_eod_history(limit: int = 30):
    try:
        return {"status": "success", "data": JournalDB.get_eod_reports(limit=limit)}
    except Exception as e:
        return {"status": "error", "data": [], "error": str(e)}

@app.post("/journal/retrain")
def trigger_retrain(background_tasks: BackgroundTasks):
    """
    Export labeled WIN/LOSS trade data from feedback.db and trigger a
    lightweight model retrain cycle using the latest outcomes.
    """
    def _do_retrain():
        try:
            training_data = JournalDB.export_training_data()
            if len(training_data) < 10:
                logger.warning("Not enough resolved trades to retrain (need >= 10).")
                return
            import json, os
            os.makedirs("app/training_data", exist_ok=True)
            out_path = "app/training_data/feedback_labels.json"
            with open(out_path, "w") as f:
                json.dump(training_data, f, indent=2)
            logger.info(f"Retrain: exported {len(training_data)} labeled rows to {out_path}")
            # Hook into the XGBoost runner if available
            try:
                from app.models.xgboost_runner import XGBoostRunner
                runner = XGBoostRunner()
                runner.retrain_from_feedback(out_path)
                logger.info("XGBoost model retrained on new feedback data.")
            except Exception as me:
                logger.warning(f"Model retraining skipped (runner unavailable): {me}")
        except Exception as e:
            logger.error(f"Retrain background task error: {e}")

    background_tasks.add_task(_do_retrain)
    return {"status": "queued", "message": "Model retraining triggered in background."}

@app.post("/admin/nse-sync")
async def manual_nse_sync(background_tasks: BackgroundTasks):
    """
    Manually trigger a full NSE instrument sync.
    Downloads all equities, F&O stocks, ETFs, commodities, indices and crypto
    from NSE India archives and adds them to the radar watchlist.
    Same job that runs automatically every Sunday 08:00 IST.
    """
    def _do_sync():
        try:
            from app.data.nse_importer import run_weekly_nse_sync
            summary = run_weekly_nse_sync(max_equities=500)
            logger.info(f"Manual NSE sync complete: {summary}")
        except Exception as e:
            logger.error(f"Manual NSE sync error: {e}")

    background_tasks.add_task(_do_sync)
    return {
        "status": "queued",
        "message": "NSE full instrument sync started in background. "
                   "This imports all stocks, F&O, ETFs, commodities, indices and crypto. "
                   "Check logs for progress."
    }


@app.on_event("startup")
def startup_event():
    # init_engines() # Don't init heavy engines on startup yet to bypass hang
    from app.radar.scheduler import RadarScheduler
    # Pass dummy data agent for now, we'll fix scheduler to lazy load too
    from app.agents.data_agent import DataAgent
    da = DataAgent()
    rs = RadarScheduler(run_pipeline_for_asset, da)
    rs.start()
    
@app.on_event("shutdown")
def shutdown_event():
    pass

# --- Phase 7: Mutual Fund Engine Imports ---
# from app.agents.mf_data_agent import MFDataAgent
# from app.features.mf_indicators import MFRiskEngine
# from app.models.mf_predictor import MFPredictor
# from app.models.mf_forecaster import MFForecaster
# from app.agents.investor_matcher import InvestorMatcher
# from app.features.sip_forecaster import SIPForecaster

mf_data = None
mf_risk = None
mf_pred = None
mf_forecaster = None
mf_matcher = None
sip_calc = None

def init_mf_engines():
    global mf_data, mf_risk, mf_pred, mf_forecaster, mf_matcher, sip_calc
    if mf_data is None:
        from app.agents.mf_data_agent import MFDataAgent
        from app.features.mf_indicators import MFRiskEngine
        from app.models.mf_predictor import MFPredictor
        from app.models.mf_forecaster import MFForecaster
        from app.agents.investor_matcher import InvestorMatcher
        from app.features.sip_forecaster import SIPForecaster
        
        mf_data = MFDataAgent()
        mf_risk = MFRiskEngine()
        mf_pred = MFPredictor()
        mf_forecaster = MFForecaster()
        mf_matcher = InvestorMatcher()
        sip_calc = SIPForecaster()

@app.get("/analyze/mutualfund/{symbol}")
def analyze_mutual_fund(symbol: str, user_profile: str = "Moderate", monthly_sip: float = 10000.0, sip_years: int = 5):
    """
    Institutional-Grade Phase 7 Pipeline for MFs/ETFs.
    """
    logger.info(f"Starting MF Intelligence Pipeline for: {symbol}")
    init_mf_engines()
    
    # 1. Fetch Data
    df = mf_data.fetch_nav_history(symbol, period="5y")
    meta = mf_data.fetch_fund_metadata(symbol)
    
    if df.empty:
        raise HTTPException(status_code=404, detail="Mutual Fund NAV history not found on standard providers.")
        
    # 2. Risk Intelligence
    risk_metrics = mf_risk.analyze_risk(df)
    
    # 3. AI Prediction Engine (Probabilities)
    predictions = mf_pred.predict_probabilities(df, risk_metrics)
    
    # 4. NAV Forecasting (Prophet)
    forecast = mf_forecaster.forecast_nav(df, periods_days=365)
    
    # 5. Investor Matching
    match_result = mf_matcher.match_profile(
        user_profile=user_profile, 
        risk_score=risk_metrics.get("risk_score_100", 50),
        volatility_class=risk_metrics.get("volatility_class", "Moderate")
    )
    
    # 6. SIP Forecasting using the AI's expected CAGR
    cagr_guess = forecast.get("expected_cagr_1yr_pct", 10.0) if forecast and "error" not in forecast else 10.0
    sip_projection = sip_calc.calculate_sip_future_value(
        monthly_sip=monthly_sip,
        years=sip_years,
        predicted_cagr_pct=cagr_guess
    )
    
    return {
        "status": "success",
        "symbol": symbol,
        "metadata": meta,
        "risk_intelligence": risk_metrics,
        "predictions": predictions,
        "forecast": forecast,
        "investor_match": match_result,
        "sip_projection": sip_projection
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


