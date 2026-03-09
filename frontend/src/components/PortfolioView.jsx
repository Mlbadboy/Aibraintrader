import React, { useState, useEffect, useRef } from 'react';
import { Plus, Briefcase, TrendingUp, AlertCircle, Trash2, Upload, FileSignature } from 'lucide-react';
import TradingViewChart from './TradingViewChart';

const PortfolioView = () => {
    const [holdings, setHoldings] = useState(() => {
        const saved = localStorage.getItem('trading_brain_portfolio');
        if (saved) {
            try {
                return JSON.parse(saved);
            } catch (e) {
                console.error("Failed to parse portfolio from local storage");
            }
        }
        // Default if nothing saved
        return [
            { id: 1, symbol: 'AAPL', name: 'Apple Inc.', shares: 10, buyPrice: 150.00, currentPrice: 189.43, dateAdded: '2025-08-15' },
            { id: 2, symbol: 'TSLA', name: 'Tesla, Inc.', shares: 5, buyPrice: 205.50, currentPrice: 215.11, dateAdded: '2025-10-01' }
        ];
    });
    const [showAddForm, setShowAddForm] = useState(false);
    const [newSymbol, setNewSymbol] = useState('');
    const [newShares, setNewShares] = useState('');
    const [newPrice, setNewPrice] = useState('');

    // Upload State
    const [isUploading, setIsUploading] = useState(false);
    const fileInputRef = useRef(null);

    // Save to local storage whenever holdings change
    useEffect(() => {
        localStorage.setItem('trading_brain_portfolio', JSON.stringify(holdings));
    }, [holdings]);

    const handleAddHolding = (e) => {
        e.preventDefault();
        if (!newSymbol || !newShares || !newPrice) return;

        const newHolding = {
            id: Date.now(),
            symbol: newSymbol.toUpperCase(),
            name: newSymbol.toUpperCase() + ' Equity',
            shares: parseFloat(newShares),
            buyPrice: parseFloat(newPrice),
            currentPrice: parseFloat(newPrice) * (1 + (Math.random() * 0.1 - 0.05)), // Mocked current price
            dateAdded: new Date().toISOString().split('T')[0]
        };

        setHoldings([...holdings, newHolding]);
        setNewSymbol('');
        setNewShares('');
        setNewPrice('');
        setShowAddForm(false);
    };

    const handleDelete = (id) => {
        setHoldings(holdings.filter(h => h.id !== id));
    };

    const totalInvested = holdings.reduce((acc, h) => acc + (h.shares * h.buyPrice), 0);
    const currentValue = holdings.reduce((acc, h) => acc + (h.shares * h.currentPrice), 0);
    const overallReturn = totalInvested > 0 ? ((currentValue - totalInvested) / totalInvested) * 100 : 0;

    const handleFileUpload = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setIsUploading(true);
        // Simulate Vision AI OCR analysis delay
        setTimeout(() => {
            const parsedHoldings = [
                { id: Date.now() + 1, symbol: 'MSFT', name: 'Microsoft Corp.', shares: 15, buyPrice: 380.00, currentPrice: 412.32, dateAdded: new Date().toISOString().split('T')[0] },
                { id: Date.now() + 2, symbol: 'NVDA', name: 'NVIDIA Corp.', shares: 8, buyPrice: 115.00, currentPrice: 124.58, dateAdded: new Date().toISOString().split('T')[0] }
            ];
            setHoldings(prev => [...prev, ...parsedHoldings]);
            setIsUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = ''; // reset input
            alert("Vision AI successfully parsed 2 assets from the document.");
        }, 2500);
    };

    return (
        <div className="p-8 h-full overflow-y-auto no-scrollbar space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-black text-white flex items-center gap-2">
                        <Briefcase size={24} className="text-primary" />
                        My Portfolio
                    </h2>
                    <p className="text-sm text-slate-500 mt-1">Manage your active holdings and get AI-driven rebalancing advice.</p>
                </div>
                <div className="flex gap-3">
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileUpload}
                        className="hidden"
                        accept="image/*,.pdf"
                    />
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isUploading}
                        className={`bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-lg font-bold flex items-center gap-2 transition-colors border border-slate-700 ${isUploading ? 'opacity-50 cursor-wait' : ''}`}
                    >
                        {isUploading ? (
                            <><div className="size-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div> Scanning...</>
                        ) : (
                            <><Upload size={18} /> Import Auto</>
                        )}
                    </button>
                    <button
                        onClick={() => setShowAddForm(!showAddForm)}
                        className="bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg font-bold flex items-center gap-2 transition-colors shadow-lg"
                    >
                        <Plus size={18} />
                        Manual Add
                    </button>
                </div>
            </div>

            {/* Top Metrics Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-[#0f172a] p-6 rounded-2xl border border-slate-800 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-5 bg-primary/20 rounded-bl-full w-24 h-24"></div>
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Total Invested</p>
                    <h3 className="text-3xl font-black text-white">${totalInvested.toLocaleString(undefined, { minimumFractionDigits: 2 })}</h3>
                </div>
                <div className="bg-[#0f172a] p-6 rounded-2xl border border-slate-800 relative overflow-hidden">
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Current Value</p>
                    <h3 className="text-3xl font-black text-white">${currentValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}</h3>
                </div>
                <div className="bg-[#0f172a] p-6 rounded-2xl border border-slate-800 relative overflow-hidden">
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Overall Return</p>
                    <h3 className={`text-3xl font-black ${overallReturn >= 0 ? 'text-emerald-400' : 'text-rose-400'} flex items-center gap-2`}>
                        {overallReturn >= 0 ? '+' : ''}{overallReturn.toFixed(2)}%
                        <TrendingUp size={24} className={overallReturn >= 0 ? 'text-emerald-400' : 'text-rose-400'} />
                    </h3>
                </div>
            </div>

            {/* Add Form Content */}
            {showAddForm && (
                <div className="bg-slate-900/50 p-6 rounded-xl border border-primary/30 animate-in slide-in-from-top-4">
                    <h4 className="text-sm font-bold text-primary mb-4 uppercase tracking-widest">Manual Trade Entry</h4>
                    <form onSubmit={handleAddHolding} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                        <div>
                            <label className="block text-xs font-bold text-slate-400 mb-2">Ticker Symbol</label>
                            <input type="text" value={newSymbol} onChange={e => setNewSymbol(e.target.value)} placeholder="e.g. MSFT" className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-white outline-none focus:border-primary" required />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-slate-400 mb-2">Shares/Quantity</label>
                            <input type="number" step="0.01" value={newShares} onChange={e => setNewShares(e.target.value)} placeholder="10" className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-white outline-none focus:border-primary" required />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-slate-400 mb-2">Avg Buy Price ($)</label>
                            <input type="number" step="0.01" value={newPrice} onChange={e => setNewPrice(e.target.value)} placeholder="200.50" className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-white outline-none focus:border-primary" required />
                        </div>
                        <button type="submit" className="bg-emerald-500 hover:bg-emerald-600 text-black font-black py-2 px-4 rounded transition-colors h-[42px]">
                            Save Holding
                        </button>
                    </form>
                </div>
            )}

            {/* Main Content Area */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* Holdings List (Left 2/3) */}
                <div className="lg:col-span-2 space-y-4">
                    <h3 className="text-lg font-bold text-white mb-4">Active Assets</h3>
                    {holdings.length === 0 ? (
                        <div className="p-8 text-center text-slate-500 bg-[#0f172a] rounded-2xl border border-slate-800">
                            No holdings added yet. Add an asset to track your portfolio.
                        </div>
                    ) : (
                        holdings.map(h => {
                            const ret = ((h.currentPrice - h.buyPrice) / h.buyPrice) * 100;
                            const profit = (h.currentPrice - h.buyPrice) * h.shares;
                            // Fake AI logic based on returns
                            const suggestion = ret > 15 ? 'Take Profits (Sell 20%)' : ret < -5 ? 'Averaging Opportunity' : 'HOLD Base Position';
                            const suggestionColor = ret > 15 ? 'text-primary' : ret < -5 ? 'text-emerald-400' : 'text-slate-400';

                            // Days held
                            const daysHeld = Math.floor((new Date() - new Date(h.dateAdded)) / (1000 * 60 * 60 * 24));

                            return (
                                <div key={h.id} className="bg-[#0f172a] p-5 rounded-xl border border-slate-800 flex flex-col md:flex-row gap-6 hover:border-slate-700 transition-colors group">
                                    <div className="flex-1">
                                        <div className="flex justify-between items-start mb-2">
                                            <div>
                                                <h4 className="text-xl font-black text-white">{h.symbol}</h4>
                                                <p className="text-xs text-slate-500">{h.shares} Shares @ ${h.buyPrice.toFixed(2)}</p>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-lg font-bold text-white">${(h.currentPrice * h.shares).toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                                                <div className={`text-sm font-bold ${ret >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                                    {ret >= 0 ? '+' : ''}${profit.toFixed(2)} ({ret.toFixed(2)}%)
                                                </div>
                                            </div>
                                        </div>
                                        <div className="mt-4 pt-4 border-t border-slate-800/50 flex flex-wrap gap-4 items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <div className={`size-2 rounded-full ${suggestionColor.replace('text-', 'bg-')}`}></div>
                                                <span className={`text-xs font-bold ${suggestionColor}`}>AI: {suggestion}</span>
                                            </div>
                                            <span className="text-[10px] uppercase text-slate-500 tracking-widest font-bold">Held for: {daysHeld} Days</span>
                                        </div>
                                    </div>
                                    <div className="w-full md:w-32 flex flex-col justify-between border-l border-slate-800 pl-6 gap-2">
                                        <div className="text-xs text-slate-500 text-center font-bold">Actions</div>
                                        <button className="text-xs font-bold text-primary hover:text-white transition-colors bg-primary/10 py-1.5 rounded">Trade</button>
                                        <button onClick={() => handleDelete(h.id)} className="text-xs font-bold text-rose-500 hover:text-white transition-colors bg-rose-500/10 py-1.5 rounded flex justify-center items-center"><Trash2 size={14} /></button>
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>

                {/* AI Analysis Sidebar (Right 1/3) */}
                <div className="space-y-6">
                    <div className="bg-gradient-to-b from-primary/10 to-[#0f172a] p-6 rounded-2xl border border-primary/20">
                        <h3 className="text-sm font-black text-primary uppercase tracking-widest mb-4 flex items-center gap-2">
                            <AlertCircle size={16} /> Portfolio Intelligence
                        </h3>
                        <p className="text-sm text-slate-300 mb-6 leading-relaxed">
                            Your portfolio currently holds {holdings.length} assets. The Ensemble AI detects a <strong>bullish structural bias</strong> in your tech holdings, but warns of overweight concentration.
                        </p>
                        <div className="space-y-4">
                            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                                <span className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">Risk Exposure</span>
                                <div className="text-sm text-white font-semibold mt-1">High (Beta: 1.45)</div>
                            </div>
                            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                                <span className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">Diversification Score</span>
                                <div className="text-sm text-rose-400 font-semibold mt-1 flex items-center gap-2">
                                    Low <span className="text-xs font-normal text-slate-500">Consider adding ETFs/Bonds</span>
                                </div>
                            </div>
                        </div>
                        <button className="w-full mt-6 bg-primary/20 hover:bg-primary/30 text-primary transition-colors py-2 rounded-lg text-xs font-bold">
                            Run Deep Rebalance Audit
                        </button>
                    </div>

                    {holdings.length > 0 ? (
                        <div className="bg-[#0f172a] rounded-2xl border border-slate-800 overflow-hidden h-64 relative">
                            <div className="absolute top-4 left-4 z-10 bg-slate-900/80 px-2 py-1 rounded text-[10px] max-w-xs backdrop-blur font-bold uppercase text-slate-400">
                                Top Holding Chart ({holdings[0].symbol})
                            </div>
                            <TradingViewChart symbol={holdings[0].symbol} />
                        </div>
                    ) : (
                        <div className="bg-[#0f172a] rounded-2xl border border-slate-800 p-6 flex items-center justify-center h-64 border-dashed text-slate-500 flex-col gap-2">
                            <Briefcase size={32} className="opacity-50" />
                            <span>Add assets to see charting</span>
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
};

export default PortfolioView;
