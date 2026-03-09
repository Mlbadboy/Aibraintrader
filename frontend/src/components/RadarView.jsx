import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Radar, RefreshCw, ShieldAlert, Zap, TrendingUp, Filter, Bell, Rocket, Clock, Globe, Plus, ChevronDown, ChevronUp, BookOpen, BarChart2, Activity } from 'lucide-react';
import { formatCurrency } from '../utils/formatters';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

const RadarView = () => {
    const [data, setData] = useState([]);
    const [signals, setSignals] = useState([]);
    const [accuracy, setAccuracy] = useState(null);
    const [toast, setToast] = useState(null); // { symbol, decision, confidence }
    const [loading, setLoading] = useState(true);
    const [activeHorizon, setActiveHorizon] = useState('ALL');
    const [activeCategory, setActiveCategory] = useState('ALL');
    const [expandedRows, setExpandedRows] = useState(new Set());
    const [flashes, setFlashes] = useState({}); // { 'AAPL-SHORT': 'up' | 'down' }
    const previousDataRef = React.useRef(null);
    const shownSignalsRef = React.useRef(new Set());

    // Custom Asset State
    const [addSymbol, setAddSymbol] = useState('');
    const [addType, setAddType] = useState('stock');
    const [addHorizon, setAddHorizon] = useState('SHORT');
    const [addStatus, setAddStatus] = useState({ loading: false, error: null, success: false });

    const toggleRow = (id) => {
        const next = new Set(expandedRows);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        setExpandedRows(next);
    };

    const handleAddAsset = async (e) => {
        e.preventDefault();
        setAddStatus({ loading: true, error: null, success: false });
        try {
            await axios.post(`${API_BASE_URL}/radar/watchlist/${addSymbol.toUpperCase()}`, {
                asset_type: addType,
                horizon: addHorizon
            });
            setAddStatus({ loading: false, error: null, success: true });
            setAddSymbol('');
            fetchRadar(); // Refresh immediately
            setTimeout(() => setAddStatus(s => ({ ...s, success: false })), 3000);
        } catch (err) {
            setAddStatus({ loading: false, error: err.response?.data?.detail || err.message, success: false });
        }
    };

    const fetchRadar = async () => {
        try {
            setLoading(true);
            const horizonParam = activeHorizon === 'ALL' ? '' : `?horizon=${activeHorizon}`;

            // Fetch live radar table
            try {
                const radarRes = await axios.get(`${API_BASE_URL}/radar/live${horizonParam}`);
                if (radarRes.data?.data) setData(radarRes.data.data);
            } catch (err) {
                console.error('Failed to fetch radar table data:', err);
            }

            // Fetch high-confidence signals (BUY/SELL with SL/TP)
            try {
                const signalsRes = await axios.get(`${API_BASE_URL}/radar/signals`);
                if (signalsRes.data?.data) {
                    const newSignals = signalsRes.data.data;
                    setSignals(newSignals);

                    // Fire notifications for newly seen high-confidence signals
                    newSignals.forEach(s => {
                        const key = `${s.symbol}-${s.decision}-${s.horizon}`;
                        if (!shownSignalsRef.current.has(key) && (s.confidence || 0) >= 0.7) {
                            shownSignalsRef.current.add(key);
                            // Browser notification
                            if ('Notification' in window && Notification.permission === 'granted') {
                                new Notification(`🚨 ${s.signal_strength} ${s.decision} Signal: ${s.symbol}`, {
                                    body: `Entry: ${s.entry_price?.toFixed(2)} | SL: ${s.stop_loss?.toFixed(2)} | Target: ${s.take_profit?.toFixed(2)} | Conf: ${((s.confidence || 0) * 100).toFixed(0)}%`,
                                    icon: '/favicon.ico'
                                });
                            }
                            // In-app toast
                            setToast({ symbol: s.symbol, decision: s.decision, confidence: s.confidence, entry: s.entry_price, sl: s.stop_loss, tp: s.take_profit });
                            setTimeout(() => setToast(null), 8000);
                        }
                    });
                }
            } catch (err) {
                console.error('Failed to fetch signals:', err);
            }

            // Fetch real accuracy stats
            try {
                const accRes = await axios.get(`${API_BASE_URL}/radar/accuracy`);
                if (accRes.data?.status === 'success') setAccuracy(accRes.data);
            } catch (err) {
                console.error('Failed to fetch accuracy:', err);
            }

        } catch (err) {
            console.error('Radar Fetch Error:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
        fetchRadar();
        const interval = setInterval(fetchRadar, 5000);
        return () => clearInterval(interval);
    }, [activeHorizon]);

    // Save previous data reference for price flashing comparison
    useEffect(() => {
        if (!previousDataRef.current) {
            // Initial load
            const initialMap = {};
            data.forEach(d => initialMap[`${d.symbol}-${d.horizon}`] = d.current_price);
            previousDataRef.current = initialMap;
            return;
        }

        const newFlashes = { ...flashes };
        let hasFlashes = false;
        const newMap = {};

        data.forEach(d => {
            const key = `${d.symbol}-${d.horizon}`;
            newMap[key] = d.current_price;

            const prevPrice = previousDataRef.current[key];
            if (prevPrice && d.current_price !== prevPrice) {
                newFlashes[key] = d.current_price > prevPrice ? 'up' : 'down';
                hasFlashes = true;
            }
        });

        previousDataRef.current = newMap;

        if (hasFlashes) {
            setFlashes(newFlashes);
            // Clear flashes after 1.5 seconds
            setTimeout(() => {
                setFlashes(current => {
                    const cleared = { ...current };
                    Object.keys(newMap).forEach(k => {
                        if (newFlashes[k]) delete cleared[k];
                    });
                    return cleared;
                });
            }, 1500);
        }
    }, [data]);

    const getBadgeStyle = (classification) => {
        switch (classification) {
            case 'Investment': return 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
            case 'Swing': return 'bg-amber-500/20 text-amber-400 border border-amber-500/30';
            case 'F&O': return 'bg-rose-500/20 text-rose-400 border border-rose-500/30';
            default: return 'bg-slate-800 text-slate-400 border border-slate-700';
        }
    };

    const filteredData = activeCategory === 'ALL'
        ? data
        : data.filter(d => (d.asset_type || 'stock').toUpperCase() === activeCategory);

    return (
        <div className="space-y-6 relative">
            {/* In-App Toast Notification */}
            {toast && (
                <div className={`fixed top-6 right-6 z-50 p-4 rounded-2xl shadow-2xl border animate-slideIn max-w-xs ${toast.decision === 'BUY'
                    ? 'bg-emerald-950 border-emerald-500/50 shadow-emerald-500/20'
                    : 'bg-rose-950 border-rose-500/50 shadow-rose-500/20'
                    }`}>
                    <div className="flex items-center gap-3 mb-2">
                        <span className={`text-xs font-black px-2 py-0.5 rounded ${toast.decision === 'BUY' ? 'bg-emerald-500 text-black' : 'bg-rose-500 text-white'
                            }`}>{toast.decision}</span>
                        <span className="text-white font-black text-sm">{toast.symbol}</span>
                        <span className="ml-auto text-[10px] text-slate-400">{((toast.confidence || 0) * 100).toFixed(0)}% conf</span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-[10px]">
                        <div><span className="text-slate-500">Entry</span><br /><span className="text-white font-bold">{toast.entry?.toFixed(2)}</span></div>
                        <div><span className="text-slate-500">Stop Loss</span><br /><span className="text-rose-400 font-bold">{toast.sl?.toFixed(2)}</span></div>
                        <div><span className="text-slate-500">Target</span><br /><span className="text-emerald-400 font-bold">{toast.tp?.toFixed(2)}</span></div>
                    </div>
                </div>
            )}

            {/* Top Signals Header / Marquee */}
            {signals.length > 0 && (
                <div className="bg-gradient-to-r from-primary/20 via-indigo-600/10 to-transparent border border-primary/30 rounded-2xl p-4 flex items-center gap-6 overflow-hidden">
                    <div className="flex items-center gap-2 text-primary font-black shrink-0">
                        <Rocket size={18} className="animate-bounce" />
                        <span className="text-xs uppercase tracking-widest">Global Top Picks:</span>
                    </div>
                    <div className="flex gap-8 animate-marquee whitespace-nowrap">
                        {signals.map(s => (
                            <div key={`${s.symbol}-${s.horizon}`} className="flex items-center gap-3">
                                <span className="text-sm font-bold text-white">{s.symbol}</span>
                                <span className={`text-xs font-mono font-bold ${s.expected_return >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                    {s.expected_return >= 0 ? '+' : ''}{s.expected_return.toFixed(2)}%
                                </span>
                                <span className="text-[10px] text-slate-500 bg-slate-900/50 px-1.5 rounded">{s.horizon}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* Main Radar Panel */}
                <div className="lg:col-span-3 space-y-6">
                    <div className="bg-slate-900/40 border border-slate-800 rounded-3xl overflow-hidden backdrop-blur-xl">
                        <div className="p-6 border-b border-slate-800 flex flex-col md:flex-row md:justify-between md:items-center gap-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-primary/10 rounded-xl">
                                    <Radar size={24} className="text-primary animate-pulse" />
                                </div>
                                <div>
                                    <h2 className="text-xl font-black text-white">Quantum Market Radar</h2>
                                    <p className="text-xs text-slate-500 font-medium">Autonomous Multi-Horizon Scanner</p>
                                </div>
                            </div>

                            <div className="flex items-center gap-2 bg-slate-950/50 p-1 rounded-xl border border-slate-800">
                                {['ALL', 'INTRADAY', 'SHORT', 'LONG'].map(h => (
                                    <button
                                        key={h}
                                        onClick={() => setActiveHorizon(h)}
                                        className={`px-4 py-1.5 rounded-lg text-[10px] font-black tracking-widest transition-all ${activeHorizon === h ? 'bg-primary text-black shadow-lg shadow-primary/20' : 'text-slate-400 hover:text-white'}`}
                                    >
                                        {h}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="px-6 py-3 border-b border-slate-800 flex items-center gap-4 bg-slate-900/20">
                            <Filter size={14} className="text-slate-500" />
                            <div className="flex gap-2">
                                {['ALL', 'STOCK', 'ETF', 'CRYPTO', 'COMMODITY'].map(cat => (
                                    <button
                                        key={cat}
                                        onClick={() => setActiveCategory(cat)}
                                        className={`text-[9px] font-bold px-3 py-1 rounded-full border ${activeCategory === cat ? 'bg-primary/20 border-primary text-primary' : 'border-slate-800 text-slate-500 hover:border-slate-600'}`}
                                    >
                                        {cat}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full text-left">
                                <thead className="bg-slate-950/30">
                                    <tr className="text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-slate-800">
                                        <th className="px-6 py-4">Asset Intelligence</th>
                                        <th className="px-6 py-4">Horizon</th>
                                        <th className="px-6 py-4 text-right">Latest Value</th>
                                        <th className="px-6 py-4 text-center">AI Pred (% Pnl)</th>
                                        <th className="px-6 py-4">Market Status</th>
                                        <th className="px-6 py-4">Action</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800/50">
                                    {filteredData.map((row) => {
                                        const rowId = `${row.symbol}-${row.horizon}`;
                                        const isExpanded = expandedRows.has(rowId);
                                        const raw = row.raw_payload || {};
                                        return (
                                            <React.Fragment key={rowId}>
                                                <tr className="group hover:bg-slate-800/30 transition-colors cursor-pointer" onClick={() => toggleRow(rowId)}>
                                                    <td className="px-6 py-5">
                                                        <div className="flex items-center gap-4">
                                                            <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-xs font-black border border-slate-700 group-hover:border-primary/50 transition-colors">
                                                                {row.symbol.slice(0, 2)}
                                                            </div>
                                                            <div>
                                                                <div className="text-sm font-black text-white">{row.symbol}</div>
                                                                <div className={`mt-1 text-[10px] px-1.5 py-0.5 rounded inline-block font-bold ${getBadgeStyle(row.classification || 'Pending')}`}>
                                                                    {row.classification || 'Awaiting ML'}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-5">
                                                        <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400">
                                                            <Clock size={12} className="text-primary" />
                                                            {row.horizon}
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-5 text-right font-mono text-sm font-bold">
                                                        <span className={
                                                            flashes[rowId] === 'up'
                                                                ? "text-emerald-400 bg-emerald-500/20 px-2 py-1 rounded transition-colors duration-300"
                                                                : flashes[rowId] === 'down'
                                                                    ? "text-rose-400 bg-rose-500/20 px-2 py-1 rounded transition-colors duration-300"
                                                                    : "text-white transition-colors duration-500"
                                                        }>
                                                            {formatCurrency(row.current_price, row.symbol)}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-5">
                                                        <div className="flex flex-col items-center gap-1">
                                                            <div className={`text-sm font-black ${(row.expected_return || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                                                {(row.expected_return || 0) >= 0 ? '+' : ''}{(row.expected_return || 0).toFixed(2)}%
                                                            </div>
                                                            <div className="w-20 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                                                <div
                                                                    className={`h-full ${(row.expected_return || 0) >= 0 ? 'bg-emerald-500' : 'bg-rose-500'}`}
                                                                    style={{ width: `${Math.min(100, Math.abs(row.expected_return || 0) * 10)}%` }}
                                                                />
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-5">
                                                        <div className="space-y-1">
                                                            <div className="text-[10px] font-bold text-slate-300 flex items-center gap-1.5 uppercase">
                                                                <Globe size={10} className="text-indigo-400" />
                                                                {(row.regime || 'Unknown').replace(/_/g, ' ')}
                                                            </div>
                                                            <div className={`text-xs font-black ${(row.decision || 'HOLD') === 'BUY' ? 'text-emerald-400' : (row.decision || 'HOLD') === 'SELL' ? 'text-rose-400' : 'text-slate-500'}`}>
                                                                {(row.decision || 'HOLD')} SIGNAL
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-5">
                                                        <button className="p-2 bg-slate-800 hover:bg-primary/20 text-slate-400 hover:text-primary rounded-xl transition-all border border-slate-700">
                                                            {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                                        </button>
                                                    </td>
                                                </tr>
                                                {isExpanded && (
                                                    <tr className="bg-slate-900/50">
                                                        <td colSpan="6" className="p-0 border-b border-slate-800">
                                                            {/* Expanded Agent Context Panel */}
                                                            <div className="p-6 bg-slate-900 shadow-inner border-l-2 border-primary">
                                                                <h3 className="text-sm font-black text-white uppercase tracking-widest mb-4 flex items-center gap-2">
                                                                    <ShieldAlert size={16} className="text-amber-400" />
                                                                    Agent's Decision & Rationale
                                                                </h3>
                                                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pointer-events-none">
                                                                    {/* ML Prediction */}
                                                                    <div className="bg-slate-950/50 rounded-xl p-4 border border-slate-800/80">
                                                                        <h4 className="text-[10px] font-black text-slate-500 uppercase flex items-center gap-2 mb-3">
                                                                            <Activity size={12} className="text-indigo-400" /> Pattern & ML Consensus
                                                                        </h4>
                                                                        {raw.ml_predictions ? (
                                                                            <div className="space-y-3">
                                                                                <div className="flex justify-between text-xs font-bold">
                                                                                    <span className="text-slate-400">Bullish Prob</span>
                                                                                    <span className="text-emerald-400">{(raw.ml_predictions.bull_prob * 100).toFixed(1)}%</span>
                                                                                </div>
                                                                                <div className="flex justify-between text-xs font-bold">
                                                                                    <span className="text-slate-400">Bearish Prob</span>
                                                                                    <span className="text-rose-400">{(raw.ml_predictions.bear_prob * 100).toFixed(1)}%</span>
                                                                                </div>
                                                                                <div className="mt-2 text-[10px] text-slate-500 italic">
                                                                                    Est. Move: {formatCurrency(raw.ml_predictions.predicted_next_close || 0, row.symbol)}
                                                                                </div>
                                                                            </div>
                                                                        ) : (
                                                                            <div className="text-xs text-slate-500 font-bold">Awaiting Scan Cycle</div>
                                                                        )}
                                                                    </div>
                                                                    {/* Market Context */}
                                                                    <div className="bg-slate-950/50 rounded-xl p-4 border border-slate-800/80">
                                                                        <h4 className="text-[10px] font-black text-slate-500 uppercase flex items-center gap-2 mb-3">
                                                                            <BarChart2 size={12} className="text-amber-400" /> Technical Context
                                                                        </h4>
                                                                        {raw.latest_indicators ? (
                                                                            <div className="space-y-2">
                                                                                <div className="text-xs font-bold text-slate-300">
                                                                                    ATR Volatility: <span className="text-white">{formatCurrency(raw.latest_indicators.atr || 0, row.symbol)}</span>
                                                                                </div>
                                                                                {raw.latest_indicators.detected_patterns && raw.latest_indicators.detected_patterns.length > 0 && (
                                                                                    <div className="mt-2 text-xs font-bold text-slate-400">
                                                                                        Pattern: <span className="text-amber-400 underline decoration-amber-400/30 underline-offset-2">{raw.latest_indicators.detected_patterns.join(', ').replace(/_/g, ' ')}</span>
                                                                                    </div>
                                                                                )}
                                                                                <div className="mt-2 text-[10px] text-slate-500 leading-tight">
                                                                                    RSI: {(raw.latest_indicators.rsi || 0).toFixed(1)} | MACD: {(raw.latest_indicators.macd || 0).toFixed(2)}
                                                                                </div>
                                                                            </div>
                                                                        ) : (
                                                                            <div className="text-xs text-slate-500 font-bold">Awaiting Technicals</div>
                                                                        )}
                                                                    </div>
                                                                    {/* News/Sentiment */}
                                                                    <div className="bg-slate-950/50 rounded-xl p-4 border border-slate-800/80">
                                                                        <h4 className="text-[10px] font-black text-slate-500 uppercase flex items-center gap-2 mb-3">
                                                                            <BookOpen size={12} className="text-emerald-400" /> Sentiment Rationale
                                                                        </h4>
                                                                        {raw.sentiment && raw.sentiment.status !== 'error' ? (
                                                                            <div className="space-y-2">
                                                                                <div className="flex justify-between items-center text-xs font-bold">
                                                                                    <span className="text-slate-400">Overall Score:</span>
                                                                                    <span className={raw.sentiment.score > 0 ? 'text-emerald-400' : raw.sentiment.score < 0 ? 'text-rose-400' : 'text-slate-400'}>
                                                                                        {raw.sentiment.score > 0 ? '+' : ''}{raw.sentiment.score.toFixed(2)}
                                                                                    </span>
                                                                                </div>
                                                                                <p className="text-[10px] text-slate-300 font-medium leading-relaxed italic line-clamp-3">
                                                                                    "{raw.sentiment.rationale || 'No major news catalyst identified.'}"
                                                                                </p>
                                                                            </div>
                                                                        ) : (
                                                                            <div className="text-xs text-slate-500 font-bold">No recent news drivers.</div>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                )}
                                            </React.Fragment>
                                        );
                                    })}
                                </tbody>
                            </table>
                            {filteredData.length === 0 && (
                                <div className="py-20 text-center">
                                    <div className="text-slate-600 font-black text-xl mb-2 opacity-50 uppercase tracking-widest">No Active Scans</div>
                                    <p className="text-sm text-slate-500">Add assets or change filters to see live analysis.</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Signals Sidebar */}
                <div className="space-y-6">
                    <div className="bg-gradient-to-b from-indigo-500/10 to-transparent border border-indigo-500/30 rounded-3xl p-6 relative overflow-hidden h-fit">
                        <div className="absolute -right-6 -top-6 text-indigo-500/10"><Bell size={100} /></div>
                        <h3 className="text-xs font-black text-indigo-400 uppercase tracking-[0.2em] mb-4 flex items-center gap-3 relative z-10">
                            <Zap size={14} fill="currentColor" />
                            Live High-Conf Signals
                            {signals.length > 0 && <span className="ml-auto bg-indigo-500 text-black text-[9px] font-black px-2 py-0.5 rounded-full">{signals.length}</span>}
                        </h3>
                        <div className="space-y-3 relative z-10">
                            {signals.map(s => (
                                <div key={`sig-${s.symbol}-${s.horizon}`} className={`border p-3 rounded-2xl transition-all cursor-pointer group ${s.decision === 'BUY'
                                    ? 'bg-emerald-950/40 border-emerald-500/30 hover:border-emerald-400/60'
                                    : 'bg-rose-950/40 border-rose-500/30 hover:border-rose-400/60'
                                    }`}>
                                    {/* Signal Header */}
                                    <div className="flex justify-between items-center mb-2">
                                        <div className="flex items-center gap-2">
                                            <span className={`text-[9px] font-black px-2 py-0.5 rounded ${s.decision === 'BUY' ? 'bg-emerald-500 text-black' : 'bg-rose-500 text-white'
                                                }`}>{s.decision}</span>
                                            <span className="text-sm font-black text-white">{s.symbol}</span>
                                        </div>
                                        <div className="flex items-center gap-1">
                                            {s.signal_strength === 'STRONG' && <span className="text-[8px] font-black text-amber-400 bg-amber-500/10 px-1.5 rounded border border-amber-500/20">STRONG</span>}
                                            <span className="text-[9px] text-slate-500 bg-slate-900/50 px-1.5 rounded">{s.horizon}</span>
                                        </div>
                                    </div>
                                    {/* Trade Levels */}
                                    <div className="grid grid-cols-3 gap-1 text-[9px] mb-2">
                                        <div className="bg-slate-900/50 rounded p-1.5">
                                            <div className="text-slate-500 font-bold mb-0.5">ENTRY</div>
                                            <div className="text-white font-black">{s.entry_price?.toFixed(2) ?? '—'}</div>
                                        </div>
                                        <div className="bg-rose-950/50 rounded p-1.5">
                                            <div className="text-rose-500 font-bold mb-0.5">STOP LOSS</div>
                                            <div className="text-rose-300 font-black">{s.stop_loss?.toFixed(2) ?? '—'}</div>
                                        </div>
                                        <div className="bg-emerald-950/50 rounded p-1.5">
                                            <div className="text-emerald-500 font-bold mb-0.5">TARGET</div>
                                            <div className="text-emerald-300 font-black">{s.take_profit?.toFixed(2) ?? '—'}</div>
                                        </div>
                                    </div>
                                    {/* Target Qualifier Badge (Option B) */}
                                    {s.target_status === 'MEETS_TARGET' && (
                                        <div className="flex items-center gap-1.5 mt-2 px-2 py-1.5 rounded-xl bg-emerald-950/60 border border-emerald-500/30">
                                            <span className="text-emerald-400 text-[10px]">✅</span>
                                            <span className="text-[9px] font-black text-emerald-400 uppercase tracking-wider">Meets Your {s.target_label} Target</span>
                                            {s.target_gap > 0 && <span className="ml-auto text-[9px] text-emerald-600 font-bold">+{s.target_gap.toFixed(1)} ahead</span>}
                                        </div>
                                    )}
                                    {s.target_status === 'BELOW_TARGET' && (
                                        <div className="flex items-center gap-1.5 mt-2 px-2 py-1.5 rounded-xl bg-amber-950/40 border border-amber-500/20">
                                            <span className="text-amber-400 text-[10px]">⚠️</span>
                                            <span className="text-[9px] font-black text-amber-400 uppercase tracking-wider">Short of {s.target_label} Target</span>
                                            {s.target_gap != null && <span className="ml-auto text-[9px] text-amber-700 font-bold">{s.target_gap.toFixed(1)} short</span>}
                                        </div>
                                    )}
                                    {/* Metrics Row */}
                                    <div className="flex justify-between items-center pt-1.5 mt-1.5 border-t border-slate-800/50">
                                        <span className="text-[9px] text-slate-500">Conf: <span className="text-white font-bold">{((s.confidence || 0) * 100).toFixed(0)}%</span></span>
                                        <span className="text-[9px] text-slate-500">R:R <span className={`font-bold ${s.risk_reward >= 2 ? 'text-emerald-400' : 'text-amber-400'}`}>{s.risk_reward?.toFixed(1) ?? '—'}x</span></span>
                                        <span className="text-[9px] text-slate-500">ML: <span className="text-indigo-400 font-bold">{s.decision === 'BUY' ? ((s.bull_prob || 0) * 100).toFixed(0) : ((s.bear_prob || 0) * 100).toFixed(0)}%</span></span>
                                    </div>
                                </div>
                            ))}
                            {signals.length === 0 && (
                                <div className="text-center py-8">
                                    <Activity size={28} className="text-slate-700 mx-auto mb-2" />
                                    <p className="text-xs text-slate-600 font-bold uppercase tracking-widest">No BUY/SELL signals yet</p>
                                    <p className="text-[10px] text-slate-700 mt-1">Awaiting next scan cycle...</p>
                                </div>
                            )}
                        </div>
                        <button
                            onClick={() => {
                                if ('Notification' in window) Notification.requestPermission();
                            }}
                            className="w-full mt-4 py-3 bg-indigo-500 hover:bg-indigo-600 text-white font-black text-xs rounded-2xl transition-all shadow-lg shadow-indigo-500/30 uppercase tracking-widest"
                        >
                            {('Notification' in window && Notification.permission === 'granted') ? '🔔 Alerts Enabled' : 'Enable Push Alerts'}
                        </button>
                    </div>

                    {/* Add Asset Form */}
                    <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-6">
                        <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                            <Plus size={14} className="text-primary" /> Inject New Asset
                        </h3>
                        <form onSubmit={handleAddAsset} className="space-y-3">
                            <input
                                type="text"
                                placeholder="Symbol (e.g. AAPL, NIFTY)"
                                value={addSymbol}
                                onChange={e => setAddSymbol(e.target.value.toUpperCase())}
                                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white font-bold outline-none focus:border-primary transition-colors"
                                required
                            />
                            <div className="flex gap-2">
                                <select
                                    value={addType}
                                    onChange={e => setAddType(e.target.value)}
                                    className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-2 py-2 text-[10px] font-bold text-slate-400 outline-none focus:border-primary uppercase"
                                >
                                    <option value="stock">Stock/Index</option>
                                    <option value="crypto">Crypto</option>
                                    <option value="etf">ETF</option>
                                    <option value="commodity">Commodity</option>
                                </select>
                                <select
                                    value={addHorizon}
                                    onChange={e => setAddHorizon(e.target.value)}
                                    className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-2 py-2 text-[10px] font-bold text-slate-400 outline-none focus:border-primary uppercase"
                                >
                                    <option value="INTRADAY">Intraday</option>
                                    <option value="SHORT">Short Term</option>
                                    <option value="LONG">Long Term</option>
                                </select>
                            </div>
                            <button
                                type="submit"
                                disabled={addStatus.loading || !addSymbol}
                                className="w-full bg-slate-800 hover:bg-primary text-slate-300 hover:text-black font-black text-xs py-2 rounded-lg transition-all disabled:opacity-50"
                            >
                                {addStatus.loading ? 'Injecting...' : 'Add to Scanner'}
                            </button>
                            {addStatus.success && <p className="text-emerald-400 text-[9px] font-bold text-center">Asset added to tracking queue.</p>}
                            {addStatus.error && <p className="text-rose-400 text-[9px] font-bold text-center">{addStatus.error}</p>}
                        </form>
                    </div>

                    <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-6">
                        <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                            <BarChart2 size={12} className="text-primary" /> Radar Performance
                        </h3>
                        {accuracy ? (
                            <div className="space-y-4">
                                {/* Win Rate */}
                                <div>
                                    <div className="flex justify-between items-end mb-1">
                                        <span className="text-xs text-slate-400">Win Rate</span>
                                        <span className="text-sm font-black text-white">{accuracy.win_rate}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                        <div className="h-full bg-emerald-500 rounded-full transition-all duration-700" style={{ width: `${accuracy.win_rate}%` }} />
                                    </div>
                                </div>
                                {/* Trade Stats Grid */}
                                <div className="grid grid-cols-2 gap-2 text-[10px]">
                                    <div className="bg-emerald-950/40 rounded-xl p-2.5 border border-emerald-900/40">
                                        <div className="text-emerald-400 font-black text-lg">{accuracy.wins}</div>
                                        <div className="text-slate-500 font-bold">Wins</div>
                                    </div>
                                    <div className="bg-rose-950/40 rounded-xl p-2.5 border border-rose-900/40">
                                        <div className="text-rose-400 font-black text-lg">{accuracy.losses}</div>
                                        <div className="text-slate-500 font-bold">Losses</div>
                                    </div>
                                    <div className="bg-slate-800/40 rounded-xl p-2.5 border border-slate-700/30">
                                        <div className="text-amber-400 font-black text-lg">{accuracy.pending}</div>
                                        <div className="text-slate-500 font-bold">Pending</div>
                                    </div>
                                    <div className="bg-slate-800/40 rounded-xl p-2.5 border border-slate-700/30">
                                        <div className="text-indigo-400 font-black text-lg">{accuracy.profit_factor}x</div>
                                        <div className="text-slate-500 font-bold">Profit Factor</div>
                                    </div>
                                </div>
                                <div className="text-[9px] text-slate-600 text-center mt-2">
                                    {accuracy.total_predictions} total signals tracked • Live from feedback DB
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                <div className="flex justify-between items-end">
                                    <span className="text-xs text-slate-400">Accumulating Data...</span>
                                    <span className="text-sm font-black text-slate-600">—</span>
                                </div>
                                <div className="w-full h-1 bg-slate-800 rounded-full"><div className="w-0 h-full bg-slate-700 rounded-full" /></div>
                                <p className="text-[10px] text-slate-700 text-center">Win/Loss tracked after each scan cycle</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RadarView;
