import yfinance as yf
import pandas as pd
from datetime import datetime
import time

PAIRS = [
    "EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY",
    "EURGBP", "EURJPY", "EURCAD", "EURCHF", "EURAUD", "EURNZD",
    "GBPJPY", "GBPCAD", "GBPCHF", "GBPAUD", "GBPNZD",
    "AUDJPY", "AUDCAD", "AUDCHF", "AUDNZD",
    "NZDJPY", "NZDCAD", "NZDCHF",
    "CADJPY", "CADCHF", "CHFJPY"
]

def debug_strength(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period='2d')
        if len(df) < 2: return None
        h = df['High'].iloc[-2]
        l = df['Low'].iloc[-2]
        c = df['Close'].iloc[-1]
        ratio = (c - l) / (h - l) if h != l else 0.5
        return {"h": h, "l": l, "c": c, "ratio": ratio}
    except Exception as e:
        return str(e)

print(f"{'Pair':<10} | {'High':<10} | {'Low':<10} | {'Close':<10} | {'Ratio':<10}")
print("-" * 55)
for p in PAIRS:
    res = debug_strength(p)
    if isinstance(res, dict):
        print(f"{p:<10} | {res['h']:<10.5f} | {res['l']:<10.5f} | {res['c']:<10.5f} | {res['ratio']:<10.4f}")
    else:
        print(f"{p:<10} | Error: {res}")
