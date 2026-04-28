import yfinance as yf
import pandas as pd
from datetime import datetime
import time
import json
import os
from position_manager import load_positions, save_positions

# Configuration
CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'NZD', 'CAD', 'CHF']
PAIRS = [
    "EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY",
    "EURGBP", "EURJPY", "EURCAD", "EURCHF", "EURAUD", "EURNZD",
    "GBPJPY", "GBPCAD", "GBPCHF", "GBPAUD", "GBPNZD",
    "AUDJPY", "AUDCAD", "AUDCHF", "AUDNZD",
    "NZDJPY", "NZDCAD", "NZDCHF",
    "CADJPY", "CADCHF", "CHFJPY"
]

def get_strength_val(symbol):
    try:
        time.sleep(0.2)
        ticker = yf.Ticker(symbol)
        df = ticker.history(period='2d')
        if len(df) < 2: return 0
        
        day_high = df['High'].iloc[-2] 
        day_low = df['Low'].iloc[-2]   
        curr_close = df['Close'].iloc[-1] 
        
        if day_high == day_low: return 0
        
        ratio = (curr_close - day_low) / (day_high - day_low)
        
        if ratio >= 0.97: return 9
        elif ratio >= 0.90: return 8
        elif ratio >= 0.75: return 7
        elif ratio >= 0.60: return 6
        elif ratio >= 0.50: return 5
        elif ratio >= 0.40: return 4
        elif ratio >= 0.25: return 3
        elif ratio >= 0.10: return 2
        elif ratio >= 0.03: return 1
        else: return 0
    except Exception:
        return 0

def calculate_powers():
    strengths = {pair: get_strength_val(pair) for pair in PAIRS}
    powers = {curr: 0.0 for curr in CURRENCIES}
    
    def distribute(pair, s):
        base = pair[:3]
        quote = pair[3:]
        if base in powers: powers[base] += s
        if quote in powers: powers[quote] += (9 - s)

    for pair, s in strengths.items():
        distribute(pair, s)
    
    normalized = {curr: val / 7 for curr, val in powers.items()}
    sorted_powers = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
    return sorted_powers, normalized

if __name__ == "__main__":
    sorted_powers, all_powers = calculate_powers()
    print("--- CURRENCY POWERS ---")
    for curr, val in sorted_powers:
        print(f"{curr}: {val:.2f}")
    
    # Check EURNZD specifically
    eur = all_powers.get("EUR", 0)
    nzd = all_powers.get("NZD", 0)
    print(f"\nGap EURNZD: {abs(eur - nzd):.2f}")
    
    # Check GBPJPY
    gbp = all_powers.get("GBP", 0)
    jpy = all_powers.get("JPY", 0)
    print(f"Gap GBPJPY: {abs(gbp - jpy):.2f}")
