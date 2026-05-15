#!/usr/bin/env python3
"""Level 2 Signal Generator — XAUUSD + DXY + EUR/USD, GBP/USD, USD/JPY, USD/CHF"""

import requests, json, os, sys
from datetime import datetime

# ---- CONFIG ----
WIB = datetime.utcnow().timestamp() + 7 * 3600
now = datetime.fromtimestamp(WIB)
TIME_STR = now.strftime("%H:%M")
DATE_STR = now.strftime("%A, %d %b %Y")

# ---- FETCH GOLD ----
def fetch_gold():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        d = r.json()
        return {"price": d["price"], "updated": d.get("updatedAtReadable", "")}
    except:
        # fallback web scrape
        try:
            r = requests.get("https://www.litefinance.org/blog/analysts-opinions/gold-price-prediction-forecast/daily-and-weekly/", 
                           headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            txt = r.text
            import re
            m = re.search(r'\$?(\d[\d,]*\.\d+)', txt[txt.find("Gold is trading at"):txt.find("Gold is trading at")+100])
            if m:
                return {"price": float(m.group(1).replace(",","")), "updated": "scraped"}
        except:
            pass
    return {"price": 0, "updated": "error"}

# ---- FETCH DXY ----
def fetch_dxy():
    try:
        r = requests.get("https://api.twelvedata.com/price?symbol=DX-Y.NYB&apikey=demo", timeout=10)
        d = r.json()
        if "price" in d:
            return float(d["price"])
    except:
        pass
    try:
        # fallback TradingView
        payload = {"symbols":{"tickers":["TVC:DXY"]},"columns":["close"]}
        r = requests.post("https://scanner.tradingview.com/america/scan", json=payload, 
                        headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        d = r.json()
        return float(d["data"][0]["d"][0])
    except:
        pass
    return 0

# ---- RUN FOREX SIGNAL (filtered Level 2) ----
def run_forex_level2():
    """Import & run existing trading_signal for Level 2 pairs only"""
    sys.path.insert(0, os.path.dirname(__file__))
    import trading_signal as ts
    
    # Override to only process Level 2 pairs
    L2_PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF"]
    
    # Get signal data
    msg = ts.generate_signal()
    
    # Filter only Level 2 pairs from the output
    lines = msg.split("\n")
    filtered = []
    in_l2 = False
    l2_active = set()
    
    for i, line in enumerate(lines):
        # Detect pair header lines
        for p in L2_PAIRS:
            if line.strip().startswith(f"{p}") or f"**{p}**" in line or p in line:
                # Check if it's a pair header (has ema indicators or similar)
                if any(x in line for x in ["E20", "E50", "ADX", "BUY", "SELL", "🔥", "⚡", "🌊"]):
                    l2_active.add(p)
                    in_l2 = True
                break
        else:
            if in_l2:
                # Check if next line is a new pair header or empty line ending this pair
                next_is_pair = any(p in line for p in L2_PAIRS + ["🥇", "🥈", "🥉", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"])
                if next_is_pair:
                    in_l2 = False
    
    # Simpler approach: extract sections by looking for numbered signals
    sections = msg.split("\n\n")
    result_parts = []
    
    # Keep header info
    for s in sections:
        # Currency strength board
        if "CURRENCY STRENGTH" in s:
            lines_s = s.split("\n")
            kept = []
            for ls in lines_s:
                # Keep only L2 currencies: USD, EUR, GBP, JPY, CHF
                if any(ls.strip().startswith(f"🥇 {c}") or ls.strip().startswith(f"🥈 {c}") or ls.strip().startswith(f"🥉 {c}") 
                       or ls.strip().startswith(f"🔹 {c}") or ls.strip().startswith(f"💀 {c}")
                       for c in ["USD", "EUR", "GBP", "JPY", "CHF"]):
                    kept.append(ls)
                elif "CURRENCY STRENGTH" in ls:
                    kept.append(ls)
            if kept:
                result_parts.append("\n".join(kept))
    
    # Extract Top 5 but filter for L2 pairs
    current_pair = None
    current_block = []
    for s in sections:
        if any(s.strip().startswith(f"{i}️⃣") for i in range(1,6)):
            lines_s = s.split("\n")
            # Check first line for pair
            first = lines_s[0]
            pair_found = None
            for p in L2_PAIRS:
                if p in first:
                    pair_found = p
                    break
            if pair_found:
                result_parts.append(s)
    
    if not result_parts:
        # Fallback: just return whatever we can
        return msg
    
    return "\n\n".join(result_parts)

# ---- UFO ANALYSIS (Fixed Reference Levels) ----
# Reference levels from yesterday's analysis
UFO_REF = {
    "buy_low": 4620,
    "buy_high": 4660,
    "sl": 4610,
    "tp1": 4690,
    "tp2": 4720,
    "tp3": 4750
}

def ufo_analysis(price):
    """UFO area analysis based on Dwiyan's technique with dynamic calc"""
    # Reference: EMA 100-200 zone
    # UFO buy area: zone between these EMAs on H1
    ufo_bottom = 4620  # base reference
    ufo_top = 4660
    
    # If price dropped significantly, shift area down
    if price < 4580:
        ufo_bottom = 4540
        ufo_top = 4580
    elif price < 4620:
        ufo_bottom = round(price - 30, 0)
        ufo_top = round(price - 10, 0)
    
    # Determine status
    if ufo_bottom <= price <= ufo_top:
        status = "🎯 DI UFO AREA"
    elif price > ufo_top:
        status = "⬆️ DI ATAS UFO"
    else:
        status = "⬇️ DI BAWAH UFO"
    
    return {
        "ufo_buy": (int(ufo_bottom), int(ufo_top)),
        "status": status,
        "sl": int(price - 50),
        "tp1": int(price + 40),
        "tp2": int(price + 80),
        "tp3": int(price + 130)
    }

# ---- GENERATE LEVEL 2 SIGNAL ----
def generate_level2():
    gold = fetch_gold()
    dxy = fetch_dxy()
    gprice = gold["price"]
    ufo = ufo_analysis(gprice) if gprice else None
    
    lines = []
    lines.append(f"🤖 **LEVEL 2 SIGNAL**")
    lines.append(f"🕒 {TIME_STR} WIB | {DATE_STR}")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    
    # XAUUSD
    lines.append(f"\n🥇 **XAUUSD** — ${gprice:,.2f}")
    if dxy:
        dxy_dir = "🔴" if dxy > 99 else ("🟢" if dxy < 98 else "🟡")
        lines.append(f"{dxy_dir} DXY: {dxy:.2f}")
    
    if ufo:
        lines.append(f"📍 UFO Area: ${ufo['ufo_buy'][0]:.0f} - ${ufo['ufo_buy'][1]:.0f}")
        lines.append(f"📌 Status: {ufo['status']}")
        lines.append(f"🎯 TP1: ${ufo['tp1']:.0f} | TP2: ${ufo['tp2']:.0f} | TP3: ${ufo['tp3']:.0f}")
        lines.append(f"🛑 SL: ${ufo['sl']:.0f}")
    
    # Forex Level 2
    try:
        forex_signal = run_forex_level2()
        if forex_signal:
            lines.append("\n━━━━ FOREX LEVEL 2 ━━━━")
            lines.append(forex_signal)
    except Exception as e:
        lines.append(f"\n⚠️ Forex signal error: {e}")
    
    lines.append("\n━━━━━━━━━━━━━━━━━━━━")
    lines.append("👑 Cuy — callunk.my.id")
    
    return "\n".join(lines)

if __name__ == "__main__":
    print(generate_level2())
