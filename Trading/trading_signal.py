import requests
from datetime import datetime
import time
import json
import os
from position_manager import load_positions
import trading_snd

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
        # Columns: close=current price, high=current daily high, low=current daily low
        # (matching MQ4 MarketInfo MODE_HIGH/MODE_LOW/MODE_BID)
        tickers = [f"OANDA:{p.replace('/', '')}" for p in PAIRS]
        
        payload = {
            "symbols": {"tickers": tickers},
            "columns": ["close", "high", "low"]
        }
        
        url = "https://scanner.tradingview.com/forex/scan"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.post(url, json=payload, headers=headers).json()
        
        strengths = {}
        for row in response.get("data", []):
            symbol = row["s"].replace("OANDA:", "")
            pair = f"{symbol[:3]}/{symbol[3:]}"
            
            c = float(row["d"][0])  # current close/bid
            h = float(row["d"][1])  # current day high
            l = float(row["d"][2])  # current day low
            
            if h == l:
                strengths[pair] = 0
                continue

            # Original "Giraia" logic dari callunk.mq4 CalculateCurrencyStrength()
            bid_ratio = (c - l) / (h - l)  # (curr_bid - day_low) / (day_high - day_low)

            # Discrete bucket mapping 0-9
            if   bid_ratio >= 0.97: score = 9
            elif bid_ratio >= 0.90: score = 8
            elif bid_ratio >= 0.75: score = 7
            elif bid_ratio >= 0.60: score = 6
            elif bid_ratio >= 0.50: score = 5
            elif bid_ratio >= 0.40: score = 4
            elif bid_ratio >= 0.25: score = 3
            elif bid_ratio >= 0.10: score = 2
            elif bid_ratio >= 0.03: score = 1
            else:                   score = 0

            strengths[pair] = score
            
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
    """Format delta string, e.g. (+0.5) or (-0.3). Empty if unchanged."""
    if previous is None:
        return ''
    diff = round(current - previous, 1)
    if diff == 0:
        return ''
    return f' ({diff:+.1f})'


def get_ema_gates():
    """Fetch EMA20/50/100/200 (H1) via TradingView scanner, return pair -> gate data."""
    try:
        tickers = [f"OANDA:{p.replace('/', '')}" for p in PAIRS]
        payload = {
            "symbols": {"tickers": tickers},
            "columns": ["close|60", "EMA20|60", "EMA50|60", "EMA100|60", "EMA200|60"]
        }
        url = "https://scanner.tradingview.com/forex/scan"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.post(url, json=payload, headers=headers).json()

        gates = {}
        for row in response.get("data", []):
            symbol = row["s"].replace("OANDA:", "")
            pair = f"{symbol[:3]}/{symbol[3:]}"

            if row["d"] is None:
                gates[pair] = {"bull": 0, "bear": 0, "emas": {}, "close": 0}
                continue

            close = float(row["d"][0])
            ema20 = float(row["d"][1])
            ema50 = float(row["d"][2])
            ema100 = float(row["d"][3])
            ema200 = float(row["d"][4])

            bull = bear = 0
            if close > ema20: bull += 1
            if close > ema50: bull += 1
            if close > ema100: bull += 1
            if close > ema200: bull += 1
            if close < ema20: bear += 1
            if close < ema50: bear += 1
            if close < ema100: bear += 1
            if close < ema200: bear += 1

            gates[pair] = {
                "bull": bull, "bear": bear, "close": close,
                "emas": {"20": ema20, "50": ema50, "100": ema100, "200": ema200}
            }

        return gates
    except Exception as e:
        print(f"Error fetching EMA gates: {e}")
        return {}


def fmt_gate_line(pair, gates, is_buy):
    """Format EMA gate display: '🟢 EMA: 4/4 E20🟢 E50🟢 E100🔴 E200🔴'
    🟢 = close above EMA, 🔴 = close below EMA."""
    g = gates.get(pair, {})
    if not g.get("emas"):
        return None

    close = g["close"]
    emas = g["emas"]
    bull = g["bull"]
    periods = ["20", "50", "100", "200"]

    parts = []
    for p in periods:
        ema = emas.get(p)
        if ema is None or ema == 0:
            parts.append(f"E{p}?")
        else:
            above = close > ema
            mark = "🟢" if above else "🔴"
            parts.append(f"E{p}{mark}")

    icon = "🟢" if (bull if is_buy else g["bear"]) >= 3 else "🟡" if (bull if is_buy else g["bear"]) >= 2 else "🔴"
    return f"{icon} EMA: {' '.join(parts)}"


