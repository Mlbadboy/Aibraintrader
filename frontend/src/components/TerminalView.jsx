import React, { useState } from 'react';
import TradingViewChart from './TradingViewChart';
import { formatCurrency } from '../utils/formatters';

const TerminalView = ({ data }) => {
    // We use data passed from App.jsx if present, otherwise fallback to default mock array
    const defaultEquities = [
        { symbol: 'NIFTY', tv_symbol: 'NSE:NIFTY', name: 'NIFTY 50', price: 23145.20, change: '-0.50%', trend: 'down' },
        { symbol: 'SENSEX', tv_symbol: 'BSE:SENSEX', name: 'SENSEX', price: 76450.10, change: '+0.10%', trend: 'up' },
        { symbol: 'BANKNIFTY', tv_symbol: 'NSE:BANKNIFTY', name: 'BANK NIFTY', price: 49870.50, change: '+0.25%', trend: 'up' },
        { symbol: 'RELIANCE.NS', tv_symbol: 'BSE:RELIANCE', name: 'Reliance Ind.', price: 2950.40, change: '+1.20%', trend: 'up' },
        { symbol: 'GOLDBEES.NS', tv_symbol: 'BSE:GOLDBEES', name: 'Gold BeES ETF', price: 62.45, change: '+0.15%', trend: 'up' },
        { symbol: 'GOLD', tv_symbol: 'OANDA:XAUUSD', name: 'Gold Spot', price: 2345.60, change: '+0.45%', trend: 'up' },
        { symbol: 'AAPL', tv_symbol: 'NASDAQ:AAPL', name: 'Apple Inc.', price: 189.43, change: '-0.21%', trend: 'down' },
        { symbol: 'NVDA', tv_symbol: 'NASDAQ:NVDA', name: 'NVIDIA Corp.', price: 124.58, change: '+4.82%', trend: 'up' },
        { symbol: 'BTC', tv_symbol: 'BINANCE:BTCUSDT', name: 'Bitcoin', price: 65123.40, change: '+2.10%', trend: 'up' }
    ];

    const [equities] = useState(defaultEquities);
    const [activeAsset, setActiveAsset] = useState(data || defaultEquities[0]);

    // Update active asset if parent data changes
    React.useEffect(() => {
        if (data) {
            setActiveAsset(data);
        }
    }, [data]);

    // Fallbacks for display
    const symbol = activeAsset.symbol || "UNKNOWN";
    const name = activeAsset.name || symbol;
    const price = activeAsset.latest_indicators?.close || activeAsset.price || 0;
    const change = activeAsset.change || "Live";
    const trend = activeAsset.trend || "up";
    const classification = activeAsset.classification || null;
    const tvSymbol = activeAsset.tv_symbol || symbol;
    const optionsStrategy = activeAsset.options_strategy || null;

    return (
        <div className="flex h-full overflow-hidden">
            <main className="flex-1 flex overflow-hidden">
                <section className="w-[60%] flex flex-col border-r border-slate-800 bg-background-dark/50">
                    <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/20">
                        <div className="flex gap-4">
                            <button className="text-xs font-bold text-white border-b-2 border-primary pb-1">All Equities</button>
                            <button className="text-xs font-bold text-slate-500 hover:text-slate-300 pb-1">Mutual Funds</button>
                        </div>
                    </div>
                    <div className="flex-1 overflow-y-auto no-scrollbar">
                        <table className="w-full text-left">
                            <thead className="sticky top-0 bg-background-dark/90 backdrop-blur z-10">
                                <tr className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800">
                                    <th className="px-4 py-3">Ticker</th>
                                    <th className="px-4 py-3">Price</th>
                                    <th className="px-4 py-3">Change</th>
                                    <th className="px-4 py-3 text-right">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {equities.map((eq) => (
                                    <tr
                                        key={eq.symbol}
                                        onClick={() => setActiveAsset(eq)}
                                        className={`cursor-pointer border-l-2 ${activeAsset.symbol === eq.symbol ? 'bg-primary/10 border-primary' : 'hover:bg-slate-800/30 border-transparent'}`}
                                    >
                                        <td className="px-4 py-3">
                                            <div className="flex items-center gap-3">
                                                <div className="text-sm font-black text-white">{eq.symbol}</div>
                                                <div className="text-[10px] text-slate-500">{eq.name}</div>
                                            </div>
                                        </td>
                                        <td className="px-4 py-3 text-sm font-mono text-white">{formatCurrency(eq.price, eq.symbol)}</td>
                                        <td className={`px-4 py-3 text-sm font-mono ${eq.trend === 'up' ? 'text-emerald-accent' : 'text-rose-400'}`}>{eq.change}</td>
                                        <td className="px-4 py-3 text-right"><span className={`material-symbols-outlined text-sm ${activeAsset.symbol === eq.symbol ? 'text-primary' : 'text-slate-600'}`}>star</span></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </section>
                <section className="flex-1 flex flex-col overflow-y-auto no-scrollbar">
                    <div className="p-6 border-b border-slate-800 flex justify-between items-start">
                        <div>
                            <div className="flex items-center gap-3">
                                <h2 className="text-2xl font-black text-white">{symbol}</h2>
                                {classification && (
                                    <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider ${classification === 'Investment' ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30' :
                                        classification === 'Swing' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                                            classification === 'F&O' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                                                'bg-slate-800 text-slate-400 border border-slate-700'
                                        }`}>
                                        {classification} Horizon
                                    </span>
                                )}
                            </div>
                            <p className="text-sm text-slate-500">{name} · Market Terminal</p>
                        </div>
                        <div className="text-right">
                            <div className="text-2xl font-black text-white">{formatCurrency(price, symbol)}</div>
                            <div className={`text-sm font-bold ${trend === 'up' ? 'text-emerald-accent' : 'text-rose-400'}`}>{change}</div>
                        </div>
                    </div>
                    {/* Chart & Trading Panel */}
                    <div className="p-6 space-y-6 flex-1 flex flex-col">
                        <div className="h-[400px] w-full rounded-xl overflow-hidden border border-slate-800">
                            <TradingViewChart symbol={tvSymbol} />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
                                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Cash Market Order</h3>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-3">
                                        <input className="w-full bg-slate-950 border border-slate-800 rounded h-10 px-3 text-sm text-white" placeholder="Quantity" type="number" defaultValue="10" />
                                        <button className="w-full bg-emerald-accent text-black font-black text-sm py-3 rounded">BUY {symbol}</button>
                                    </div>
                                    <div className="space-y-3">
                                        <input className="w-full bg-slate-950 border border-slate-800 rounded h-10 px-3 text-sm text-white" placeholder="Target Price" type="number" />
                                        <button className="w-full bg-rose-500 text-white font-black text-sm py-3 rounded">SELL {symbol}</button>
                                    </div>
                                </div>
                            </div>

                            {optionsStrategy && optionsStrategy.status === 'success' && (
                                <div className="bg-gradient-to-br from-indigo-500/10 to-transparent border border-indigo-500/30 rounded-xl p-4 relative overflow-hidden">
                                    <div className="absolute -right-10 -top-10 text-indigo-500/20 rotate-12">
                                        <span className="material-symbols-outlined" style={{ fontSize: '100px' }}>psychology</span>
                                    </div>
                                    <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                        <span className="material-symbols-outlined text-[14px]">auto_awesome</span>
                                        AI Options Strategy (F&O)
                                    </h3>
                                    <div className="space-y-3 relative z-10">
                                        <div className="flex justify-between items-center text-sm">
                                            <span className="text-slate-400">Recommended Strike</span>
                                            <span className="text-white font-black bg-slate-800 px-2 py-1 rounded border border-slate-700">{optionsStrategy.strike} {optionsStrategy.type}</span>
                                        </div>
                                        <div className="flex justify-between items-center text-sm">
                                            <span className="text-slate-400">Current Premium</span>
                                            <span className="text-emerald-400 font-mono font-bold">₹{optionsStrategy.lastPrice}</span>
                                        </div>
                                        <div className="flex justify-between items-center text-sm">
                                            <span className="text-slate-400">Implied Volatility</span>
                                            <span className="text-slate-300 font-mono">{(optionsStrategy.impliedVolatility * 100).toFixed(2)}%</span>
                                        </div>
                                        <div className="pt-3 border-t border-indigo-500/20">
                                            <p className="text-[10px] text-indigo-300 font-medium leading-relaxed">{optionsStrategy.rationale}</p>
                                        </div>
                                        <button className="w-full mt-2 bg-indigo-500 hover:bg-indigo-600 text-white font-black text-sm py-2.5 rounded transition-colors shadow-lg shadow-indigo-500/20">
                                            ONE-CLICK EXECUTE {optionsStrategy.strike}{optionsStrategy.type}
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </section>
            </main>
        </div>
    );
};

export default TerminalView;
