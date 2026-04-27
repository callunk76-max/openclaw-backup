import requests
from datetime import datetime
import time
from position_manager import load_positions

# Configuration
CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'NZD', 'CAD', 'CHF']
PAIRS = [
    "EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD", "USD/CAD", "USD/CHF", "USD/JPY",
    "EUR/GBP", "EUR/JPY", "EUR/CAD", "EUR/CHF", "EUR/AUD", "EUR/NZD",
    "GBP/JPY", "GBP/CAD", "GBP/CHF", "GBP/AUD", "GBP/NZD",
    "AUD/JPY", "AUD/CAD", "AUD/CHF", "AUD/NZD",
    "NZD/JPY", "NZD/CAD", "NZD/CHF",
    "CAD/JPY", "CAD/CHF", "CHF/JPY"
]

def get_all_strengths():
    try:
        # Format for TradingView Scanner API (OANDA broker)
        tickers = [f"OANDA:{p.replace('/', '')}" for p in PAIRS]
        
        payload = {
            "symbols": {"tickers": tickers},
            "columns": ["close", "high[1]", "low[1]"] # Current close, yesterday's high, yesterday's low
        }
        
        url = "https://scanner.tradingview.com/forex/scan"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.post(url, json=payload, headers=headers).json()
        
        strengths = {}
        for row in response.get("data", []):
            symbol = row["s"].replace("OANDA:", "")
            pair = f"{symbol[:3]}/{symbol[3:]}"
            
            c = float(row["d"][0])
            h = float(row["d"][1])
            l = float(row["d"][2])
            
            if h == l:
                strengths[pair] = 0
                continue
                
            # Callunk / Giraia ratio logic
            ratio = (c - l) / (h - l)
            ratio = max(0, min(1, ratio))
            
            if ratio >= 0.97: strengths[pair] = 9
            elif ratio >= 0.90: strengths[pair] = 8
            elif ratio >= 0.75: strengths[pair] = 7
            elif ratio >= 0.60: strengths[pair] = 6
            elif ratio >= 0.50: strengths[pair] = 5
            elif ratio >= 0.40: strengths[pair] = 4
            elif ratio >= 0.25: strengths[pair] = 3
            elif ratio >= 0.10: strengths[pair] = 2
            elif ratio >= 0.03: strengths[pair] = 1
            else: strengths[pair] = 0
            
        return strengths
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {pair: 0 for pair in PAIRS}

def calculate_powers():
    pair_strengths = get_all_strengths()
    
    currency_sums = {c: 0 for c in CURRENCIES}
    
    for pair, score in pair_strengths.items():
        base, quote = pair.split('/')
        currency_sums[base] += score
        currency_sums[quote] += (9 - score)
        
    # Average them
    normalized = {c: val / 7 for c, val in currency_sums.items()}
    sorted_powers = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
    
    return sorted_powers, normalized

def get_decision_label(gap):
    if gap >= 7.0: return "ENTER NOW 🔥", "✅"
    elif gap >= 5.0: return "WAIT FOR DIP ⏳", "☑️"
    elif gap >= 4.0: return "WATCH CLOSELY 👀", "⚠️"
    else: return "AVOID / CHOPPY ❌", "🛑"

