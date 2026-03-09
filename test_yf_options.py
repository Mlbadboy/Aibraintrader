import yfinance as yf
import traceback

print("Starting yf test for Indian indices...")
for sym in ["^NSEI", "AAPL"]:
    print(f"\n--- Testing Options for {sym} ---")
    try:
        t = yf.Ticker(sym)
        print("Fetching options expiries...")
        # For some Indian tickers, this property call hangs waiting for Yahoo Finance data that doesn't exist.
        exp = t.options
        print(f"Expiries: {exp}")
        if exp:
            c = t.option_chain(exp[0])
            print(f"Calls found: {len(c.calls)}")
            print(f"Puts found: {len(c.puts)}")
        else:
            print("No expiries found.")
    except Exception as e:
        print(f"Error fetching options for {sym}:")
        traceback.print_exc()
print("Done.")