def get_market_context(pairs_list):
    """Fetch ATR, ADX, RSI (H1 & H4) for multi-TF context.
    Returns dict: pair -> {atr_60, atr_240, adx_60, rsi_60, rsi_240, close_60}
    """
    try:
        tickers = [f"OANDA:{p.replace('/', '')}" for p in pairs_list]
        payload = {
            "symbols": {"tickers": tickers},
            "columns": ["ATR|60", "ATR|240", "ADX|60", "RSI|60", "RSI|240", "close|60"]
        }
        url = "https://scanner.tradingview.com/forex/scan"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.post(url, json=payload, headers=headers).json()

        ctx = {}
        for row in response.get("data", []):
            symbol = row["s"].replace("OANDA:", "")
            pair = f"{symbol[:3]}/{symbol[3:]}"

            if row["d"] is None or None in row["d"]:
                ctx[pair] = None
                continue

            ctx[pair] = {
                "atr_60": row["d"][0],
                "atr_240": row["d"][1],
                "adx_60": row["d"][2],
                "rsi_60": row["d"][3],
                "rsi_240": row["d"][4],
                "close_60": row["d"][5],
            }

        return ctx
    except Exception as e:
        print(f"Error fetching market context: {e}")
        return {}



def get_decision_label(gap):
    # Threshold disesuaikan untuk sigmoid scaling (range efektif ~2-7)
    if gap >= 4.0: return "ENTER NOW 🔥", "✅"
    elif gap >= 3.0: return "WAIT FOR DIP ⏳", "☑️"
    elif gap >= 2.0: return "WATCH CLOSELY 👀", "⚠️"
    else: return "AVOID / CHOPPY ❌", "🛑"

def get_pivot_levels(pairs_list):
    """Fetch high[1], low[1], close[1] (D1) and calculate floor pivot points.
    Returns dict: pair -> {pivot, r1, r2, r3, s1, s2, s3}
    """
    try:
        tickers = [f"OANDA:{p.replace('/', '')}" for p in pairs_list]
        payload = {
            "symbols": {"tickers": tickers},
            "columns": ["high[1]|60", "low[1]|60", "close[1]|60"]
        }
        url = "https://scanner.tradingview.com/forex/scan"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.post(url, json=payload, headers=headers).json()

        pivots = {}
        for row in response.get("data", []):
            symbol = row["s"].replace("OANDA:", "")
            pair = f"{symbol[:3]}/{symbol[3:]}"

            if row["d"] is None or None in row["d"]:
                continue

            h1 = float(row["d"][0])
            l1 = float(row["d"][1])
            c1 = float(row["d"][2])

            if h1 == l1:
                continue

            p = (h1 + l1 + c1) / 3
            pivots[pair] = {
                "pivot": round(p, 5),
                "r1": round(2 * p - l1, 5),
                "r2": round(p + (h1 - l1), 5),
                "r3": round(h1 + 2 * (p - l1), 5),
                "s1": round(2 * p - h1, 5),
                "s2": round(p - (h1 - l1), 5),
                "s3": round(l1 - 2 * (h1 - p), 5),
            }

        return pivots
    except Exception as e:
        print(f"Error fetching pivot data: {e}")
        return {}


def fmt_snr_advice(pair, pivots, current_price, direction):
    """Practical SnR advice based on pivot proximity and trade direction.
    direction: 'BUY', 'SELL', or 'NEUTRAL'
    Returns: short practical string like 'BUY ✅🛣️ PANJANG'
    """
    pv = pivots.get(pair)
    if not pv or current_price <= 0:
        return None

    supports = [pv["s1"], pv["s2"], pv["s3"]]
    resists  = [pv["r1"], pv["r2"], pv["r3"]]

    # Nearest resistance above price
    near_res_dist = None
    for r in resists:
        if r > current_price:
            d = (r - current_price) / current_price * 100
            if near_res_dist is None or d < near_res_dist:
                near_res_dist = d

    # Nearest support below price
    near_sup_dist = None
    for s in supports:
        if s < current_price:
            d = (current_price - s) / current_price * 100
            if near_sup_dist is None or d < near_sup_dist:
                near_sup_dist = d

    # Count broken resistances (R below price = bullish breakout)
    broken_res = sum(1 for r in resists if r < current_price)
    broken_sup = sum(1 for s in supports if s > current_price)

    if direction == "BUY":
        # BUY: cares about resistance ahead
        if near_res_dist is None:
            # All R broken, open road
            return "BUY ✅🛣️ PANJANG"
        elif near_res_dist >= 1.0:
            return "BUY ✅ MASIH OK"
        elif near_res_dist >= 0.3:
            return "BUY ⚠️ MENTOK"
        else:
            return "BUY 🚧 MENTOK!"

    elif direction == "SELL":
        # SELL: cares about support below
        if near_sup_dist is None:
            return "SELL ✅🛣️ PANJANG"
        elif near_sup_dist >= 1.0:
            return "SELL ✅ MASIH OK"
        elif near_sup_dist >= 0.3:
            return "SELL ⚠️ MENTOK"
        else:
            return "SELL 🚧 MENTOK!"

    # NEUTRAL — show what needs to happen
    if broken_res >= 2:
        # Price has broken resistances (bullish structure)
        if near_res_dist and near_res_dist < 0.5:
            return "NUNGGU PULLBACK"
        return "NUNGGU BUY OK ⬆️"
    elif broken_sup >= 2:
        if near_sup_dist and near_sup_dist < 0.5:
            return "NUNGGU PULLBACK"
        return "NUNGGU SELL OK ⬇️"
    else:
        return "NUNGGU SINYAL ⏳"


