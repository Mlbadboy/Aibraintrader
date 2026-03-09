"""
Trade Journal Database — Phase 29
Full target lifecycle: ACTIVE → COMPLETED / FAILED → archived history
  - profit_targets: per-symbol goals with status lifecycle
  - eod_reports:    daily end-of-day flash reports
"""

import sqlite3
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH      = "app/journal/journal.db"
FEEDBACK_DB  = "app/feedback/feedback.db"


# ─── Schema Init ──────────────────────────────────────────────────────────────

def _init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Profit targets — full lifecycle
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profit_targets (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol        TEXT NOT NULL,
            asset_type    TEXT DEFAULT 'stock',
            target_points REAL DEFAULT 0.0,
            target_amount REAL DEFAULT 0.0,
            target_pct    REAL DEFAULT 0.0,
            lot_size      INTEGER DEFAULT 1,
            notes         TEXT DEFAULT '',
            status        TEXT DEFAULT 'ACTIVE',   -- ACTIVE | COMPLETED | FAILED
            -- Link to the feedback.db prediction row that resolved this target
            resolved_trade_id   INTEGER DEFAULT NULL,
            resolved_outcome    TEXT DEFAULT NULL,  -- WIN or LOSS
            resolved_pnl        REAL DEFAULT NULL,
            resolved_at         TEXT DEFAULT NULL,
            created_at          TEXT,
            updated_at          TEXT,
            UNIQUE(symbol, status)   -- allow re-adding when previous is resolved
        )
    ''')

    # Migrate older table if it doesn't have status column
    try:
        cursor.execute("ALTER TABLE profit_targets ADD COLUMN status TEXT DEFAULT 'ACTIVE'")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE profit_targets ADD COLUMN resolved_trade_id INTEGER DEFAULT NULL")
        cursor.execute("ALTER TABLE profit_targets ADD COLUMN resolved_outcome TEXT DEFAULT NULL")
        cursor.execute("ALTER TABLE profit_targets ADD COLUMN resolved_pnl REAL DEFAULT NULL")
        cursor.execute("ALTER TABLE profit_targets ADD COLUMN resolved_at TEXT DEFAULT NULL")
    except Exception:
        pass

    # EOD Reports
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS eod_reports (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date     TEXT UNIQUE,
            total_signals   INTEGER DEFAULT 0,
            buy_signals     INTEGER DEFAULT 0,
            sell_signals    INTEGER DEFAULT 0,
            wins            INTEGER DEFAULT 0,
            losses          INTEGER DEFAULT 0,
            pending         INTEGER DEFAULT 0,
            win_rate        REAL DEFAULT 0.0,
            gross_profit    REAL DEFAULT 0.0,
            gross_loss      REAL DEFAULT 0.0,
            profit_factor   REAL DEFAULT 0.0,
            best_trade      TEXT DEFAULT '',
            worst_trade     TEXT DEFAULT '',
            target_hits     TEXT DEFAULT '[]',
            target_misses   TEXT DEFAULT '[]',
            generated_at    TEXT
        )
    ''')
    try:
        cursor.execute("ALTER TABLE eod_reports ADD COLUMN target_misses TEXT DEFAULT '[]'")
    except Exception:
        pass

    conn.commit()
    conn.close()
    logger.info("Journal DB (Phase 29) initialized.")


_init_db()