def generate_signal():
    sorted_powers, all_powers = calculate_powers()
    
    timestamp = datetime.now().strftime('%H:%M')
    
    # 1. Analyze Open Positions
    open_positions = load_positions()
    position_updates = []
    for active_pair, info in list(open_positions.items()):
        # Handle cases where slash is missing or present
        if '/' not in active_pair:
            b, q = active_pair[:3], active_pair[3:]
        else:
            b, q = active_pair.split('/')
            
        b_pow = all_powers.get(b, 0)
        q_pow = all_powers.get(q, 0)
        gap = abs(b_pow - q_pow)
        
        trade_type = info.get("type", "BUY").upper()
        
        # New Directional Logic
        if trade_type == "BUY":
            if b_pow > q_pow:
                if gap >= 4.0: status = "HOLD ✅"
                elif gap >= 2.0: status = "WATCH ⚠️ (Weakening)"
                else: status = "CUT ✂️ (Gap too close)"
            else:
                status = "CUT ❌ (Trend Reversed)"
                
        elif trade_type == "SELL":
            if q_pow > b_pow:
                if gap >= 4.0: status = "HOLD ✅"
                elif gap >= 2.0: status = "WATCH ⚠️ (Weakening)"
                else: status = "CUT ✂️ (Gap too close)"
            else:
                status = "CUT ❌ (Trend Reversed)"
                
        position_updates.append(f"📌 {active_pair} [{trade_type}] : {status}\n   └ Power: {b} ({b_pow:.2f}) vs {q} ({q_pow:.2f}) | Gap: {gap:.2f}")

    # 2. Generate Gap combinations
    all_gaps = []
    for i in range(len(CURRENCIES)):
        for j in range(i + 1, len(CURRENCIES)):
            c1, c2 = CURRENCIES[i], CURRENCIES[j]
            p1, p2 = all_powers[c1], all_powers[c2]
            gap = abs(p1 - p2)
            
            # Find matching pair
            actual_pair = ""
            for p in PAIRS:
                if c1 in p and c2 in p:
                    actual_pair = p
                    break
            
            # If pair exists
            if actual_pair:
                base = actual_pair.split('/')[0]
                quote = actual_pair.split('/')[1]
                
                is_buy = all_powers[base] > all_powers[quote]
                action = "🟢 STRONG BUY ⬆️" if is_buy else "🔴 STRONG SELL ⬇️"
                if gap < 4.0: 
                    action = "⚪ NEUTRAL ↔️"
                
                decision, conf_emoji = get_decision_label(gap)
                
                all_gaps.append({
                    'pair': actual_pair, 
                    'gap': gap, 
                    'base_val': all_powers[base],
                    'quote_val': all_powers[quote],
                    'action': action, 
                    'decision': decision, 
                    'conf': conf_emoji
                })

    top_3 = sorted(all_gaps, key=lambda x: x['gap'], reverse=True)[:3]
    
    # ---------------- BUILD MESSAGE ---------------- #
    msg_parts = []
    msg_parts.append(f"🤖 **CALLUNK AI TRADING AGENT**")
    msg_parts.append(f"🕒 {timestamp} (GMT+8) | Data: D1 (Real-time)")
    msg_parts.append(f"〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️")
    
    # Board
    msg_parts.append(f"📊 **CURRENCY STRENGTH BOARD**")
    for i, (curr, val) in enumerate(sorted_powers):
        if i == 0: emoji = "🥇"
        elif i == 1: emoji = "🥈"
        elif i == 2: emoji = "🥉"
        elif i == len(sorted_powers) - 1: emoji = "💀"
        else: emoji = "🔹"
        msg_parts.append(f"{emoji} {curr} : {val:.2f}")
    
    msg_parts.append(f"〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️")
    
    # Open Positions
    if position_updates:
        msg_parts.append("💼 **OPEN POSITIONS MANAGER**")
        msg_parts.extend(position_updates)
        msg_parts.append(f"〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️")

    # Top 3
    msg_parts.append(f"🎯 **TOP 3 TRADING OPPORTUNITIES**")
    for idx, s in enumerate(top_3, 1):
        base, quote = s['pair'].split('/')
        
        msg_parts.append(f"{idx}️⃣ **{s['pair']}**")
        msg_parts.append(f"⚡ Power : {base} ({s['base_val']:.2f}) vs {quote} ({s['quote_val']:.2f})")
        msg_parts.append(f"📉 Gap   : {s['gap']:.2f} Pts")
        msg_parts.append(f"📈 Action: {s['action']}")
        msg_parts.append(f"🎯 Status: {s['conf']} {s['decision']}")
        if idx < 3: msg_parts.append("")

    return "\n".join(msg_parts)

if __name__ == "__main__":
    print(generate_signal())