def calculate_entry_levels(pair, direction, pivots, current_price, atr=None):
    """Calculate entry range, TP, and SL.
    
    Entry zone: Use pivot points (S1-cur for BUY, cur-R1 for SELL).
    TP/SL: ATR-based (dynamic) with pivot fallback.
    
    ATR-based TP = price ± (ATR × 1.5)
    ATR-based SL = price ± (ATR × 0.8)
    """
    pv = pivots.get(pair)
    if not pv or current_price <= 0:
        return None

    # Dynamic precision based on pair type
    if "JPY" in pair:
        precision = 3
    elif current_price < 10:
        precision = 5
    else:
        precision = 4

    if direction == "BUY":
        entry_bottom = pv["s1"]
        entry_top = current_price

        # ATR-based TP/SL with pivot fallback
        if atr and atr > 0:
            tp = current_price + (atr * 1.5)
            sl = current_price - (atr * 0.8)
        else:
            tp = pv["r1"]
            sl = pv["s2"]

        # Safety: guarantee tp > price, sl < price
        if tp <= current_price:
            tp = current_price + (current_price * 0.003)
        if sl >= current_price:
            sl = current_price - (current_price * 0.002)

    elif direction == "SELL":
        entry_bottom = current_price
        entry_top = pv["r1"]

        if atr and atr > 0:
            tp = current_price - (atr * 1.5)
            sl = current_price + (atr * 0.8)
        else:
            tp = pv["s1"]
            sl = pv["r2"]

        if tp >= current_price:
            tp = current_price - (current_price * 0.003)
        if sl <= current_price:
            sl = current_price + (current_price * 0.002)
    else:
        return None

    return {
        "direction": direction,
        "entry_bottom": round(entry_bottom, precision),
        "entry_top": round(entry_top, precision),
        "tp": round(tp, precision),
        "sl": round(sl, precision),
    }


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
                
                all_gaps.append({
                    'pair': actual_pair, 
                    'gap': gap, 
                    'base_val': all_powers[base],
                    'quote_val': all_powers[quote],
                    'action': action
                })

    # Filter by minimum gap, then take top 5
    MIN_GAP = 2.0
    top_5 = sorted([g for g in all_gaps if g['gap'] >= MIN_GAP],
                   key=lambda x: x['gap'], reverse=True)[:5]
    
    current_pairs = [s['pair'] for s in top_5]
    
    # ---------------- FETCH EMA GATES & SND ZONES ---------------- #
    all_gates = get_ema_gates()

    # Fetch SnD zone analysis for top pairs
    snd_data = trading_snd.analyze_all_pairs(current_pairs, all_gates, all_gates) if current_pairs else {}
    
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

    # Top 5 signals
    if top_5:
        count = len(top_5)
        if count == 1:
            msg_parts.append(f"🎯 **TOP OPPORTUNITY**")
        else:
            msg_parts.append(f"🎯 **TOP {count} SIGNALS**")
    else:
        msg_parts.append(f"🎯 **NO SIGNALS** | Min gap 2.0, none qualified ✅")
        msg_parts.append(f"   └ Wait for wider spread between currencies")
    for idx, s in enumerate(top_5, 1):
        display_pair = s['pair']
        msg_parts.append(f"{idx}️⃣ **{display_pair}**")
        
        # Indicator: EMA Gates
        if "BUY" in s['action']:
            gate_is_buy = True
        elif "SELL" in s['action']:
            gate_is_buy = False
        else:
            g = all_gates.get(s['pair'], {})
            gate_is_buy = g.get("bull", 0) >= g.get("bear", 0)
        gate_line = fmt_gate_line(s['pair'], all_gates, gate_is_buy)
        if gate_line:
            msg_parts.append(f"   {gate_line}")

        if idx < count: msg_parts.append("")

    # ---------------- MARKET CONTEXT (ADX/RSI/ATR) ---------------- #
    market_context = get_market_context(current_pairs) if current_pairs else {}
    
    if not top_5:
        msg_parts.append("")

    # Remove the last elements (old signal loop from above left stale gate_line in msg_parts)
    # Keep only header + board + open positions. Remove everything from signal header onwards.
    # The signal header was appended above at "Top 5 signals" block.
    # We'll re-add it properly here.
    while len(msg_parts) > 0 and "🎯" in msg_parts[-1] and "NO SIGNALS" in msg_parts[-1]:
        msg_parts.pop()
    while len(msg_parts) > 0 and "Wait for wider" in msg_parts[-1]:
        msg_parts.pop()
    # Remove the old signal header and any stale gate lines
    # Find where the signal section starts and truncate to there
    last_safe_idx = 0
    for i, line in enumerate(msg_parts):
        if "🎯 **TOP" in line or ("🎯" in line and "NO SIGNALS" in line):
            break
        last_safe_idx = i + 1
    # Also check for stale gate lines from the old loop
    while len(msg_parts) > last_safe_idx:
        msg_parts.pop()

    # ---------------- SIGNALS (with context + confluence) ---------------- #
    if top_5:
        count = len(top_5)
        if count == 1:
            msg_parts.append(f"🎯 **TOP OPPORTUNITY**")
        else:
            msg_parts.append(f"🎯 **TOP {count} SIGNALS**")
    else:
        msg_parts.append(f"🎯 **NO SIGNALS** | Min gap 2.0, none qualified ✅")
        msg_parts.append(f"   └ Wait for wider spread between currencies")
        msg_parts.append("")

    for idx, s in enumerate(top_5, 1):
        display_pair = s['pair']
        msg_parts.append(f"{idx}️⃣ **{display_pair}**")

        # EMA Gates
        if "BUY" in s['action']:
            gate_is_buy = True
        elif "SELL" in s['action']:
            gate_is_buy = False
        else:
            g = all_gates.get(s['pair'], {})
            gate_is_buy = g.get("bull", 0) >= g.get("bear", 0)
        gate_line = fmt_gate_line(s['pair'], all_gates, gate_is_buy)
        if gate_line:
            msg_parts.append(f"   {gate_line}")

        # REGIME: ADX + RSI + ATR
        ctx = market_context.get(s['pair'])
        if ctx:
            adx = ctx.get("adx_60", 0) or 0
            rsi = ctx.get("rsi_60", 50) or 50
            atr = ctx.get("atr_60", 0) or 0

            trend_icon = "🔥" if adx >= 25 else ("⚡" if adx >= 20 else "🌊")
            regime = "TRENDING" if adx >= 25 else ("WEAK TREND" if adx >= 20 else "RANGING")

            if rsi >= 60: rsi_mark = "🟢"
            elif rsi >= 50: rsi_mark = "🟡"
            elif rsi >= 40: rsi_mark = "🟠"
            else: rsi_mark = "🔴"

            # Convert ATR to pips for readability
            if "JPY" in s['pair']:
                atr_pips = atr * 100
                atr_display = f"{atr_pips:.1f}"
            elif s['pair'] in ["XAU/USD", "XAG/USD"]:
                atr_pips = atr
                atr_display = f"{atr_pips:.2f}"
            else:
                atr_pips = atr * 10000
                atr_display = f"{atr_pips:.1f}"

            msg_parts.append(f"   📊 ADX: {adx:.0f} ({regime})")

        # SnD Advice
        g = all_gates.get(s['pair'], {})
        cur_price = g.get("close", 0)
        if "BUY" in s['action']:
            snd_dir = "BUY"
        elif "SELL" in s['action']:
            snd_dir = "SELL"
        else:
            snd_dir = "NEUTRAL"
        pair_snd = snd_data.get(s['pair'], {})
        advice = trading_snd.fmt_snd_advice(s['pair'], pair_snd, cur_price, snd_dir) if pair_snd.get('has_data') and cur_price else None
        if advice:
            msg_parts.append(f"   {advice}")

        # Entry Suggestion (inline)
        if "BUY" in s['action'] or "SELL" in s['action']:
            pv = get_pivot_levels([s['pair']])
            g = all_gates.get(s['pair'], {})
            cur_price = g.get("close", 0)
            ctx = market_context.get(s['pair'])
            atr_val = ctx.get("atr_60") if ctx else None
            direction = "BUY" if "BUY" in s['action'] else "SELL"
            levels = calculate_entry_levels(s['pair'], direction, pv, cur_price, atr_val)
            if levels:
                msg_parts.append(f"   **{levels['direction']}** : {levels['entry_bottom']} - {levels['entry_top']}")
                msg_parts.append(f"   TP : **{levels['tp']}** | SL : **{levels['sl']}**")

        if idx < count:
            msg_parts.append("")

    return "\n".join(msg_parts)

if __name__ == "__main__":
    print(generate_signal())
