import requests
from datetime import datetime
import time
import json
import os
from position_manager import load_positions

# Signal history tracking for consecutive numbering
SIGNAL_HISTORY_FILE = '/root/.openclaw/workspace/Trading/signal_history.json'

def load_signal_history():
    if os.path.exists(SIGNAL_HISTORY_FILE):
        with open(SIGNAL_HISTORY_FILE, 'r') as f:
            data = json.load(f)
        today = datetime.now().strftime('%Y-%m-%d')
        # Migrate old format (int values) to new format (dict)
        if "history" in data:
            for pair, val in list(data["history"].items()):
                if isinstance(val, int):
                    data["history"][pair] = {
                        "consecutive": val, "stars": 0, "crown_date": today
                    }
        return data
    return {"history": {}, "last_pairs": []}

def update_signal_history(current_pairs):
    """Track consecutive appearances, stars, and crown for pairs.
    
    Same-day logic:
      👑  = first continuous run (no gaps). Crown stays while present.
      ⭐  = reappearance after disappearing. Accumulates per gap.
      num = consecutive appearances within current run.
    
    Next day: EVERYTHING resets. All pairs start fresh with 👑.
    """
    today = datetime.now().strftime('%Y-%m-%d')
    history = load_signal_history()
    last_pairs = set(history.get("last_pairs", []))
    hist = history.get("history", {})
    current_set = set(current_pairs)

    updated = {}

    for pair in current_pairs:
        was_in_last = pair in last_pairs
        entry = hist.get(pair)

        if entry is None:
            # Brand new pair — first time ever
            entry = {"consecutive": 1, "stars": 0, "crown_date": today}

        elif was_in_last:
            # Ensure crown_date exists (safety for old/migrated entries)
            entry.setdefault("crown_date", today)
            # Consecutive appearance — increment
            entry["consecutive"] = entry.get("consecutive", 0) + 1
            # Crossing into a new day → full reset
            if entry.get("crown_date", "") != today:
                entry["crown_date"] = today
                entry["stars"] = 0
                entry["consecutive"] = 1

        else:
            # Reappearance (was missing last run)
            crown_date = entry.get("crown_date", "")
            entry["consecutive"] = 1
            if crown_date != today:
                # New day — fresh start
                entry["stars"] = 0
                entry["crown_date"] = today
            else:
                # Same day — add a star, crown cycle over
                entry["stars"] = entry.get("stars", 0) + 1

        updated[pair] = entry

    # Keep disappeared pairs in history so star/crown state persists
    for pair, entry in hist.items():
        if pair not in current_set:
            updated[pair] = entry

    history["history"] = updated
    history["last_pairs"] = current_pairs

    with open(SIGNAL_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)

    return updated

def get_pair_display(pair, counts):
    """Return pair with 👑/⭐/number markings."""
    data = counts.get(pair, {})
    consecutive = data.get("consecutive", 0)
    stars = data.get("stars", 0)
    crown_date = data.get("crown_date", "")
    today = datetime.now().strftime('%Y-%m-%d')

    # 👑 mode: no stars, active crown cycle
    if stars == 0 and crown_date == today:
        return f"{pair} 👑{consecutive}"

    # ⭐ mode: reappeared after disappearing
    if stars > 0:
        return f"{pair} {'⭐' * stars}{consecutive}"

    return pair

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

# Previous signal tracking for delta display
PREV_SIGNAL_FILE = '/root/.openclaw/workspace/Trading/previous_signal.json'

def load_prev_signal():
    if os.path.exists(PREV_SIGNAL_FILE):
        try:
            with open(PREV_SIGNAL_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_prev_signal(data):
    with open(PREV_SIGNAL_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def fmt_delta(current, previous):
    """Format delta string, e.g. (+0.5) or (-0.3)."""
    if previous is None:
        return ''
    diff = round(current - previous, 1)
    if diff == 0:
        return ' (±0.0)'
    return f' ({diff:+.1f})'


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

    # Filter by minimum gap 5.5, then take top 3 or fewer
    MIN_GAP = 5.5
    top_3 = sorted([g for g in all_gaps if g['gap'] >= MIN_GAP],
                   key=lambda x: x['gap'], reverse=True)[:3]
    
    # Track signal history for consecutive numbering
    current_pairs = [s['pair'] for s in top_3]
    signal_counts = update_signal_history(current_pairs) if current_pairs else {}
    
    # ---------------- LOAD PREVIOUS STATE FOR DELTAS ---------------- #
    prev = load_prev_signal()
    prev_strengths = prev.get('strengths', {})
    prev_gaps = prev.get('gaps', {})

    # Save current state for next run
    current_strengths = {c: round(v, 2) for c, v in all_powers.items()}
    current_gaps = {g['pair']: round(g['gap'], 2) for g in all_gaps}
    save_prev_signal({'strengths': current_strengths, 'gaps': current_gaps})

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
        prev_val = prev_strengths.get(curr)
        delta = fmt_delta(val, prev_val) if prev_val is not None else ''
        msg_parts.append(f"{emoji} {curr} : {val:.2f}{delta}")
    
    msg_parts.append(f"〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️")
    
    # Open Positions
    if position_updates:
        msg_parts.append("💼 **OPEN POSITIONS MANAGER**")
        msg_parts.extend(position_updates)
        msg_parts.append(f"〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️")

    # Top opportunities (minimum gap 5.5)
    if top_3:
        count = len(top_3)
        if count == 1:
            msg_parts.append(f"🎯 **TOP OPPORTUNITY**")
        else:
            msg_parts.append(f"🎯 **TOP {count} OPPORTUNITIES**")
    else:
        msg_parts.append(f"🎯 **NO SIGNALS** | Min gap 5.5, none qualified ✅")
        msg_parts.append(f"   └ Wait for wider spread between currencies")
    for idx, s in enumerate(top_3, 1):
        base, quote = s['pair'].split('/')
        
        display_pair = get_pair_display(s['pair'], signal_counts)
        prev_gap_val = prev_gaps.get(s['pair'])
        gap_delta = fmt_delta(s['gap'], prev_gap_val) if prev_gap_val is not None else ''
        msg_parts.append(f"{idx}️⃣ **{display_pair}**")
        msg_parts.append(f"⚡ Power : {base} ({s['base_val']:.2f}) vs {quote} ({s['quote_val']:.2f})")
        msg_parts.append(f"📉 Gap   : {s['gap']:.2f}{gap_delta} Pts")
        msg_parts.append(f"📈 Action: {s['action']}")
        msg_parts.append(f"🎯 Status: {s['conf']} {s['decision']}")
        if idx < 3: msg_parts.append("")

    return "\n".join(msg_parts)

if __name__ == "__main__":
    print(generate_signal())
