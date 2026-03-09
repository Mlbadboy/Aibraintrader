import React, { useState } from 'react';

const SIPPlannerView = () => {
    const [targetAmount, setTargetAmount] = useState(2500000);
    const [monthlySIP, setMonthlySIP] = useState(5000);
    const [duration, setDuration] = useState(15);
    const [goalType, setGoalType] = useState('Retirement');

    return (
        <div className="p-8 grid grid-cols-12 gap-8">
            <div className="col-span-12 lg:col-span-4 space-y-6">
                <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-6 shadow-sm">
                    <h3 className="text-lg font-bold mb-6 flex items-center gap-2">
                        <span className="material-symbols-outlined text-primary">target</span>
                        Goal Configuration
                    </h3>
                    <form className="space-y-5" onSubmit={(e) => e.preventDefault()}>
                        <div>
                            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">What are you planning for?</label>
                            <div className="grid grid-cols-2 gap-2">
                                {['Retirement', 'Home', 'Education', 'Custom'].map((type) => (
                                    <button
                                        key={type}
                                        onClick={() => setGoalType(type)}
                                        className={`p-3 border-2 rounded-lg text-sm font-bold flex flex-col items-center gap-1 transition-all ${goalType === type ? 'border-primary bg-primary/20 text-white' : 'border-slate-800 text-slate-400 hover:border-primary hover:text-white'}`}
                                        type="button"
                                    >
                                        <span className="material-symbols-outlined">
                                            {type === 'Retirement' ? 'blind' : type === 'Home' ? 'home' : type === 'Education' ? 'school' : 'more_horiz'}
                                        </span>
                                        {type}
                                    </button>
                                ))}
                            </div>
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Target Amount</label>
                            <div className="relative">
                                <span className="absolute left-3 top-1/2 -translate-y-1/2 font-bold text-slate-400">$</span>
                                <input
                                    className="w-full bg-slate-900 border-slate-800 rounded-lg pl-8 py-2.5 font-bold text-white focus:outline-none focus:border-primary"
                                    type="number"
                                    value={targetAmount}
                                    onChange={(e) => setTargetAmount(e.target.value)}
                                />
                            </div>
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Monthly Investment (SIP)</label>
                            <div className="relative">
                                <span className="absolute left-3 top-1/2 -translate-y-1/2 font-bold text-slate-400">$</span>
                                <input
                                    className="w-full bg-slate-900 border-slate-800 rounded-lg pl-8 py-2.5 font-bold text-white focus:outline-none focus:border-primary"
                                    type="number"
                                    value={monthlySIP}
                                    onChange={(e) => setMonthlySIP(e.target.value)}
                                />
                            </div>
                        </div>
                        <div>
                            <div className="flex justify-between mb-2">
                                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider">Duration (Years)</label>
                                <span className="text-xs font-bold text-primary">{duration} Years</span>
                            </div>
                            <input
                                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-primary"
                                max="40" min="1" type="range"
                                value={duration}
                                onChange={(e) => setDuration(e.target.value)}
                            />
                        </div>
                        <button className="w-full py-3 bg-primary text-white font-bold rounded-lg shadow-lg shadow-primary/30 hover:bg-primary/90 transition-all flex items-center justify-center gap-2">
                            <span className="material-symbols-outlined">calculate</span>
                            Recalculate Projections
                        </button>
                    </form>
                </div>
                <div className="bg-gradient-to-br from-slate-900 to-primary/40 p-[1px] rounded-xl shadow-xl overflow-hidden">
                    <div className="bg-slate-900 p-5 rounded-[11px] space-y-4">
                        <div className="flex items-center gap-2">
                            <span className="material-symbols-outlined text-primary">psychology</span>
                            <h3 className="text-white font-bold text-sm uppercase tracking-widest">AI Optimizer</h3>
                        </div>
                        <div className="bg-white/5 border border-white/10 p-4 rounded-lg">
                            <p className="text-white text-xs font-semibold mb-3">Suggested Fund Mix for 92% Probability:</p>
                            <div className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <span className="text-slate-400 text-xs font-medium">Aggressive Growth</span>
                                    <span className="text-emerald-accent text-xs font-bold">65%</span>
                                </div>
                                <div className="w-full h-1 bg-white/10 rounded-full">
                                    <div className="h-full bg-emerald-accent rounded-full" style={{ width: '65%' }}></div>
                                </div>
                                <div className="flex items-center justify-between">
                                    <span className="text-slate-400 text-xs font-medium">Global Bluechips</span>
                                    <span className="text-primary text-xs font-bold">25%</span>
                                </div>
                                <div className="w-full h-1 bg-white/10 rounded-full">
                                    <div className="h-full bg-primary rounded-full" style={{ width: '25%' }}></div>
                                </div>
                                <div className="flex items-center justify-between">
                                    <span className="text-slate-400 text-xs font-medium">Hedging Assets</span>
                                    <span className="text-yellow-500 text-xs font-bold">10%</span>
                                </div>
                                <div className="w-full h-1 bg-white/10 rounded-full">
                                    <div className="h-full bg-yellow-500 rounded-full" style={{ width: '10%' }}></div>
                                </div>
                            </div>
                        </div>
                        <button className="w-full py-2.5 text-xs font-bold text-white bg-white/10 border border-white/20 rounded-lg hover:bg-white/20 transition-colors">
                            Apply Strategy
                        </button>
                    </div>
                </div>
            </div>
            <div className="col-span-12 lg:col-span-8 space-y-8">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-6 flex flex-col items-center text-center">
                        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Goal Success Probability</h3>
                        <div className="relative size-40">
                            <div className="w-full h-full rounded-full" style={{
                                background: 'conic-gradient(from 180deg at 50% 100%, #10b981 0deg, #10b981 120deg, #f59e0b 140deg, #ef4444 180deg)',
                                mask: 'radial-gradient(farthest-side, transparent 75%, white 76%)',
                                WebkitMask: 'radial-gradient(farthest-side, transparent 75%, white 76%)'
                            }}></div>
                            <div className="absolute inset-2 bg-[#0f172a] rounded-full flex flex-col items-center justify-center">
                                <span className="text-3xl font-black text-white leading-none">84%</span>
                                <span className="text-[10px] font-bold text-emerald-accent uppercase tracking-tighter mt-1">Highly Likely</span>
                            </div>
                            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-4 bg-white rounded-full border-4 border-slate-800 shadow-lg"></div>
                        </div>
                        <p className="mt-4 text-xs text-slate-500 max-w-[200px]">Based on current market volatility and AI forecasted returns.</p>
                    </div>
                    <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-6 grid grid-cols-1 gap-4">
                        <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-800">
                            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Total Invested</p>
                            <h4 className="text-xl font-bold text-white">${(monthlySIP * duration * 12).toLocaleString()}</h4>
                        </div>
                        <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-800">
                            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Estimated Wealth Gain</p>
                            <h4 className="text-xl font-bold text-emerald-accent">+$1,600,000</h4>
                        </div>
                        <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-800">
                            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Corpus at Maturity</p>
                            <h4 className="text-xl font-bold text-primary">${targetAmount.toLocaleString()}</h4>
                        </div>
                    </div>
                </div>
                <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-8">
                    <div className="flex items-center justify-between mb-8">
                        <div>
                            <h3 className="text-lg font-bold text-white">Projected Wealth Accumulation</h3>
                            <p className="text-sm text-slate-500">Wealth growth curve with 12.5% CAGR assumption</p>
                        </div>
                        <div className="flex items-center gap-3">
                            <div className="flex items-center gap-1.5">
                                <div className="size-3 rounded-full bg-primary"></div>
                                <span className="text-xs font-bold text-slate-400 uppercase">Growth</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                                <div className="size-3 rounded-full bg-slate-300 dark:bg-slate-700"></div>
                                <span className="text-xs font-bold text-slate-400 uppercase">Principal</span>
                            </div>
                        </div>
                    </div>
                    <div className="h-[300px] w-full relative">
                        <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 1000 300">
                            <defs>
                                <linearGradient id="chart-poly-grad" x1="0" x2="0" y1="0" y2="1">
                                    <stop offset="0%" stopColor="#136dec" stopOpacity="0.3"></stop>
                                    <stop offset="100%" stopColor="#136dec" stopOpacity="0"></stop>
                                </linearGradient>
                            </defs>
                            <path d="M0 280 L 1000 150" fill="none" stroke="#475569" strokeDasharray="8" strokeWidth="2"></path>
                            <path fill="url(#chart-poly-grad)" d="M0 280 Q 250 270, 500 200 T 750 120 T 1000 40 V 300 H 0 Z"></path>
                            <path d="M0 280 Q 250 270, 500 200 T 750 120 T 1000 40" fill="none" stroke="#136dec" strokeWidth="4"></path>
                        </svg>
                        <div className="flex justify-between mt-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                            <span>Year 0</span>
                            <span>Year {Math.round(duration / 5)}</span>
                            <span>Year {Math.round(duration / 5 * 2)}</span>
                            <span>Year {Math.round(duration / 5 * 3)}</span>
                            <span>Year {Math.round(duration / 5 * 4)}</span>
                            <span>Year {duration}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SIPPlannerView;
