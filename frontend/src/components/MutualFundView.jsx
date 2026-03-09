import React, { useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine } from 'recharts';
import { ShieldAlert, Target, TrendingUp, AlertTriangle, CheckCircle, Calculator, BatteryCharging, DollarSign } from 'lucide-react';

const MutualFundView = ({ data }) => {
    const [sipAmount, setSipAmount] = useState(data.sip_projection.monthly_sip);
    const [sipYears, setSipYears] = useState(data.sip_projection.duration_years);

    if (!data || data.error) return null;

    const { metadata, risk_intelligence, predictions, forecast, investor_match, sip_projection } = data;

    const renderForecastChart = () => {
        if (!forecast || !forecast.time_series) return null;

        // Format data for Recharts
        const chartData = forecast.time_series.map((item, i) => {
            // Sample every 7th day for cleaner chart rendering if huge dataset
            if (i % 7 !== 0 && i !== forecast.time_series.length - 1) return null;
            return {
                date: new Date(item.ds).toLocaleDateString(undefined, { month: 'short', year: '2-digit' }),
                Expected: item.yhat,
                upper: item.yhat_upper,
                lower: item.yhat_lower
            };
        }).filter(Boolean);

        return (
            <div className="glass-card" style={{ gridColumn: '1 / -1', height: '400px', display: 'flex', flexDirection: 'column' }}>
                <div className="card-header border-bottom">
                    <TrendingUp size={20} color="var(--accent-base)" />
                    AI NAV Forecast (12 Months)
                </div>
                <div style={{ flex: 1, marginTop: '1rem', position: 'relative' }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorExpected" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="var(--accent-base)" stopOpacity={0.8} />
                                    <stop offset="95%" stopColor="var(--accent-base)" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="colorRange" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="var(--text-secondary)" stopOpacity={0.2} />
                                    <stop offset="95%" stopColor="var(--text-secondary)" stopOpacity={0.05} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
                            <XAxis dataKey="date" stroke="var(--text-muted)" tick={{ fontSize: 12 }} dy={10} />
                            <YAxis stroke="var(--text-muted)" tick={{ fontSize: 12 }} domain={['dataMin - 10', 'dataMax + 10']} />
                            <Tooltip
                                contentStyle={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '8px' }}
                                itemStyle={{ color: 'var(--text-primary)' }}
                                formatter={(value) => `$${value.toFixed(2)}`}
                            />

                            {/* Confidence Band Area */}
                            <Area type="monotone" dataKey="upper" stroke="none" fill="url(#colorRange)" />
                            <Area type="monotone" dataKey="lower" stroke="none" fill="var(--bg-primary)" />

                            {/* Main Expectation Line */}
                            <Area type="monotone" dataKey="Expected" stroke="var(--accent-base)" strokeWidth={3} fill="url(#colorExpected)" />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>
        );
    };

    return (
        <div className="dashboard-grid">

            {/* Overview Card */}
            <div className="glass-card">
                <div className="card-header border-bottom">
                    <div>
                        <h3 style={{ margin: 0, fontSize: '1.25rem' }}>{metadata.name}</h3>
                        <span className="text-muted" style={{ fontSize: '0.875rem' }}>{metadata.category} | ER: {metadata.expense_ratio ? (metadata.expense_ratio * 100).toFixed(2) + '%' : 'N/A'}</span>
                    </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
                    <div>
                        <div className="text-muted" style={{ fontSize: '0.875rem' }}>Current NAV</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>${forecast?.current_nav.toFixed(2)}</div>
                    </div>
                    <div>
                        <div className="text-muted" style={{ fontSize: '0.875rem' }}>Annualized CAGR ({risk_intelligence.years_analyzed.toFixed(1)}Y)</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--success-color)' }}>
                            {risk_intelligence.cagr_pct.toFixed(2)}%
                        </div>
                    </div>
                </div>

                <div style={{ marginTop: '1.5rem' }}>
                    <div className="text-muted" style={{ fontSize: '0.875rem', marginBottom: '0.5rem' }}>AI Investor Match: {investor_match.user_profile} Profile</div>
                    <div className="progress-bg">
                        <div
                            className={`progress-fill ${investor_match.suitability_score_100 > 70 ? 'bg-success' : 'bg-warning'}`}
                            style={{ width: `${investor_match.suitability_score_100}%` }}
                        ></div>
                    </div>
                    {investor_match.warnings.map((w, i) => (
                        <div key={i} className="text-muted" style={{ fontSize: '0.75rem', marginTop: '0.5rem', color: 'var(--warning-color)' }}>
                            <AlertTriangle size={12} style={{ display: 'inline', marginRight: '4px' }} /> {w}
                        </div>
                    ))}
                </div>
            </div>

            {/* Advanced Risk Intelligence */}
            <div className="glass-card">
                <div className="card-header border-bottom">
                    <ShieldAlert size={20} color="var(--warning-color)" />
                    Institutional Risk Metrics
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
                    <div className="flex-between">
                        <span className="text-muted">Volatility Class</span>
                        <span className="badge badge-warning">{risk_intelligence.volatility_class}</span>
                    </div>
                    <div className="flex-between">
                        <span className="text-muted">Sharpe Ratio</span>
                        <span style={{ fontWeight: 'bold', color: risk_intelligence.sharpe_ratio > 1 ? 'var(--success-color)' : 'inherit' }}>
                            {risk_intelligence.sharpe_ratio.toFixed(2)}
                        </span>
                    </div>
                    <div className="flex-between">
                        <span className="text-muted">Sortino Ratio</span>
                        <span style={{ fontWeight: 'bold' }}>{risk_intelligence.sortino_ratio.toFixed(2)}</span>
                    </div>
                    <div className="flex-between">
                        <span className="text-muted">Max Drawdown</span>
                        <span style={{ fontWeight: 'bold', color: 'var(--danger-color)' }}>-{risk_intelligence.max_drawdown_pct.toFixed(2)}%</span>
                    </div>
                    <div className="flex-between border-top" style={{ paddingTop: '0.5rem', marginTop: 'auto' }}>
                        <span className="text-muted">Quant Risk Score</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ fontWeight: 'bold', fontSize: '1.25rem' }}>{risk_intelligence.risk_score_100}/100</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Probability Engine */}
            <div className="glass-card">
                <div className="card-header border-bottom">
                    <Target size={20} color="var(--success-color)" />
                    AI Probability Engine
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
                    <div>
                        <div className="flex-between" style={{ marginBottom: '4px' }}>
                            <span className="text-muted" style={{ fontSize: '0.875rem' }}>Prob. of Positive Return (1Y)</span>
                            <span style={{ fontWeight: 'bold' }}>{predictions.prob_positive_1y}%</span>
                        </div>
                        <div className="progress-bg" style={{ height: '6px' }}><div className="progress-fill bg-success" style={{ width: `${predictions.prob_positive_1y}%` }}></div></div>
                    </div>

                    <div>
                        <div className="flex-between" style={{ marginBottom: '4px' }}>
                            <span className="text-muted" style={{ fontSize: '0.875rem' }}>Prob. Beating Benchmark</span>
                            <span style={{ fontWeight: 'bold' }}>{predictions.prob_beat_benchmark}%</span>
                        </div>
                        <div className="progress-bg" style={{ height: '6px' }}><div className="progress-fill bg-accent" style={{ width: `${predictions.prob_beat_benchmark}%` }}></div></div>
                    </div>

                    <div className="border-top" style={{ paddingTop: '1rem', marginTop: '0.5rem' }}>
                        <div className="text-muted" style={{ fontSize: '0.875rem', marginBottom: '0.5rem' }}>Explainable AI: Key Factors</div>
                        {predictions.explainability.map((factor, i) => (
                            <div key={i} className="flex-between text-muted" style={{ fontSize: '0.875rem', padding: '2px 0' }}>
                                <span>{factor.factor}</span>
                                <span style={{ color: factor.impact.includes('Positive') ? 'var(--success-color)' : 'var(--danger-color)' }}>
                                    {factor.impact}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* SIP Forecaster */}
            <div className="glass-card">
                <div className="card-header border-bottom">
                    <Calculator size={20} color="var(--accent-base)" />
                    SIP Wealth Forecaster
                </div>

                <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div style={{ display: 'flex', gap: '0.5rem', background: 'var(--bg-tertiary)', padding: '0.5rem', borderRadius: '8px', alignItems: 'center' }}>
                        <DollarSign size={16} className="text-muted" />
                        <input
                            type="number"
                            className="search-input"
                            style={{ background: 'transparent', border: 'none', padding: 0, width: '100%' }}
                            value={sipAmount}
                            onChange={(e) => setSipAmount(Number(e.target.value))}
                        />
                        <span className="text-muted">/mo</span>
                    </div>

                    <div className="flex-between">
                        <span className="text-muted">Duration</span>
                        <span>{sipYears} Years</span>
                    </div>
                    <input type="range" min="1" max="25" value={sipYears} onChange={(e) => setSipYears(Number(e.target.value))} style={{ width: '100%', accentColor: 'var(--accent-base)' }} />

                    <div className="border-top flex-between" style={{ paddingTop: '1rem' }}>
                        <span className="text-muted">Future Value (Nominal)</span>
                        <span style={{ fontWeight: 'bold', fontSize: '1.25rem', color: 'var(--success-color)' }}>
                            ${sip_projection.future_value_nominal.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </span>
                    </div>
                    <div className="flex-between">
                        <span className="text-muted" style={{ fontSize: '0.875rem' }}>Inflation Adj (Real Value)</span>
                        <span className="text-muted" style={{ fontSize: '0.875rem' }}>${sip_projection.inflation_adjusted_fv.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                    </div>
                </div>
            </div>

            {/* Time Series Prophet Forecast plotted here */}
            {renderForecastChart()}

        </div>
    );
};

export default MutualFundView;
