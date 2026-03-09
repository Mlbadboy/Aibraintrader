from apscheduler.schedulers.background import BackgroundScheduler
import logging
# from app.scrapers.nse_scraper import NSEScraper
# from app.radar.database import RadarDB
# from app.agents.classification_agent import ClassificationAgent

logger = logging.getLogger(__name__)

# Constants for Horizon Mapping
HORIZON_MAP = {
    "INTRADAY": {"interval": "5m", "period": "1d", "limit": 200},
    "SHORT": {"interval": "1h", "period": "1mo", "limit": 500},
    "LONG": {"interval": "1d", "period": "1y", "limit": 1000}
}

PIPELINE_FUNC = None
DATA_AGENT = None
# classifier = ClassificationAgent()
# nse_scraper = NSEScraper()

def radar_job():
    """
    Refactored Radar Job for Phase 21 & 26.
    Uses ThreadPoolExecutor to process assets in parallel to avoid sequential bottlenecks.
    Prioritizes newest assets by reversing the watchlist.
    """
    if PIPELINE_FUNC is None:
        return
        
    from app.radar.database import RadarDB
    from concurrent.futures import ThreadPoolExecutor
    
    watchlist = RadarDB.get_watchlist()
    if not watchlist:
        return
        
    # Reverse to prioritize newly injected assets
    processing_list = watchlist[::-1]
    
    def process_single_asset(asset):
        symbol = asset['symbol']
        asset_type = asset['asset_type']
        horizon_key = asset.get('target_horizon', 'SHORT').upper()
        
        # Use fallback if horizon key is invalid
        config = HORIZON_MAP.get(horizon_key, HORIZON_MAP["SHORT"])
        
        logger.info(f"Scanning {symbol} for {horizon_key} horizon...")
        
        try:
            # Run pipeline
            payload = PIPELINE_FUNC(
                symbol, 
                asset_type, 
                interval=config['interval'], 
                period=config.get('period', '1mo'),
                limit=config.get('limit', 500)
            )
            
            if payload and "error" not in payload:
                # Calculate Expected Return
                expected_return = payload.get('ml_predictions', {}).get('predicted_next_close', 0)
                if expected_return > 0:
                    current = payload.get('latest_indicators', {}).get('close', 1)
                    payload['expected_return'] = ((expected_return - current) / current) * 100
                else:
                    payload['expected_return'] = payload.get('confidence', 0) / 5.0
                
                # Store in Radar Database
                RadarDB.update_result(symbol, horizon_key, payload)
                logger.info(f"Autonomous Scan Success: {symbol} [{horizon_key}]")
            else:
                logger.error(f"Failed pipeline for {symbol}: {payload.get('error') if payload else 'No payload'}")
                 
        except Exception as e:
            logger.error(f"Radar Error on {symbol}: {e}")

    # Use a small pool to avoid API rate limits/CPU spikes
    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(process_single_asset, processing_list)

    logger.info("=== Autonomous Radar Scan Loop Complete ===")
    
    # Evaluate any pending trades in the background to keep accuracy stats live
    try:
        from app.feedback.loop import FeedbackLoop
        FeedbackLoop.evaluate_pending_trades()
    except Exception as e:
        logger.warning(f"Feedback evaluation skipped: {e}")

def fast_price_job():
    """High-frequency polling job to update prices without running the ML pipeline."""
    if DATA_AGENT is None:
        return
        
    try:
        from app.radar.database import RadarDB
        watchlist = RadarDB.get_watchlist()
        if not watchlist:
            return
            
        symbols = [item['symbol'] for item in watchlist]
        
        # Use rapid fetch for each symbol to bypass yfinance library level hangs
        live_prices = {}
        for sym in symbols:
            price = DATA_AGENT.fetch_rapid_price(sym)
            if price > 0:
                live_prices[sym] = price
        
        if live_prices:
            # Update DB instantly
            from app.radar.database import RadarDB
            for sym, price in live_prices.items():
                RadarDB.update_live_price(sym, price)
                
    except Exception as e:
        logger.error(f"Fast Price Job Error: {e}")

def refresh_watchlist_job():
    """
    Weekly NSE watchlist sync — downloads all instrument categories from NSE India.
    Runs every Sunday at 08:00 IST so the watchlist is ready before Monday market open.
    """
    try:
        from app.data.nse_importer import run_weekly_nse_sync
        summary = run_weekly_nse_sync(max_equities=500)
        logger.info(f"Weekly NSE Sync complete: {summary}")
    except Exception as e:
        logger.error(f"Error in weekly NSE sync: {e}")


class RadarScheduler:
    def __init__(self, pipeline_ref, data_agent_ref):
        global PIPELINE_FUNC, DATA_AGENT
        PIPELINE_FUNC = pipeline_ref
        DATA_AGENT = data_agent_ref

        self.scheduler = BackgroundScheduler()

        import datetime

        # ── Scan cycle — full ML pipeline every 5 minutes ──────────────────
        self.scheduler.add_job(
            radar_job, 'interval', minutes=5,
            next_run_time=datetime.datetime.now(),
            id='radar_scan', name='ML Radar Scan'
        )

        # ── Fast live price refresh every 10 seconds ────────────────────────
        self.scheduler.add_job(
            fast_price_job, 'interval', seconds=10,
            id='fast_price', name='Live Price Ticker'
        )

        # ── Weekly NSE full sync — every Sunday at 08:00 IST ────────────────
        # IST = UTC+5:30 → 08:00 IST = 02:30 UTC
        self.scheduler.add_job(
            refresh_watchlist_job,
            'cron',
            day_of_week='sun',   # Every Sunday
            hour=2,              # 08:00 IST = 02:30 UTC
            minute=30,
            timezone='UTC',
            id='weekly_nse_sync',
            name='Weekly NSE Instrument Sync'
        )

        # ── Mid-week refresh — every Wednesday at 08:00 IST ─────────────────
        # Catches any new IPOs or listings during the week
        self.scheduler.add_job(
            refresh_watchlist_job,
            'cron',
            day_of_week='wed',
            hour=2,
            minute=30,
            timezone='UTC',
            id='midweek_nse_sync',
            name='Mid-Week NSE Update'
        )

        logger.info("RadarScheduler configured:")
        logger.info("  ✅ ML Radar Scan     — every 5 minutes")
        logger.info("  ✅ Live Price Ticker — every 10 seconds")
        logger.info("  ✅ NSE Weekly Sync   — every Sunday  08:00 IST")
        logger.info("  ✅ NSE Mid-Week Sync — every Wednesday 08:00 IST")

    def start(self):
        self.scheduler.start()
        logger.info("Radar Scheduler Started — all jobs active.")

        # Run an immediate sync on first boot if watchlist is small
        try:
            from app.radar.database import RadarDB
            watchlist = RadarDB.get_watchlist()
            if len(watchlist) < 20:
                logger.info("Small watchlist detected — running immediate NSE sync on startup...")
                import threading
                t = threading.Thread(target=refresh_watchlist_job, daemon=True)
                t.start()
        except Exception as e:
            logger.warning(f"Could not check watchlist size on start: {e}")

    def stop(self):
        self.scheduler.shutdown()
