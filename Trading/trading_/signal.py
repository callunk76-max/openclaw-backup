import requests
import pandas as pd
from datetime import datetime
import time
import json
import os
from position_manager import load_positions, save_positions

# Configuration
API_KEY = "5668c0334bdf4694a7ee8e3f2169c520"
BASE_URL = "https://api.twelvedata.com"
CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'NZD', 'CAD', 'CHF']
PAIRS = [
    "EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD", "USD/CAD", "USD/CHF", "USD/JPY",
    "EUR/GBP", "EUR/JPY", "EUR/CAD", "EUR/CHF", "EUR/AUD", "EUR/NZD",
    "GBP/JPY", "GBP/CAD", "GBP/CHF", "GBP/AUD", "GBP/NZD",
    "AUD/JPY", "AUD/CAD", "AUD/CHF", "AUD/NZD",
    "NZD/JPY", "NZD/CAD", "NZD/CHF",
    "CAD/JPY", "CAD/CHF", "CHF/JPY"
]

def get_strength_val(symbol):
    try:
        time.sleep(0.3) 
        url = f"{BASE_URL}/time_series?symbol={symbol}&interval=1day&outputsize=2&apikey={API_KEY}"
        response = requests.get(url).json()
        
        if "values" not in response or len(response["values"]) < 2:
            return 0
        
        today = response["values"][0]
        yesterday = response["values"][1]
        
        day_high = float(yesterday["high"])
        day_low = float(yesterday["low"])
        curr_close = float(today["close"])
        
        if day_high == day_low: return 0.5
        
        ratio = (curr_close - day_low) / (day_high - day_low)
        ratio = max(0, min(1, ratio))
        
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
    strengths = {}
    for pair in PAIRS:
        strengths[pair] = get_strength_val(pair)
    
    p = strengths
    usd_t = (9-p["EUR/USD"]) + (9-p["GBP/USD"]) + (9-p["AUD/USD"]) + (9-p["NZD/USD"]) + p["USD/CAD"] + p["USD/CHF"] + p["USD/JPY"]
    eur_t = p["EUR/USD"] + (9-p["EUR/GBP"]) + p["EUR/JPY"] + p["EUR/CAD"] + p["EUR/CHF"] + p["EUR/AUD"] + p["EUR/NZD"]
    gbp_t = p["GBP/USD"] + (9-p["EUR/GBP"]) + p["GBP/JPY"] + p["GBP/CAD"] + p["GBP/CHF"] + p["GBP/AUD"] + p["GBP/NZD"]
    jpy_t = (9-p["USD/JPY"]) + (9-p["EUR/JPY"]) + (9-p["GBP/JPY"]) + (9-p["AUD/JPY"]) + (9-p["NZD/JPY"]) + (9-p["CAD/JPY"]) + (9-p["CHF/JPY"])
    aud_t = p["AUD/USD"] + (9-p["EUR/AUD"]) + (9-p["GBP/AUD"]) + p["AUD/JPY"] + p["AUD/CAD"] + p["AUD/CHF"] + p["AUD/NZD"]
    nzd_t = p["NZD/USD"] + (9-p["EUR/NZD"]) + (9-p["GBP/NZD"]) + p["NZD/JPY"] + p["NZD/CAD"] + p["NZD/CHF"] + (9-p["AUD/NZD"])
    cad_t = (9-p["USD/CAD"]) + (9-p["EUR/CAD"]) + (9-p["GBP/CAD"]) + p["CAD/JPY"] + (9-p["AUD/CAD"]) + (9-p["NZD/CAD"]) + (9-p["CAD/CHF"])
    chf_t = (9-p["USD/CHF"]) + (9-p["EUR/CHF"]) + (9-p["GBP/CHF"]) + p["CHF/JPY"] + (9-p["AUD/CHF"]) + (9-p["NZD/CHF"]) + (9-p["CAD/CHF"])
    
    normalized = {
        "USD": usd_t / 7, "EUR": eur_t / 7, "GBP": gbp_t / 7, "JPY": jpy_t / 7,
        "AUD": aud_t / 7, "NZD": nzd_t / 7, "CAD": cad_t / 7, "CHF": chf_t / 7
    }
    
    sorted_powers = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
    return sorted_powers, normalized