class JournalDB:

    # ─── PROFIT TARGETS — ACTIVE LIFECYCLE ────────────────────────────────────

    @staticmethod
    def set_target(symbol: str, asset_type: str = 'stock', target_points: float = 0,
                   target_amount: float = 0, target_pct: float = 0,
                   lot_size: int = 1, notes: str = '') -> dict:
        """
        Set a new ACTIVE profit target for a symbol.
        Replaces any existing ACTIVE target for the same symbol.
        """
        conn   = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now    = datetime.utcnow().isoformat()

        # Remove any existing ACTIVE target for this symbol so user can re-add
        cursor.execute(
            "DELETE FROM profit_targets WHERE symbol = ? AND status = 'ACTIVE'",
            (symbol.upper(),)
        )

        cursor.execute('''
            INSERT INTO profit_targets
                (symbol, asset_type, target_points, target_amount, target_pct,
                 lot_size, notes, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)
        ''', (symbol.upper(), asset_type, target_points, target_amount, target_pct,
              lot_size, notes, now, now))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return {"id": new_id, "symbol": symbol.upper(), "status": "ACTIVE"}

    @staticmethod
    def get_targets(status: str = 'ACTIVE') -> list:
        """Get targets filtered by status (ACTIVE, COMPLETED, FAILED, or ALL)."""
        conn   = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if status == 'ALL':
            cursor.execute('SELECT * FROM profit_targets ORDER BY created_at DESC')
        else:
            cursor.execute(
                'SELECT * FROM profit_targets WHERE status = ? ORDER BY created_at DESC',
                (status,)
            )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def delete_target(symbol: str, status: str = 'ACTIVE') -> bool:
        conn   = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM profit_targets WHERE symbol = ? AND status = ?',
            (symbol.upper(), status)
        )
        conn.commit()
        conn.close()
        return True

    # ─── TARGET RESOLUTION — called by feedback loop ───────────────────────────

    @staticmethod
    def resolve_targets_from_feedback() -> list:
        """
        Scans all ACTIVE targets and checks feedback.db for WIN/LOSS outcomes
        on the symbol. If found, marks the target as COMPLETED (WIN) or FAILED (LOSS)
        and removes it from the ACTIVE pool.

        Returns list of newly resolved targets for notification.
        """
        resolved = []
        try:
            # Get active targets
            active = JournalDB.get_targets('ACTIVE')
            if not active:
                return []

            # Query feedback.db for recent resolved predictions
            fconn   = sqlite3.connect(FEEDBACK_DB)
            fconn.row_factory = sqlite3.Row
            fcursor = fconn.cursor()

            jconn   = sqlite3.connect(DB_PATH)
            jcursor = jconn.cursor()
            now     = datetime.utcnow().isoformat()

            for tgt in active:
                symbol          = tgt['symbol']
                target_points   = tgt.get('target_points', 0) or 0
                target_pct      = tgt.get('target_pct', 0) or 0
                target_amount   = tgt.get('target_amount', 0) or 0
                lot_size        = tgt.get('lot_size', 1) or 1
                created_at      = tgt.get('created_at', '')

                # Find the most recent WIN or LOSS for this symbol after target was created
                fcursor.execute('''
                    SELECT id, symbol, decision, entry_price, take_profit, stop_loss,
                           actual_pnl, outcome, timestamp
                    FROM predictions
                    WHERE symbol = ? AND outcome IN ('WIN', 'LOSS')
                      AND timestamp > ?
                    ORDER BY timestamp DESC LIMIT 1
                ''', (symbol, created_at or ''))
                trade = fcursor.fetchone()
                if not trade:
                    continue
                trade = dict(trade)

                outcome      = trade['outcome']
                actual_pnl   = trade.get('actual_pnl', 0) or 0
                entry_price  = trade.get('entry_price', 0) or 0
                trade_id     = trade['id']

                # Evaluate whether the WIN met the trader's profit target
                if outcome == 'WIN':
                    move = abs(actual_pnl)
                    if target_points > 0:
                        met = move >= target_points
                    elif target_pct > 0 and entry_price:
                        met = (move / entry_price * 100) >= target_pct
                    elif target_amount > 0:
                        met = (move * lot_size) >= target_amount
                    else:
                        met = True  # No specific goal — any WIN counts

                    new_status = 'COMPLETED' if met else 'FAILED'
                else:
                    new_status = 'FAILED'
                    met = False

                # Resolve the target
                jcursor.execute('''
                    UPDATE profit_targets SET
                        status = ?,
                        resolved_trade_id = ?,
                        resolved_outcome = ?,
                        resolved_pnl = ?,
                        resolved_at = ?,
                        updated_at = ?
                    WHERE id = ?
                ''', (new_status, trade_id, outcome, round(actual_pnl, 4), now, now, tgt['id']))

                resolved.append({
                    'symbol':      symbol,
                    'status':      new_status,
                    'outcome':     outcome,
                    'actual_pnl':  round(actual_pnl, 4),
                    'met_target':  met,
                })
                logger.info(f"Target RESOLVED: {symbol} → {new_status} (trade {trade_id}, pnl={actual_pnl:.2f})")

            jconn.commit()
            jconn.close()
            fconn.close()

        except Exception as e:
            logger.error(f"resolve_targets_from_feedback error: {e}")

        return resolved

    # ─── ACTIVE TARGETS WITH LIVE SIGNALS ────────────────────────────────────

    @staticmethod
    def get_active_targets_with_signals(radar_signals: list = None) -> list:
        """
        Returns ACTIVE targets, each enriched with its latest radar signal prediction.
        radar_signals: the current list returned by /radar/signals (passed in to avoid DB calls).
        """
        active = JournalDB.get_targets('ACTIVE')
        if not active:
            return []

        # Build a quick lookup dict from signals list (keyed by symbol)
        sig_map = {}
        if radar_signals:
            for s in radar_signals:
                sym = (s.get('symbol') or '').upper()
                if sym and sym not in sig_map:
                    sig_map[sym] = s

        enriched = []
        for tgt in active:
            sym    = tgt['symbol'].upper()
            signal = sig_map.get(sym)  # may be None if no active signal
            enriched.append({
                **tgt,
                'live_signal': signal,   # full signal dict with entry/SL/TP/target_status etc.
            })

        return enriched

    # ─── TRADE HISTORY ────────────────────────────────────────────────────────

    @staticmethod
    def get_trades(date_from: str = None, date_to: str = None, symbol: str = None,
                   outcome: str = None, limit: int = 200) -> list:
        conn   = sqlite3.connect(FEEDBACK_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        conditions, params = [], []
        if date_from:
            conditions.append("timestamp >= ?"); params.append(date_from)
        if date_to:
            conditions.append("timestamp <= ?"); params.append(date_to + "T23:59:59")
        if symbol:
            conditions.append("symbol = ?"); params.append(symbol.upper())
        if outcome:
            conditions.append("outcome = ?"); params.append(outcome.upper())

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        cursor.execute(f'''
            SELECT id, timestamp, symbol, regime, strategy, decision,
                   confidence, entry_price, stop_loss, take_profit, outcome, actual_pnl
            FROM predictions {where}
            ORDER BY timestamp DESC LIMIT ?
        ''', params + [limit])

        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    # ─── EOD REPORT ───────────────────────────────────────────────────────────

    @staticmethod
    def generate_eod_report(report_date: str = None) -> dict:
        if not report_date:
            report_date = datetime.utcnow().strftime('%Y-%m-%d')

        date_start = report_date + "T00:00:00"
        date_end   = report_date + "T23:59:59"

        conn   = sqlite3.connect(FEEDBACK_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, symbol, decision, confidence, entry_price, stop_loss,
                   take_profit, outcome, actual_pnl, timestamp
            FROM predictions WHERE timestamp BETWEEN ? AND ?
        ''', (date_start, date_end))
        day_trades = [dict(r) for r in cursor.fetchall()]
        conn.close()

        total   = len(day_trades)
        buys    = sum(1 for t in day_trades if t['decision'] == 'BUY')
        sells   = sum(1 for t in day_trades if t['decision'] == 'SELL')
        wins    = sum(1 for t in day_trades if t['outcome'] == 'WIN')
        losses  = sum(1 for t in day_trades if t['outcome'] == 'LOSS')
        pending = sum(1 for t in day_trades if t['outcome'] == 'PENDING')

        gross_profit = sum(t['actual_pnl'] for t in day_trades
                          if t['outcome'] == 'WIN' and t['actual_pnl']) or 0
        gross_loss   = sum(abs(t['actual_pnl']) for t in day_trades
                          if t['outcome'] == 'LOSS' and t['actual_pnl']) or 0

        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0.0
        pf       = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (
                       10.0 if gross_profit > 0 else 0.0)

        resolved    = [t for t in day_trades if t['outcome'] in ('WIN', 'LOSS')]
        best_trade  = max(resolved, key=lambda x: x.get('actual_pnl', 0), default={}).get('symbol', '—')
        worst_trade = min(resolved, key=lambda x: x.get('actual_pnl', 0), default={}).get('symbol', '—')

        # Resolved targets today
        jconn   = sqlite3.connect(DB_PATH)
        jconn.row_factory = sqlite3.Row
        jcursor = jconn.cursor()
        jcursor.execute('''
            SELECT symbol, status, resolved_outcome, resolved_pnl
            FROM profit_targets WHERE resolved_at BETWEEN ? AND ?
        ''', (date_start, date_end))
        resolved_targets = [dict(r) for r in jcursor.fetchall()]
        jconn.close()

        target_hits   = [r for r in resolved_targets if r['status'] == 'COMPLETED']
        target_misses = [r for r in resolved_targets if r['status'] == 'FAILED']

        report = {
            "report_date":    report_date,
            "total_signals":  total,
            "buy_signals":    buys,
            "sell_signals":   sells,
            "wins":           wins,
            "losses":         losses,
            "pending":        pending,
            "win_rate":       round(win_rate, 1),
            "gross_profit":   round(gross_profit, 2),
            "gross_loss":     round(gross_loss, 2),
            "profit_factor":  pf,
            "best_trade":     best_trade,
            "worst_trade":    worst_trade,
            "target_hits":    target_hits,
            "target_misses":  target_misses,
            "trades":         day_trades,
            "generated_at":   datetime.utcnow().isoformat(),
        }

        # Persist
        jconn   = sqlite3.connect(DB_PATH)
        jcursor = jconn.cursor()
        jcursor.execute('''
            INSERT INTO eod_reports
                (report_date, total_signals, buy_signals, sell_signals, wins, losses,
                 pending, win_rate, gross_profit, gross_loss, profit_factor,
                 best_trade, worst_trade, target_hits, target_misses, generated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(report_date) DO UPDATE SET
                total_signals=excluded.total_signals, buy_signals=excluded.buy_signals,
                sell_signals=excluded.sell_signals, wins=excluded.wins, losses=excluded.losses,
                pending=excluded.pending, win_rate=excluded.win_rate,
                gross_profit=excluded.gross_profit, gross_loss=excluded.gross_loss,
                profit_factor=excluded.profit_factor, best_trade=excluded.best_trade,
                worst_trade=excluded.worst_trade, target_hits=excluded.target_hits,
                target_misses=excluded.target_misses, generated_at=excluded.generated_at
        ''', (
            report_date, total, buys, sells, wins, losses, pending,
            round(win_rate, 1), round(gross_profit, 2), round(gross_loss, 2), pf,
            best_trade, worst_trade,
            json.dumps(target_hits), json.dumps(target_misses),
            datetime.utcnow().isoformat()
        ))
        jconn.commit()
        jconn.close()

        return report

    @staticmethod
    def get_eod_reports(limit: int = 30) -> list:
        conn   = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM eod_reports ORDER BY report_date DESC LIMIT ?', (limit,))
        rows = []
        for r in cursor.fetchall():
            d = dict(r)
            d['target_hits']   = json.loads(d.get('target_hits')   or '[]')
            d['target_misses'] = json.loads(d.get('target_misses') or '[]')
            rows.append(d)
        conn.close()
        return rows

    # ─── MODEL RETRAINING TRIGGER ─────────────────────────────────────────────

    @staticmethod
    def export_training_data() -> list:
        """
        Exports all resolved (WIN/LOSS) predictions from feedback.db as
        labeled training rows for model retraining.
        Each row: symbol, features dict, label (1=WIN, 0=LOSS).
        """
        conn   = sqlite3.connect(FEEDBACK_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT symbol, regime, strategy, decision, confidence,
                   entry_price, stop_loss, take_profit, actual_pnl, outcome
            FROM predictions
            WHERE outcome IN ('WIN', 'LOSS')
            ORDER BY timestamp DESC LIMIT 5000
        ''')
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        training = []
        for r in rows:
            if not r['entry_price'] or not r['stop_loss'] or not r['take_profit']:
                continue
            try:
                risk_pts   = abs(r['entry_price'] - r['stop_loss'])
                reward_pts = abs(r['take_profit']  - r['entry_price'])
                rr_ratio   = round(reward_pts / risk_pts, 3) if risk_pts else 0
                training.append({
                    'symbol':    r['symbol'],
                    'decision':  r['decision'],
                    'confidence': r['confidence'] or 0,
                    'rr_ratio':  rr_ratio,
                    'regime':    r['regime'] or 'unknown',
                    'label':     1 if r['outcome'] == 'WIN' else 0,
                })
            except Exception:
                continue
        return training
