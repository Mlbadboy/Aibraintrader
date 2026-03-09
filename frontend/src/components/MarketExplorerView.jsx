import React from 'react';
import TradingViewChart from './TradingViewChart';

const MarketExplorerView = ({ onSelectAsset }) => {
    return (
        <div className="p-8 space-y-10">
            <section className="bg-card-dark rounded-2xl border border-slate-800 overflow-hidden shadow-2xl">
                <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-900/50">
                    <div className="flex items-center gap-4">
                        <h2 className="text-xl font-bold text-white flex items-center gap-2">
                            <span className="material-symbols-outlined text-neon-blue animate-pulse">monitoring</span>
                            Institutional Market Flow
                        </h2>
                        <div className="h-6 w-px bg-slate-800"></div>
                        <div className="flex gap-4">
                            {[
                                { name: 'S&P 500', symbol: 'SPY', color: 'bg-primary', type: 'stock' },
                                { name: 'Nasdaq 100', symbol: 'QQQ', color: 'bg-emerald-accent', type: 'stock' },
                                { name: 'Bitcoin', symbol: 'BTCUSD', color: 'bg-neon-purple', type: 'crypto' }
                            ].map(m => (
                                <div key={m.name} onClick={() => onSelectAsset && onSelectAsset(m.type, m.symbol)} className={`flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/50 border border-slate-700 cursor-pointer hover:bg-slate-700/50 transition-colors`}>
                                    <div className={`size-2 rounded-full ${m.color}`}></div>
                                    <span className="text-[10px] font-black text-slate-300 uppercase tracking-tighter">{m.name}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
                <div className="h-[450px] w-full p-4 bg-slate-950">
                    <TradingViewChart symbol="SPY" />
                </div>
            </section>

            <section>
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                        <span className="material-symbols-outlined text-primary">analytics</span>
                        US Market Intelligence
                    </h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[
                        { name: 'Apple Inc.', symbol: 'AAPL', change: '+1.2%', trend: 'up' },
                        { name: 'Tesla, Inc.', symbol: 'TSLA', change: '-0.8%', trend: 'down' },
                        { name: 'Nvidia Corp.', symbol: 'NVDA', change: '+2.5%', trend: 'up' },
                        { name: 'Microsoft', symbol: 'MSFT', change: '+1.5%', trend: 'up' },
                        { name: 'Amazon', symbol: 'AMZN', change: '+0.9%', trend: 'up' },
                        { name: 'Meta Platforms', symbol: 'META', change: '+3.1%', trend: 'up' }
                    ].map(stock => (
                        <div key={stock.symbol} onClick={() => onSelectAsset && onSelectAsset('stock', stock.symbol)} className="cursor-pointer p-6 rounded-2xl bg-[#0f172a] border border-slate-800 shadow-xl hover:border-primary/50 transition-all group overflow-hidden relative">
                            <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
                                <span className="material-symbols-outlined text-6xl text-white font-black">{stock.symbol.slice(0, 1)}</span>
                            </div>
                            <div className="flex justify-between items-start mb-4 relative z-10">
                                <div>
                                    <h3 className="text-lg font-black text-white">{stock.symbol}</h3>
                                    <p className="text-xs font-bold text-slate-500 uppercase">{stock.name}</p>
                                </div>
                                <span className={`text-xs font-black px-2 py-1 rounded-md ${stock.trend === 'up' ? 'text-emerald-400 bg-emerald-400/10' : 'text-rose-400 bg-rose-400/10'}`}>
                                    {stock.change}
                                </span>
                            </div>
                            <div className="h-32 w-full mt-4 rounded-xl overflow-hidden grayscale group-hover:grayscale-0 transition-all duration-500 pointer-events-none">
                                <TradingViewChart symbol={stock.symbol} />
                            </div>
                        </div>
                    ))}
                </div>
            </section>
            <section>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pb-4">
                    <div className="p-5 rounded-2xl bg-gradient-to-br from-primary/10 to-transparent border border-primary/20 cursor-pointer hover:border-primary/40 transition-all" onClick={() => onSelectAsset && onSelectAsset('crypto', 'BTC')}>
                        <div className="flex justify-between items-start mb-4">
                            <div className="p-2 bg-primary/20 rounded-lg text-primary"><span className="material-symbols-outlined">trending_up</span></div>
                            <span className="text-[10px] font-bold uppercase text-primary">Live Now</span>
                        </div>
                        <h3 className="text-lg font-bold mb-1">Trending Crypto</h3>
                        <p className="text-xs text-slate-400">Bitcoin & Ethereum breaking key technical levels</p>
                    </div>
                    <div className="p-5 rounded-2xl bg-gradient-to-br from-emerald-500/10 to-transparent border border-emerald-500/20 cursor-pointer hover:border-emerald-500/40 transition-all" onClick={() => onSelectAsset && onSelectAsset('mutualfund', 'VTSAX')}>
                        <div className="flex justify-between items-start mb-4">
                            <div className="p-2 bg-emerald-500/20 rounded-lg text-emerald-500"><span className="material-symbols-outlined">account_balance</span></div>
                            <span className="text-[10px] font-bold uppercase text-emerald-500">Top Funds</span>
                        </div>
                        <h3 className="text-lg font-bold mb-1">Mutual Funds</h3>
                        <p className="text-xs text-slate-400">Vanguard Total Stock Market Index (VTSAX)</p>
                    </div>
                    <div className="p-5 rounded-2xl bg-gradient-to-br from-yellow-500/10 to-transparent border border-yellow-500/20 cursor-pointer hover:border-yellow-500/40 transition-all" onClick={() => onSelectAsset && onSelectAsset('stock', 'RELIANCE.NS')}>
                        <div className="flex justify-between items-start mb-4">
                            <div className="p-2 bg-yellow-500/20 rounded-lg text-yellow-500"><span className="material-symbols-outlined">public</span></div>
                            <span className="text-[10px] font-bold uppercase text-yellow-500">Global Markets</span>
                        </div>
                        <h3 className="text-lg font-bold mb-1">Indian Equities</h3>
                        <p className="text-xs text-slate-400">View NIFTY 50 and top NSE performers</p>
                    </div>
                </div>
            </section>
        </div>
    );
};

export default MarketExplorerView;
