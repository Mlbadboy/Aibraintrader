import React from 'react';
import { ShieldAlert, Crosshair, DollarSign, Target, RefreshCw } from 'lucide-react';
import { formatCurrency } from '../utils/formatters';
const RiskCard = ({ data, onRefresh }) => {
    if (!data || !data.risk_assessment) return null;

    const risk = data.risk_assessment;
    const isHold = risk.approved_action === 'HOLD';

    if (isHold) {
        return (
            <div className="glass-card">
                <div className="card-header flex-between">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><ShieldAlert size={20} /> Risk Guardian</div>
                    {onRefresh && (
                        <button onClick={onRefresh} className="search-button hover:text-white transition-colors" style={{ padding: '0.25rem', background: 'transparent', color: 'var(--text-secondary)' }} title="Refresh Live Guardian Data">
                            <RefreshCw size={14} />
                        </button>
                    )}
                </div>
                <div className="empty-state" style={{ height: 'auto', padding: '2rem 0' }}>
                    <ShieldAlert size={48} className="empty-icon" />
                    <p>Trade Vetoed or Market is Flat.</p>
                    <p className="text-sm">No position sizing or stops generated.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="glass-card">
            <div className="card-header flex-between">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><ShieldAlert size={20} /> Risk Guardian</div>
                {onRefresh && (
                    <button onClick={onRefresh} className="search-button hover:text-white transition-colors" style={{ padding: '0.25rem', background: 'transparent', color: 'var(--text-secondary)' }} title="Refresh Live Guardian Data">
                        <RefreshCw size={14} />
                    </button>
                )}
            </div>

            <div className="risk-grid">
                <div className="risk-item">
                    <div className="risk-label">
                        <DollarSign size={16} /> Max Risk (USD)
                    </div>
                    <div className="risk-value">
                        {formatCurrency(risk.risk_amount_usd, data.symbol || '')}
                    </div>
                </div>

                <div className="risk-item">
                    <div className="risk-label">
                        Position Size
                    </div>
                    <div style={{ textAlign: 'right' }}>
                        <div className="risk-value">{formatCurrency(risk.position_size_usd, data.symbol || '')}</div>
                        <div className="text-sm text-muted">{risk.position_size_units} shares/coins</div>
                    </div>
                </div>

                <div className="risk-item" style={{ borderLeft: '4px solid var(--accent-base)' }}>
                    <div className="risk-label">
                        <Crosshair size={16} /> Entry Price
                    </div>
                    <div className="risk-value">
                        {formatCurrency(risk.entry_price, data.symbol || '')}
                    </div>
                </div>

                <div className="risk-item" style={{ borderLeft: '4px solid var(--danger-color)' }}>
                    <div className="risk-label">
                        Stop Loss
                    </div>
                    <div className="risk-value">
                        {formatCurrency(risk.stop_loss, data.symbol || '')}
                    </div>
                </div>

                <div className="risk-item" style={{ borderLeft: '4px solid var(--success-color)' }}>
                    <div className="risk-label">
                        <Target size={16} /> Take Profit
                    </div>
                    <div className="risk-value">
                        {formatCurrency(risk.take_profit, data.symbol || '')}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RiskCard;
