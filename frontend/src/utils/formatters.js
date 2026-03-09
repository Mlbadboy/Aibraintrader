// Utility functions for formatting data in the frontend

/**
 * Formats a given price based on the asset symbol.
 * Indian assets (.NS, .BO, NIFTY) will be formatted with ₹.
 * All other assets will default to $.
 * 
 * @param {number} price - The price to format
 * @param {string} symbol - The ticker symbol (e.g., 'AAPL', 'RELIANCE.NS')
 * @returns {string} The formatted currency string
 */
export const formatCurrency = (price, symbol) => {
    if (price === undefined || price === null || isNaN(price)) return 'N/A';

    // Safety check for symbol
    const safeSymbol = symbol ? String(symbol).toUpperCase() : '';

    // Check if Indian asset
    const isIndian = safeSymbol.endsWith('.NS') ||
        safeSymbol.endsWith('.BO') ||
        safeSymbol.includes('NIFTY') ||
        safeSymbol.includes('SENSEX') ||
        safeSymbol.includes('BANKNIFTY');

    if (isIndian) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(price);
    }

    // Default USD formatting
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(price);
};
