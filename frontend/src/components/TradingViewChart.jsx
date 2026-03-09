import React, { useEffect, useRef } from 'react';

const TradingViewChart = ({ symbol, theme = 'dark' }) => {
    const container = useRef();

    useEffect(() => {
        // Clear previous widget
        if (container.current) {
            container.current.innerHTML = '';
        }

        const formatTVSymbol = (sym) => {
            if (!sym) return "SPY";
            const s = sym.toUpperCase();
            // Handle explicit prefixes already set by backend
            if (s.includes(':')) return s;
            // Handle Indian symbols with suffixes - prioritize BSE for free widget compatibility
            if (s.endsWith('.NS')) return `BSE:${s.split('.')[0]}`;
            if (s.endsWith('.BO')) return `BSE:${s.split('.')[0]}`;
            // Handle NIFTY/SENSEX indices if naked
            if (s === 'NIFTY') return "NSE:NIFTY"; // Indices usually require their home exchange
            if (s === 'SENSEX') return "BSE:SENSEX";
            return s;
        };

        const script = document.createElement("script");
        script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
        script.type = "text/javascript";
        script.async = true;

        script.innerHTML = JSON.stringify({
            "autosize": true,
            "symbol": formatTVSymbol(symbol),
            "interval": "D",
            "timezone": "Etc/UTC",
            "theme": theme,
            "style": "1",
            "locale": "en",
            "enable_publishing": false,
            "allow_symbol_change": true,
            "calendar": false,
            "support_host": "https://www.tradingview.com"
        });

        container.current.appendChild(script);
    }, [symbol, theme]);

    return (
        <div className="tradingview-widget-container h-full w-full rounded-2xl overflow-hidden border border-slate-800 shadow-2xl" ref={container}>
            <div className="tradingview-widget-container__widget h-full w-full"></div>
        </div>
    );
};

export default TradingViewChart;