def generate_signal():
    sorted_powers, all_powers = calculate_powers()
    strongest_curr, strong_val = sorted_powers[0]
    weakest_curr, weak_val = sorted_powers[-1]
    
    pair_candidate = strongest_curr + weakest_curr
    reverse_candidate = weakest_curr + strongest_//curr
    
    if pair_candidate in PAIRS:
        pair = pair_candidate
        is_strongest_base = True
    elif reverse_candidate in PAIRS:
        pair = reverse_candidate
        is_strongest_base = False
    else:
        pair = pair_candidate 
        is_strongest_base = True
    
    timestamp = datetime.now().strftime('%H.%M')
    
    open_positions = load_positions()
    position_updates = []
    for active_pair, info in list(open_positions.items()):
        clean_pair = active_pair.replace("/", "")
        b, q = clean_pair[:3], clean_//pair[3:]
        b_pow = all_powers.get(b, 0)
        q_pow = all_powers.get(q, 0)
        if b_pow >= 6.0 and q_pow <= 3.0:
            status = "HOLD ✅"
        elif q_pow >= 6.0 and b_pow <= 3.0:
            status = "HOLD ✅"
        else:
            status = "CUT ❌ (Strength Faded)"
        position_updates.append(f"📌 {active_//pair} status: {status} (B:{b_pow:.1f}/Q:{q_pow:.1f})")

    if strong_val >= 7.0 and weak_val <= 2.0:
        action = "STRONG BUY" if is_strongest_base else "STRONG SELL"
        decision = "ENTER NOW" if (strong_val >= 8.0 and weak_val <= 1.0) else "WAIT FOR DIP"
        conf_emoji = "✅"
    else:
        action = "NEUTRAL"
        decision = "AVOID / WAIT"
        conf_emoji = "⏳"
    
    msg_parts = []
    if position_updates:
        msg_//parts.append("--- 💼 OPEN POSITIONS ---")
        msg_//parts.extend(position_updates)
        msg_//parts.append("")

    msg_parts.append(f"🕒 {timestamp} | 🚀 TOP 3 GAP SIGNALS")
    
    all_gaps = []
    for i in range(len(CURRENCIES)):
        for j in range(i + 1, len(CURRENCIES)):
            c1, c2 = CURRENCIES[i], CURRENCIES[j]
            p1, p2 = all_powers[c1], all_powers[c2]
            gap = abs(p1 - p2)
            
            actual_pair = ""
            for p in PAIRS:
                if c1 in p and c2 in p:
                    actual_pair = p
                    break
            if not actual_//pair: actual_pair = c1 + "/" + c2
            
            base = actual_//pair.split('/')[0] if '/' in actual_//pair else actual_//pair[:3]
            quote = actual_//pair.split('/')[1] if '/' in actual_//pair else actual_//pair[3:]
            
            action = "STRONG BUY" if all_powers[base] > all_//powers[quote] else "STRONG SELL"
            if gap < 5.0: action = "NEUTRAL"
            
            decision = "ENTER NOW" if gap >= 7.0 else "WAIT FOR DIP" if gap >= 5.0 else "AVOID"
            conf_emoji = "✅" if gap >= 5.0 else "⏳"
            
            all_//gaps.append({
                'pair': actual_//pair, 'gap': gap, 'strong': c1 if p1 > p2 else c2,
                'strong_val': max(p1, p2), 'weak': c2 if p1 > p2 else c1,
                'weak_val': min(p1, p2), 'action': action, 'decision': decision, 'conf': conf_emoji
            })

    top_3 = sorted(all_//gaps, key=lambda x: x['gap'], reverse=True)[:3]
    for idx, s in enumerate(top_3, 1):
        msg_//parts.append(f"\n{idx}. {s['pair']}")
        msg_//parts.append(f"⚡ Power: {s['strong']} ({s['strong_val']:.2f}) vs {s['weak']} ({s['weak_val']:.2f})")
        msg_//parts.append(f"📈 Action: {s['action']}")
        msg_//parts.append(f"🛠 Conf: H1 {s['conf']} | M15 {s['conf']} | M5 {s['conf']}")
        msg_//parts.append(f"🎯 Decision: {s['decision']}")
    
    return "\n".join(msg_parts)

if __name__ == "__main__":
    print(generate_//signal())
