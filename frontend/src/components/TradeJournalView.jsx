import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import {
    BookOpen, TrendingUp, TrendingDown, Target, Clock, CheckCircle2,
    XCircle, AlertCircle, RefreshCw, Zap, BarChart2, Calendar, Plus,
    Trash2, Award, Activity, DollarSign, ArrowUpRight, ArrowDownRight,
    Flame, ShieldCheck, Eye, Brain, Cpu
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const fmt = (v, d = 2) => (v ?? 0).toFixed(d);
const fmtCur = (v) => {
    const n = Math.abs(v ?? 0);
    return `₹${n >= 1000 ? (n / 1000).toFixed(1) + 'K' : n.toFixed(2)}`;
};

// ─── Shared UI Components ─────────────────────────────────────────────────────

const StatCard = ({ icon: Icon, label, value, sub, color = 'indigo' }) => {
    const cls = {
        emerald: 'from-emerald-500/10 border-emerald-500/20 text-emerald-400',
        rose: 'from-rose-500/10    border-rose-500/20    text-rose-400',
        amber: 'from-amber-500/10   border-amber-500/20   text-amber-400',
        indigo: 'from-indigo-500/10  border-indigo-500/20  text-indigo-400',
        primary: 'from-primary/10     border-primary/20     text-primary',
    }[color];
    return (
        <div className={`bg-gradient-to-br ${cls} to-transparent border rounded-2xl p-4`}>
            <div className="flex items-center gap-2 mb-2">
                <Icon size={13} className="opacity-70" />
                <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{label}</span>
            </div>
            <div className="text-xl font-black text-white">{value}</div>
            {sub && <div className="text-[10px] text-slate-500 mt-1 font-medium">{sub}</div>}
        </div>
    );
};

const OutcomeBadge = ({ outcome }) => {
    if (outcome === 'WIN') return <span className="inline-flex items-center gap-1 text-[9px] font-black bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/30"><CheckCircle2 size={8} /> WIN</span>;
    if (outcome === 'LOSS') return <span className="inline-flex items-center gap-1 text-[9px] font-black bg-rose-500/20    text-rose-400    px-2 py-0.5 rounded-full border border-rose-500/30"><XCircle size={8} /> LOSS</span>;
    return <span className="inline-flex items-center gap-1 text-[9px] font-black bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full border border-amber-500/30"><Clock size={8} /> PENDING</span>;
};

const TargetStatusChip = ({ status }) => {
    if (status === 'COMPLETED') return <span className="text-[9px] font-black bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/30">✅ COMPLETED</span>;
    if (status === 'FAILED') return <span className="text-[9px] font-black bg-rose-500/20    text-rose-400    px-2 py-0.5 rounded-full border border-rose-500/30">❌ FAILED</span>;
    return <span className="text-[9px] font-black bg-primary/20 text-primary px-2 py-0.5 rounded-full border border-primary/30 animate-pulse">● TRACKING</span>;
};

// ─── Active Target Card (with live signal) ────────────────────────────────────

const SignalStaleBanner = ({ sig }) => {
    if (!sig) return null;
    const { signal_fresh, market_open, signal_age_hours } = sig;
    if (signal_fresh) return null;

    const ageLabel = signal_age_hours != null ? `${signal_age_hours}h ago` : 'unknown age';
    if (!market_open) {
        return (
            <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-800/60 border border-slate-700/50 mb-2">
                <span className="text-slate-500 text-base">🔒</span>
                <div>
                    <div className="text-[10px] font-black text-slate-400 uppercase tracking-wider">Market Closed — Last Session Data</div>
                    <div className="text-[9px] text-slate-600">Signal from {ageLabel} · Qualifier paused until market opens</div>
                </div>
            </div>
        );
    }
    return (
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-amber-950/30 border border-amber-700/30 mb-2">
            <span className="text-amber-600 text-base">⏱️</span>
            <div>
                <div className="text-[10px] font-black text-amber-600 uppercase tracking-wider">Stale Signal — {ageLabel}</div>
                <div className="text-[9px] text-amber-900">Signal is older than 4h · Awaiting next scan cycle</div>
            </div>
        </div>
    );
};

const ActiveTargetCard = ({ target, onDelete }) => {
    const sig = target.live_signal;
    const [flash, setFlash] = useState(false);

    useEffect(() => { setFlash(true); setTimeout(() => setFlash(false), 800); }, [target.status]);

    const goalLabel = target.target_points > 0 ? `${target.target_points} pts`
        : target.target_pct > 0 ? `${target.target_pct}%`
            : target.target_amount > 0 ? `₹${target.target_amount}` : 'Any move';

    return (
        <div className={`border rounded-2xl p-5 transition-all duration-500 ${flash ? 'scale-[1.01]' : ''} ${sig?.target_status === 'MEETS_TARGET'
            ? 'bg-emerald-950/30 border-emerald-500/30'
            : sig?.target_status === 'BELOW_TARGET'
                ? 'bg-amber-950/20 border-amber-500/20'
                : 'bg-slate-900/40 border-slate-800'}`}
        >
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
                <div>
                    <div className="flex items-center gap-2">
                        <span className="text-base font-black text-white">{target.symbol}</span>
                        <span className="text-[9px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-bold uppercase">{target.asset_type}</span>
                        <TargetStatusChip status={target.status} />
                    </div>
                    <div className="text-[10px] text-slate-500 mt-0.5 font-bold">
                        Goal: <span className="text-primary">{goalLabel}</span>
                        {target.lot_size > 1 && <span className="ml-2 text-slate-600">× {target.lot_size} lots</span>}
                    </div>
                </div>
                <button onClick={() => onDelete(target.symbol)}
                    className="text-slate-700 hover:text-rose-400 transition-all p-1 opacity-60 hover:opacity-100">
                    <Trash2 size={13} />
                </button>
            </div>

            {/* Live Signal Panel */}
            {sig ? (
                <div className="space-y-2">
                    {/* Direction + Confidence */}
                    <div className="flex items-center gap-2 mb-1">
                        <span className={`text-[9px] font-black px-2 py-1 rounded ${sig.decision === 'BUY' ? 'bg-emerald-500 text-black' : 'bg-rose-500 text-white'}`}>
                            {sig.decision}
                        </span>
                        <div className="flex-1 bg-slate-800 rounded-full h-1.5">
                            <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${(sig.confidence * 100).toFixed(0)}%` }} />
                        </div>
                        <span className="text-xs font-black text-white">{(sig.confidence * 100).toFixed(0)}%</span>
                        {sig.signal_strength === 'STRONG' && <span className="text-[8px] font-black text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">STRONG</span>}
                    </div>

                    {/* Market Closed / Stale Banner */}
                    <SignalStaleBanner sig={sig} />

                    {/* Price Levels — dimmed when market is closed */}
                    <div className={`grid grid-cols-3 gap-1.5 text-[9px] ${!sig.signal_fresh ? 'opacity-50' : ''}`}>
                        <div className="bg-slate-900/60 rounded-xl p-2.5 text-center">
                            <div className="text-slate-500 font-bold mb-0.5">ENTRY</div>
                            <div className="text-white font-black">{fmt(sig.entry_price)}</div>
                        </div>
                        <div className="bg-rose-950/40 rounded-xl p-2.5 text-center">
                            <div className="text-rose-500 font-bold mb-0.5">STOP LOSS</div>
                            <div className="text-rose-300 font-black">{fmt(sig.stop_loss)}</div>
                        </div>
                        <div className="bg-emerald-950/40 rounded-xl p-2.5 text-center">
                            <div className="text-emerald-500 font-bold mb-0.5">TARGET TP</div>
                            <div className="text-emerald-300 font-black">{fmt(sig.take_profit)}</div>
                        </div>
                    </div>

                    {/* Target Qualifier — only shown when market is open and signal is fresh */}
                    {sig.target_status === 'STALE' ? null : sig.target_status === 'MEETS_TARGET' ? (
                        <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-emerald-950/60 border border-emerald-500/40">
                            <span className="text-base">✅</span>
                            <div>
                                <div className="text-[10px] font-black text-emerald-400 uppercase tracking-wider">Meets Your {sig.target_label} Target</div>
                                <div className="text-[9px] text-emerald-700">Predicted move: {fmt(sig.predicted_move)} · +{fmt(sig.target_gap)} ahead</div>
                            </div>
                        </div>
                    ) : (
                        <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-amber-950/40 border border-amber-500/20">
                            <span className="text-base">⚠️</span>
                            <div>
                                <div className="text-[10px] font-black text-amber-400 uppercase tracking-wider">Short of {sig.target_label} Target</div>
                                <div className="text-[9px] text-amber-800">Predicted: {fmt(sig.predicted_move)} · {fmt(sig.target_gap)} short — watch for stronger signal</div>
                            </div>
                        </div>
                    )}

                    {/* Reason Tags */}
                    {sig.reason_tags?.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                            {sig.reason_tags.slice(0, 3).map((tag, i) => (
                                <span key={i} className="text-[8px] bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-1.5 py-0.5 rounded-full font-bold">{tag}</span>
                            ))}
                        </div>
                    )}
                </div>
            ) : (
                <div className="flex items-center gap-2 py-3 text-slate-600">
                    <Eye size={14} />
                    <span className="text-[10px] font-bold">No active signal yet — watching {target.symbol}</span>
                </div>
            )}

            {target.notes && <p className="text-[9px] text-slate-700 mt-2 italic">"{target.notes}"</p>}
        </div>
    );
};

// ─── Resolved Target History Card ─────────────────────────────────────────────

const ResolvedCard = ({ target }) => (
    <div className={`border rounded-xl p-3 ${target.status === 'COMPLETED'
        ? 'bg-emerald-950/20 border-emerald-800/30' : 'bg-rose-950/20 border-rose-800/30'}`}>
        <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
                <span className="font-black text-white text-sm">{target.symbol}</span>
                <TargetStatusChip status={target.status} />
            </div>
            <div className={`text-sm font-black ${target.resolved_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {target.resolved_pnl >= 0 ? '+' : ''}{fmt(target.resolved_pnl)}
            </div>
        </div>
        <div className="text-[9px] text-slate-600 mt-1">
            Resolved {target.resolved_at?.slice(0, 16).replace('T', ' ')} · {target.resolved_outcome}
        </div>
    </div>
);

// ─── Main Component ───────────────────────────────────────────────────────────

const TradeJournalView = () => {
    const [activeTab, setActiveTab] = useState('targets'); // targets | journal | eod
    const [activeTargets, setActiveTargets] = useState([]);
    const [resolvedTargets, setResolvedTargets] = useState([]);
    const [trades, setTrades] = useState([]);
    const [eodReport, setEodReport] = useState(null);
    const [eodHistory, setEodHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState(null);
    const [pollCount, setPollCount] = useState(0);
    const [marketStatus, setMarketStatus] = useState(null);
    const [filterOutcome, setFilterOutcome] = useState('ALL');
    const [filterDate, setFilterDate] = useState('');
    const [retrainStatus, setRetrainStatus] = useState(null);
    const timerRef = useRef(null);

    // Profit target form
    const [tForm, setTForm] = useState({ symbol: '', asset_type: 'stock', target_points: '', target_amount: '', target_pct: '', lot_size: 1, notes: '' });
    const [tStatus, setTStatus] = useState({ loading: false, error: null, success: false });

    const fetchAll = useCallback(async () => {
        try {
            const params = {};
            if (filterOutcome !== 'ALL') params.outcome = filterOutcome;
            if (filterDate) params.date_from = params.date_to = filterDate;

            const [atRes, cmpRes, failRes, tradeRes, eodRes, histRes] = await Promise.allSettled([
                axios.get(`${API_BASE_URL}/journal/active-targets`),
                axios.get(`${API_BASE_URL}/journal/targets?status=COMPLETED`),
                axios.get(`${API_BASE_URL}/journal/targets?status=FAILED`),
                axios.get(`${API_BASE_URL}/journal/trades`, { params: { ...params, limit: 200 } }),
                axios.get(`${API_BASE_URL}/journal/eod-report`),
                axios.get(`${API_BASE_URL}/journal/eod-history`),
            ]);

            if (atRes.status === 'fulfilled') {
                setActiveTargets(atRes.value.data?.data || []);
                if (atRes.value.data?.market_status) setMarketStatus(atRes.value.data.market_status);
            }
            const completed = cmpRes.status === 'fulfilled' ? cmpRes.value.data?.data || [] : [];
            const failed = failRes.status === 'fulfilled' ? failRes.value.data?.data || [] : [];
            setResolvedTargets([...completed, ...failed].sort((a, b) =>
                (b.resolved_at || '').localeCompare(a.resolved_at || '')
            ));
            if (tradeRes.status === 'fulfilled') setTrades(tradeRes.value.data?.data || []);
            if (eodRes.status === 'fulfilled') setEodReport(eodRes.value.data?.data);
            if (histRes.status === 'fulfilled') setEodHistory(histRes.value.data?.data || []);
            setLastUpdate(new Date());
            setPollCount(c => c + 1);
        } catch (e) {
            console.error('Journal fetch error:', e);
        } finally {
            setLoading(false);
        }
    }, [filterOutcome, filterDate]);

    // 30s realtime polling
    useEffect(() => {
        fetchAll();
        timerRef.current = setInterval(fetchAll, 30000);
        return () => clearInterval(timerRef.current);
    }, [fetchAll]);

    const handleSetTarget = async (e) => {
        e.preventDefault();
        setTStatus({ loading: true, error: null, success: false });
        try {
            await axios.post(`${API_BASE_URL}/journal/targets/${tForm.symbol.toUpperCase()}`, {
                asset_type: tForm.asset_type,
                target_points: parseFloat(tForm.target_points) || 0,
                target_amount: parseFloat(tForm.target_amount) || 0,
                target_pct: parseFloat(tForm.target_pct) || 0,
                lot_size: parseInt(tForm.lot_size) || 1,
                notes: tForm.notes,
            });
            setTForm({ symbol: '', asset_type: 'stock', target_points: '', target_amount: '', target_pct: '', lot_size: 1, notes: '' });
            setTStatus({ loading: false, error: null, success: true });
            await fetchAll();
            setTimeout(() => setTStatus(s => ({ ...s, success: false })), 3000);
        } catch (err) {
            setTStatus({ loading: false, error: err.response?.data?.detail || err.message, success: false });
        }
    };

    const handleDeleteTarget = async (symbol) => {
        await axios.delete(`${API_BASE_URL}/journal/targets/${symbol}`);
        fetchAll();
    };

    const handleRetrain = async () => {
        setRetrainStatus('queued');
        try {
            await axios.post(`${API_BASE_URL}/journal/retrain`);
            setRetrainStatus('running');
            setTimeout(() => setRetrainStatus(null), 8000);
        } catch { setRetrainStatus('error'); }
    };

    // Today summary
    const todayStr = new Date().toISOString().slice(0, 10);
    const todayTrades = trades.filter(t => t.timestamp?.startsWith(todayStr));
    const todayWins = todayTrades.filter(t => t.outcome === 'WIN').length;
    const todayLosses = todayTrades.filter(t => t.outcome === 'LOSS').length;
    const todayPnL = todayTrades.reduce((a, t) => a + (t.actual_pnl || 0), 0);

    const tabs = [
        { id: 'targets', label: 'Active Targets', icon: Target, badge: activeTargets.length },
        { id: 'journal', label: 'Trade Journal', icon: BookOpen, badge: null },
        { id: 'eod', label: 'EOD Report', icon: Calendar, badge: null },
    ];

    return (
        <div className="p-6 space-y-5 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-black text-white flex items-center gap-3">
                        <div className="p-2 bg-primary/10 rounded-xl"><BookOpen size={22} className="text-primary" /></div>
                        Trade Journal
                    </h1>
                    <p className="text-xs text-slate-500 mt-1 ml-12 flex items-center gap-2">
                        Realtime · Auto-resolves targets · EOD report daily
                        {lastUpdate && <span className="text-slate-700 font-mono">· Updated {lastUpdate.toLocaleTimeString()}</span>}
                        <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse inline-block" />
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={handleRetrain}
                        className={`flex items-center gap-1.5 px-3 py-2 text-[10px] font-black rounded-xl border transition-all ${retrainStatus === 'running' ? 'bg-indigo-500/20 border-indigo-500/40 text-indigo-400' : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-white'}`}>
                        <Brain size={11} className={retrainStatus === 'running' ? 'animate-spin' : ''} />
                        {retrainStatus === 'running' ? 'Training...' : 'Retrain Model'}
                    </button>
                    <button onClick={fetchAll}
                        className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-black rounded-xl transition-all border border-slate-700">
                        <RefreshCw size={11} className={loading ? 'animate-spin' : ''} /> Refresh
                    </button>
                </div>
            </div>

            {/* Today Stats Bar */}
            <div className="grid grid-cols-4 gap-3">
                <StatCard icon={Activity} label="Today's Signals" value={todayTrades.length} sub="▲ Predicted by AI" color="indigo" />
                <StatCard icon={CheckCircle2} label="Wins Today" value={todayWins} sub={`${todayWins + todayLosses > 0 ? ((todayWins / (todayWins + todayLosses)) * 100).toFixed(0) : 0}% win rate`} color="emerald" />
                <StatCard icon={XCircle} label="Losses Today" value={todayLosses} sub="Stopped out" color="rose" />
                <StatCard icon={DollarSign} label="Today's P&L" value={todayPnL >= 0 ? `+${fmtCur(todayPnL)}` : `-${fmtCur(Math.abs(todayPnL))}`} sub="Actual realized" color={todayPnL >= 0 ? 'emerald' : 'rose'} />
            </div>

            {/* Tabs */}
            <div className="flex gap-2 bg-slate-900/50 p-1 rounded-2xl border border-slate-800 w-fit">
                {tabs.map(({ id, label, icon: Icon, badge }) => (
                    <button key={id} onClick={() => setActiveTab(id)}
                        className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-black tracking-wider transition-all relative ${activeTab === id ? 'bg-primary text-black shadow-lg shadow-primary/20' : 'text-slate-400 hover:text-white'}`}>
                        <Icon size={12} /> {label}
                        {badge > 0 && <span className={`text-[8px] font-black rounded-full w-4 h-4 flex items-center justify-center ${activeTab === id ? 'bg-black/30 text-black' : 'bg-primary text-black'}`}>{badge}</span>}
                    </button>
                ))}
            </div>

            {/* ── ACTIVE TARGETS TAB ──────────────────────────────────────────────── */}
            {activeTab === 'targets' && (
                <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                    {/* Add Target Form */}
                    <div className="lg:col-span-2 bg-slate-900/40 border border-slate-800 rounded-3xl p-6 h-fit">
                        <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-5 flex items-center gap-2">
                            <Plus size={13} className="text-primary" /> Set New Target
                        </h3>
                        <form onSubmit={handleSetTarget} className="space-y-3">
                            <div>
                                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-1">Symbol</label>
                                <input required value={tForm.symbol}
                                    onChange={e => setTForm(f => ({ ...f, symbol: e.target.value.toUpperCase() }))}
                                    placeholder="e.g. NIFTY, BANKNIFTY, AAPL, BTCUSDT"
                                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-white font-bold outline-none focus:border-primary transition-all" />
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                                <div>
                                    <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-1">Type</label>
                                    <select value={tForm.asset_type} onChange={e => setTForm(f => ({ ...f, asset_type: e.target.value }))}
                                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-300 font-bold outline-none focus:border-primary">
                                        <option value="stock">Stock/Index</option>
                                        <option value="crypto">Crypto</option>
                                        <option value="commodity">Commodity</option>
                                        <option value="fo">F&amp;O</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-1">Lot Size</label>
                                    <input type="number" min={1} value={tForm.lot_size} onChange={e => setTForm(f => ({ ...f, lot_size: e.target.value }))}
                                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-white font-bold outline-none focus:border-primary" />
                                </div>
                            </div>
                            <div className="bg-slate-950/60 rounded-2xl p-4 border border-slate-800/50 space-y-2">
                                <p className="text-[9px] font-black text-slate-600 uppercase tracking-widest">Set ONE target type:</p>
                                {[
                                    ['target_points', 'Points Target (index/F&O)', 'e.g. 50 pts for NIFTY'],
                                    ['target_amount', 'Amount Target (₹)', 'e.g. 5000 profit'],
                                    ['target_pct', '% Return Target', 'e.g. 2% return'],
                                ].map(([field, label, ph]) => (
                                    <div key={field}>
                                        <label className="text-[10px] text-slate-500 font-bold block mb-1">{label}</label>
                                        <input type="number" placeholder={ph} value={tForm[field]}
                                            onChange={e => setTForm(f => ({ ...f, [field]: e.target.value }))}
                                            className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white font-bold outline-none focus:border-primary" />
                                    </div>
                                ))}
                            </div>
                            <div>
                                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-1">Notes (optional)</label>
                                <input placeholder="e.g. BTST trade, weekly expiry" value={tForm.notes}
                                    onChange={e => setTForm(f => ({ ...f, notes: e.target.value }))}
                                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-white outline-none focus:border-primary" />
                            </div>
                            <button type="submit" disabled={tStatus.loading || !tForm.symbol}
                                className="w-full bg-primary hover:brightness-110 text-black font-black text-xs py-3 rounded-xl disabled:opacity-50 transition-all shadow-lg shadow-primary/20">
                                {tStatus.loading ? 'Activating...' : '+ Activate Target & Watch'}
                            </button>
                            {tStatus.success && <p className="text-emerald-400 text-[9px] font-bold text-center">✅ Target active — model now tracking {tForm.symbol || 'signal'}</p>}
                            {tStatus.error && <p className="text-rose-400 text-[9px] font-bold text-center">{tStatus.error}</p>}
                        </form>

                        {/* Resolved History */}
                        {resolvedTargets.length > 0 && (
                            <div className="mt-6">
                                <h4 className="text-[9px] font-black text-slate-600 uppercase tracking-widest mb-3 flex items-center gap-1">
                                    <Award size={10} /> Resolved History ({resolvedTargets.length})
                                </h4>
                                <div className="space-y-2 max-h-56 overflow-y-auto no-scrollbar">
                                    {resolvedTargets.map((t, i) => <ResolvedCard key={i} target={t} />)}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Active Targets List */}
                    <div className="lg:col-span-3 space-y-4">
                        <div className="flex items-center justify-between">
                            <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                <ShieldCheck size={12} className="text-primary" />
                                Active — Watching {activeTargets.length} Symbol{activeTargets.length !== 1 ? 's' : ''}
                            </h3>
                            <div className="text-[9px] text-slate-700 flex items-center gap-1">
                                <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse" />
                                Auto-updates every 30s
                            </div>
                        </div>

                        {activeTargets.length === 0 ? (
                            <div className="text-center py-20 bg-slate-900/30 rounded-3xl border border-slate-800 border-dashed">
                                <Target size={40} className="text-slate-700 mx-auto mb-3" />
                                <p className="text-slate-600 font-bold text-sm">No Active Targets</p>
                                <p className="text-slate-700 text-xs mt-1 max-w-xs mx-auto">
                                    Add a profit target above. Once added, the model will show live signals
                                    and automatically mark the target as Complete (WIN hits TP) or Failed (LOSS hits SL).
                                </p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {activeTargets.map((tgt, i) => (
                                    <ActiveTargetCard key={`${tgt.symbol}-${i}`} target={tgt} onDelete={handleDeleteTarget} />
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* ── TRADE JOURNAL TAB ───────────────────────────────────────────────── */}
            {activeTab === 'journal' && (
                <div className="space-y-4">
                    <div className="flex flex-wrap gap-3 items-center">
                        <div className="flex gap-1 bg-slate-900/50 p-1 rounded-xl border border-slate-800">
                            {['ALL', 'WIN', 'LOSS', 'PENDING'].map(o => (
                                <button key={o} onClick={() => setFilterOutcome(o)}
                                    className={`px-3 py-1.5 rounded-lg text-[10px] font-black transition-all ${filterOutcome === o ? 'bg-primary text-black' : 'text-slate-400 hover:text-white'}`}>
                                    {o}
                                </button>
                            ))}
                        </div>
                        <input type="date" value={filterDate} onChange={e => setFilterDate(e.target.value)}
                            className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white outline-none focus:border-primary" />
                        {filterDate && <button onClick={() => setFilterDate('')} className="text-xs text-rose-400">✕ Clear</button>}
                        <span className="ml-auto text-[10px] text-slate-600 font-bold">{trades.length} records</span>
                    </div>
                    <div className="bg-slate-900/40 border border-slate-800 rounded-3xl overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left">
                                <thead className="bg-slate-950/30 border-b border-slate-800">
                                    <tr className="text-[9px] font-black text-slate-500 uppercase tracking-widest">
                                        {['Symbol', 'Decision', 'Conf', 'Entry', 'Stop Loss', 'Target', 'Outcome', 'P&L', 'Time'].map(h => (
                                            <th key={h} className="px-4 py-3">{h}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800/40">
                                    {trades.length === 0 ? (
                                        <tr><td colSpan={9} className="text-center py-16 text-slate-600 text-sm font-bold">No trade records found</td></tr>
                                    ) : trades.map(t => (
                                        <tr key={t.id} className="hover:bg-slate-800/20 transition-colors">
                                            <td className="px-4 py-3 text-sm font-black text-white">{t.symbol}</td>
                                            <td className="px-4 py-3">
                                                <span className={`text-[9px] font-black px-2 py-0.5 rounded ${t.decision === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>{t.decision}</span>
                                            </td>
                                            <td className="px-4 py-3 text-xs font-bold text-white">{((t.confidence || 0) * 100).toFixed(0)}%</td>
                                            <td className="px-4 py-3 text-xs font-mono text-slate-300">{fmt(t.entry_price)}</td>
                                            <td className="px-4 py-3 text-xs font-mono text-rose-400">{fmt(t.stop_loss)}</td>
                                            <td className="px-4 py-3 text-xs font-mono text-emerald-400">{fmt(t.take_profit)}</td>
                                            <td className="px-4 py-3"><OutcomeBadge outcome={t.outcome} /></td>
                                            <td className="px-4 py-3 text-xs font-black">
                                                <span className={t.actual_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                                                    {t.actual_pnl >= 0 ? '+' : ''}{fmt(t.actual_pnl)}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 text-[10px] text-slate-500 font-mono">{t.timestamp?.slice(0, 16).replace('T', ' ')}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}

            {/* ── EOD REPORT TAB ───────────────────────────────────────────────────── */}
            {activeTab === 'eod' && (
                <div className="space-y-5">
                    {eodReport ? (
                        <>
                            {/* Flash Banner */}
                            <div className="bg-gradient-to-r from-indigo-500/10 via-primary/5 to-transparent border border-indigo-500/20 rounded-3xl p-6 relative overflow-hidden">
                                <div className="absolute right-6 top-4 opacity-10"><Flame size={80} className="text-primary" /></div>
                                <div className="flex items-center gap-3 mb-4">
                                    <Zap size={16} className="text-primary" />
                                    <h2 className="text-sm font-black text-white uppercase tracking-widest">EOD Flash Report</h2>
                                    <span className="text-[10px] bg-primary/20 text-primary px-2 py-0.5 rounded font-bold border border-primary/30">{eodReport.report_date}</span>
                                    <span className="ml-auto text-[9px] text-slate-600 font-mono">Generated {eodReport.generated_at?.slice(11, 16)} UTC</span>
                                </div>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <StatCard icon={Activity} label="Total Signals" value={eodReport.total_signals} sub={`${eodReport.buy_signals} BUY · ${eodReport.sell_signals} SELL`} color="indigo" />
                                    <StatCard icon={CheckCircle2} label="Successful" value={eodReport.wins} sub={`${fmt(eodReport.win_rate, 1)}% win rate`} color="emerald" />
                                    <StatCard icon={XCircle} label="Failed" value={eodReport.losses} sub={`${eodReport.pending} still pending`} color="rose" />
                                    <StatCard icon={BarChart2} label="Profit Factor" value={`${fmt(eodReport.profit_factor)}x`} sub={`Gross +${fmtCur(eodReport.gross_profit)}`} color="primary" />
                                </div>
                            </div>

                            {/* Target results */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div className="bg-emerald-950/40 border border-emerald-500/20 rounded-2xl p-4">
                                    <div className="text-[9px] font-black text-emerald-500 uppercase tracking-widest mb-2 flex items-center gap-1"><Award size={10} /> Best Trade</div>
                                    <div className="text-2xl font-black text-white">{eodReport.best_trade || '—'}</div>
                                </div>
                                <div className="bg-rose-950/40 border border-rose-500/20 rounded-2xl p-4">
                                    <div className="text-[9px] font-black text-rose-500 uppercase tracking-widest mb-2 flex items-center gap-1"><TrendingDown size={10} /> Worst Trade</div>
                                    <div className="text-2xl font-black text-white">{eodReport.worst_trade || '—'}</div>
                                </div>
                                <div className="bg-primary/5 border border-primary/20 rounded-2xl p-4">
                                    <div className="text-[9px] font-black text-primary uppercase tracking-widest mb-2 flex items-center gap-1"><Target size={10} /> Target Results Today</div>
                                    {(eodReport.target_hits?.length > 0 || eodReport.target_misses?.length > 0) ? (
                                        <div className="space-y-1">
                                            {(eodReport.target_hits || []).map((h, i) => (
                                                <div key={i} className="text-xs text-emerald-400 font-black">✅ {h.symbol}</div>
                                            ))}
                                            {(eodReport.target_misses || []).map((h, i) => (
                                                <div key={i} className="text-xs text-rose-400 font-black">❌ {h.symbol}</div>
                                            ))}
                                        </div>
                                    ) : <div className="text-sm font-black text-slate-600">No targets resolved today</div>}
                                </div>
                            </div>

                            {/* Trade list */}
                            <div className="bg-slate-900/40 border border-slate-800 rounded-3xl overflow-hidden">
                                <div className="px-6 py-4 border-b border-slate-800">
                                    <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest">Today's Full Trade Log ({eodReport.trades?.length || 0})</h3>
                                </div>
                                <div className="max-h-64 overflow-y-auto">
                                    <table className="w-full text-left">
                                        <thead className="bg-slate-950/40 sticky top-0">
                                            <tr className="text-[9px] font-black text-slate-600 uppercase tracking-widest border-b border-slate-800">
                                                {['Symbol', 'Dir', 'Conf', 'Entry', 'Outcome', 'P&L'].map(h => (
                                                    <th key={h} className="px-5 py-3">{h}</th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-800/40">
                                            {(eodReport.trades || []).map(t => (
                                                <tr key={t.id} className="hover:bg-slate-800/20">
                                                    <td className="px-5 py-2.5 text-sm font-black text-white">{t.symbol}</td>
                                                    <td className="px-4 py-2.5"><span className={`text-[9px] font-black px-2 py-0.5 rounded ${t.decision === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>{t.decision}</span></td>
                                                    <td className="px-4 py-2.5 text-xs text-slate-400 font-bold">{((t.confidence || 0) * 100).toFixed(0)}%</td>
                                                    <td className="px-4 py-2.5 text-xs font-mono text-slate-300">{fmt(t.entry_price)}</td>
                                                    <td className="px-4 py-2.5"><OutcomeBadge outcome={t.outcome} /></td>
                                                    <td className="px-4 py-2.5 text-xs font-black">
                                                        <span className={t.actual_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}>{t.actual_pnl >= 0 ? '+' : ''}{fmt(t.actual_pnl)}</span>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            {/* History */}
                            {eodHistory.length > 1 && (
                                <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-6">
                                    <h3 className="text-xs font-black text-slate-500 uppercase tracking-widest mb-4 flex items-center gap-2"><BarChart2 size={12} className="text-primary" /> {eodHistory.length}-Day Report History</h3>
                                    <div className="space-y-2">
                                        {eodHistory.map(r => (
                                            <div key={r.report_date} className="flex items-center justify-between py-2 border-b border-slate-800/40 last:border-0">
                                                <span className="text-xs font-bold text-slate-400 font-mono">{r.report_date}</span>
                                                <div className="flex items-center gap-4 text-[10px]">
                                                    <span className="text-emerald-400 font-black">{r.wins}W</span>
                                                    <span className="text-rose-400 font-black">{r.losses}L</span>
                                                    <span className={`font-black ${r.gross_profit - r.gross_loss >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                                        {r.gross_profit - r.gross_loss >= 0 ? '+' : ''}{fmtCur(r.gross_profit - r.gross_loss)}
                                                    </span>
                                                    <span className="text-indigo-400 font-bold">{fmt(r.profit_factor)}x PF</span>
                                                    <div className="flex gap-1">
                                                        {(r.target_hits || []).map((h, i) => <span key={i} className="text-emerald-600">✅{h.symbol}</span>)}
                                                        {(r.target_misses || []).map((h, i) => <span key={i} className="text-rose-700">❌{h.symbol}</span>)}
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="text-center py-24">
                            <Calendar size={40} className="text-slate-700 mx-auto mb-4" />
                            <p className="text-slate-500 font-bold">Generating EOD Report...</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default TradeJournalView;
