import time

print("Checking app.agents.data_agent line by line...")

print("Importing yfinance...", flush=True)
s = time.time()
import yfinance as yf
print(f"  OK ({time.time()-s:.2f}s)")

print("Importing ccxt...", flush=True)
s = time.time()
import ccxt
print(f"  OK ({time.time()-s:.2f}s)")

print("Importing pandas...", flush=True)
s = time.time()
import pandas as pd
print(f"  OK ({time.time()-s:.2f}s)")

print("Done with imports. Instantiating DataAgent code...", flush=True)
s = time.time()
b = ccxt.binance()
print(f"  ccxt.binance() OK ({time.time()-s:.2f}s)")

print("All fine.")
