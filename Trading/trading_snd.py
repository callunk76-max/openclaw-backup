"""
trading_snd.py — Supply & Demand Zone Detection (Practical Implementation)
 
Uses available D1 OHLC data + EMA levels to build dynamic SnD zones
instead of rigid pivot points.

Key concepts (from forum research):
  - SnD zones ≠ pivot points. Zones are RANGES, not exact lines.
  - Base + Impulse: consolidation → explosive move = valid zone.
  - Fresh zones (unretested) >> stale zones.
  - Volatility matters: thresholds should adapt to daily range.
  - Higher timeframe (D1/H4) > lower timeframe (H1/M15).
"""

import requests
import json
from datetime import datetime, timezone
import math

PAIRS = [
    "EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD", "USD/CAD", "USD/CHF", "USD/JPY",
    "EUR/GBP", "EUR/JPY", "EUR/CAD", "EUR/CHF", "EUR/AUD", "EUR/NZD",
    "GBP/JPY", "GBP/CAD", "GBP/CHF", "GBP/AUD", "GBP/NZD",
    "AUD/JPY", "AUD/CAD", "AUD/CHF", "AUD/NZD",
    "NZD/JPY", "NZD/CAD", "NZD/CHF",
    "CAD/JPY", "CAD/CHF", "CHF/JPY"
]


def fetch_daily_candles(pairs, num_days=10):
    """Fetch daily OHLC data for given pairs via TradingView scanner.
    Returns dict: pair -> [candle0, candle1, ...] where candle0=most recent.
    Each candle: {open, high, low, close}
    """
    columns = ['close', 'high', 'low', 'open']
    for i in range(1, num_days):
        columns.extend([f'close[{i}]', f'high[{i}]', f'low[{i}]', f'open[{i}]'])

    tickers = [f"OANDA:{p.replace('/', '')}" for p in pairs]
    payload = {
        "symbols": {"tickers": tickers},
        "columns": columns
    }
    url = "https://scanner.tradingview.com/forex/scan"
    headers = {"User-Agent": "Mozilla/5.0"}

    result = {}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15).json()
        for row in response.get("data", []):
            symbol = row["s"].replace("OANDA:", "")
            pair = f"{symbol[:3]}/{symbol[3:]}"
            vals = row["d"]

            candles = []
            for i in range(num_days):
                base = i * 4
                if base + 3 < len(vals):
                    o, h, l, c = vals[base:base+4]
                    if c is not None:
                        candles.append({
                            "open": o, "high": h, "low": l, "close": c,
                        })
            result[pair] = candles
        return result
    except Exception as e:
        print(f"[SnD] Error fetching daily candles: {e}")
        return {}


def calc_body_percent(candle):
    """Return candle body as percentage of total range."""
    body = abs(candle["close"] - candle["open"])
    rng = candle["high"] - candle["low"]
    if rng == 0:
        return 100
    return (body / rng) * 100


def find_snd_zones(candles):
    """Identify Supply & Demand zones from daily candle data.
    
    Algorithm:
    1. Base + Impulse pattern detection:
       - Base = candle where body < 55% of range (consolidation)
       - Impulse = next candle with large body or big directional move
       - Zone boundaries use body range (not full wick range) for precision
    2. Structure-based zones:
       - Swing highs/lows that showed strong rejection
       - Consecutive same-direction candles = momentum zones
    
    Returns: list of zone dicts sorted by freshness (newest first)
             or None if no zones can be detected
    """
    zones = []
    n = len(candles)

    for i in range(n - 1):
        curr = candles[i]
        next_c = candles[i + 1]

        curr_body_pct = calc_body_percent(curr)
        next_body_pct = calc_body_percent(next_c)

        curr_range = curr["high"] - curr["low"]
        next_range = next_c["high"] - next_c["low"]
        curr_body = abs(curr["close"] - curr["open"])
        next_body = abs(next_c["close"] - next_c["open"])

        is_bullish = next_c["close"] > next_c["open"]
        is_bearish = next_c["close"] < next_c["open"]

        # Base: body < 55% or range below average of neighbors
        is_base = curr_body_pct < 55

        # Impulse: 
        #   - Range significantly bigger than base
        #   - OR body >= 55% of its own range
        #   - OR strong directional (close near top/bottom)
        is_impulse = (next_range > curr_range * 1.3 or next_body_pct >= 55)

        if is_base and is_impulse:
            # Zone = body range of BASE candle (more precise than full H-L)
            zone_top = max(curr["open"], curr["close"])
            zone_bot = min(curr["open"], curr["close"])
            
            # If body is tiny, use 40% of candle range as zone
            if zone_top == zone_bot:
                mid = (curr["high"] + curr["low"]) / 2
                buffer = curr_range * 0.2
                zone_top = mid + buffer
                zone_bot = mid - buffer

            zone_type = "DEMAND" if is_bullish else "SUPPLY"

            # Strength: bigger impulse = stronger zone
            strength = min(round(next_body_pct / 15, 1), 5.0)
            if strength < 1:
                strength = 1.0

            zones.append({
                "type": zone_type,
                "top": round(zone_top, 5),
                "bottom": round(zone_bot, 5),
                "mid": round((zone_top + zone_bot) / 2, 5),
                "height": round(zone_top - zone_bot, 5),
                "strength": strength,
                "freshness": i,
                "impulse_body_pct": round(next_body_pct, 1),
            })

        # Also detect swing-based zones:
        # Strong reversal candle (big body closing against prior direction)
        if i > 0 and i < n - 1:
            prev = candles[i - 1]
            
            # Bullish Engulfing / Strong reversal up
            if (curr["close"] < curr["open"] and  # red candle
                next_c["close"] > next_c["open"] and  # then green candle
                next_body >= curr_range * 0.8 and  # significant move
                next_c["close"] > curr["mid"]):  # closed above midpoint
                
                zone_top = max(next_c["open"], next_c["close"])
                zone_bot = min(next_c["open"], next_c["close"])
                
                zones.append({
                    "type": "DEMAND",
                    "top": round(zone_top, 5),
                    "bottom": round(zone_bot, 5),
                    "mid": round((zone_top + zone_bot) / 2, 5),
                    "height": round(zone_top - zone_bot, 5),
                    "strength": min(round(next_body_pct / 15, 1), 5.0),
                    "freshness": i,
                    "impulse_body_pct": round(next_body_pct, 1),
                })
            
            # Bearish Engulfing / Strong reversal down
            if (curr["close"] > curr["open"] and  # green candle
                next_c["close"] < next_c["open"] and  # then red candle
                next_body >= curr_range * 0.8 and
                next_c["close"] < curr["mid"]):
                
                zone_top = max(next_c["open"], next_c["close"])
                zone_bot = min(next_c["open"], next_c["close"])
                
                zones.append({
                    "type": "SUPPLY",
                    "top": round(zone_top, 5),
                    "bottom": round(zone_bot, 5),
                    "mid": round((zone_top + zone_bot) / 2, 5),
                    "height": round(zone_top - zone_bot, 5),
                    "strength": min(round(next_body_pct / 15, 1), 5.0),
                    "freshness": i,
                    "impulse_body_pct": round(next_body_pct, 1),
                })

    if not zones:
        return None

    # Sort by freshness (newest first = lowest index)
    zones.sort(key=lambda z: z["freshness"])
    
    # Remove duplicate/redundant zones (merged overlapping)
    merged = []
    for z in zones:
        is_dup = False
        for m in merged:
            if m["type"] == z["type"]:
                # Check overlap
                if (z["bottom"] <= m["top"] and z["top"] >= m["bottom"]):
                    # Merge: expand zone to cover both
                    m["bottom"] = min(m["bottom"], z["bottom"])
                    m["top"] = max(m["top"], z["top"])
                    m["mid"] = (m["top"] + m["bottom"]) / 2
                    m["height"] = m["top"] - m["bottom"]
                    m["strength"] = max(m["strength"], z["strength"])
                    m["freshness"] = min(m["freshness"], z["freshness"])
                    is_dup = True
                    break
        if not is_dup:
            merged.append(z)

    return merged


def build_ema_zones(current_price, emas, direction):
    """Build dynamic zones from EMA levels as fallback when no SnD zones found.
    
    EMA levels act as natural support/resistance.
    Returns: list of zone dicts
    """
    zones = []
    if not emas:
        return zones

    # EMAs act as dynamic zones
    periods = ["20", "50", "100", "200"]
    for p in periods:
        ema = emas.get(p)
        if ema is None or ema == 0:
            continue

        # Each EMA creates a zone with spread = 0.15% around it
        spread = ema * 0.0015  # 0.15% buffer
        zone_top = ema + spread
        zone_bot = ema - spread

        if current_price > ema:
            # Price above EMA = support zone
            zones.append({
                "type": "DEMAND",
                "top": round(zone_top, 5),
                "bottom": round(zone_bot, 5),
                "mid": round(ema, 5),
                "height": round(spread * 2, 5),
                "strength": 1.5,
                "freshness": 0,
                "impulse_body_pct": 0,
                "ema_label": f"E{p}",
            })
        else:
            # Price below EMA = resistance zone
            zones.append({
                "type": "SUPPLY",
                "top": round(zone_top, 5),
                "bottom": round(zone_bot, 5),
                "mid": round(ema, 5),
                "height": round(spread * 2, 5),
                "strength": 1.5,
                "freshness": 0,
                "impulse_body_pct": 0,
                "ema_label": f"E{p}",
            })

    return zones


def get_price_vs_zones(current_price, zones, direction):
    """Evaluate current price relative to detected SnD zones.
    
    Args:
        current_price: Current market price
        zones: List of zone dicts from find_snd_zones()
        direction: 'BUY', 'SELL', or 'NEUTRAL'
    
    Returns: dict with status, room, zone info
    """
    if not zones:
        return None

    # Find nearest zones
    nearest_above = None  # Supply/Resistance above price
    nearest_below = None  # Demand/Support below price
    min_dist_above = float('inf')
    min_dist_below = float('inf')

    for z in zones:
        zone_mid = z["mid"]

        if zone_mid > current_price:
            # Zone above price
            # If price is below zone bottom = more room
            if current_price < z["bottom"]:
                dist = abs(z["bottom"] - current_price) / current_price * 100
            else:
                # Price is inside or touching zone = tight
                dist = abs(z["mid"] - current_price) / current_price * 100
            
            if dist < min_dist_above:
                min_dist_above = dist
                nearest_above = {**z, "distance": round(dist, 2)}

        elif zone_mid < current_price:
            # Zone below price
            if current_price > z["top"]:
                dist = abs(current_price - z["top"]) / current_price * 100
            else:
                dist = abs(current_price - z["mid"]) / current_price * 100
            
            if dist < min_dist_below:
                min_dist_below = dist
                nearest_below = {**z, "distance": round(dist, 2)}

    advice = {}
    if direction == "BUY":
        # BUY: key concern = nearest resistance/supply above price
        if nearest_above:
            dist = nearest_above["distance"]
            if dist >= 1.5:
                advice["status"] = "PANJANG ✅🛣️"
            elif dist >= 0.8:
                advice["status"] = "OK ✅"
            elif dist >= 0.4:
                advice["status"] = "WASPADA ⚠️"
            else:
                advice["status"] = "MENTOK 🚧"
            advice["zone"] = nearest_above
            advice["room"] = dist
        else:
            advice["status"] = "PANJANG ✅🛣️"
            advice["zone"] = None
            advice["room"] = 99

    elif direction == "SELL":
        # SELL: key concern = nearest support/demand below price
        if nearest_below:
            dist = nearest_below["distance"]
            if dist >= 1.5:
                advice["status"] = "PANJANG ✅🛣️"
            elif dist >= 0.8:
                advice["status"] = "OK ✅"
            elif dist >= 0.4:
                advice["status"] = "WASPADA ⚠️"
            else:
                advice["status"] = "MENTOK 🚧"
            advice["zone"] = nearest_below
            advice["room"] = dist
        else:
            advice["status"] = "PANJANG ✅🛣️"
            advice["zone"] = None
            advice["room"] = 99

    else:
        # NEUTRAL — show nearest zone info
        if nearest_above and nearest_below:
            if nearest_above["distance"] < nearest_below["distance"]:
                advice["status"] = f"NUNGGU ⬆️ {nearest_above['distance']:.1f}% ke Supply"
                advice["zone"] = nearest_above
            else:
                advice["status"] = f"NUNGGU ⬇️ {nearest_below['distance']:.1f}% ke Demand"
                advice["zone"] = nearest_below
        elif nearest_above:
            advice["status"] = f"NUNGGU ⬆️ {nearest_above['distance']:.1f}% ke Supply"
            advice["zone"] = nearest_above
        elif nearest_below:
            advice["status"] = f"NUNGGU ⬇️ {nearest_below['distance']:.1f}% ke Demand"
            advice["zone"] = nearest_below
        else:
            advice["status"] = "NUNGGU SINYAL ⏳"
            advice["zone"] = None
        advice["room"] = 0

    return advice


def fmt_snd_advice(pair, snd_data, current_price, direction):
    """Format SnD advice for signal output (replaces fmt_snr_advice).
    
    Args:
        pair: str (e.g. 'EUR/USD')
        snd_data: dict from analyze_pair_snd()
        current_price: float
        direction: 'BUY', 'SELL', or 'NEUTRAL'
    
    Returns: formatted string or None if no data
    """
    if not snd_data or not snd_data.get("has_data"):
        return None

    zones = snd_data.get("zones", [])
    if not zones:
        # No SnD zones — use EMA zones as fallback
        emas = snd_data.get("emas", {})
        if emas:
            zones = build_ema_zones(current_price, emas, direction)
        if not zones:
            return None

    advice = get_price_vs_zones(current_price, zones, direction)
    if not advice:
        return None

    room = advice.get("room", 0)
    status = advice.get("status", "NUNGGU SINYAL ⏳")
    zone = advice.get("zone")

    if zone and room < 99:
        zone_type = "Demand 🟢" if zone["type"] == "DEMAND" else "Supply 🔴"
        z_top = zone["top"]
        z_bot = zone["bottom"]
        label = zone.get("ema_label", "")
        str_stars = "★" * min(int(zone.get("strength", 1)), 5)
        
        ema_suffix = f" ({label})" if label else ""
        
        if direction in ("BUY", "SELL"):
            return f"SnD: {status} | {zone_type} {z_bot}-{z_top}{ema_suffix} {str_stars} | Room: {room:.1f}%"
        else:
            return f"SnD: {status} | {zone_type} {z_bot}-{z_top}{ema_suffix}"
    else:
        return f"SnD: {status} | 🛣️ Open Road"


def analyze_all_pairs(pairs, current_data=None, gatelines=None):
    """Run SnD analysis for all pairs.
    
    Args:
        pairs: list of pair strings
        current_data: dict of pair->{close, emas, ...} from get_ema_gates
        gatelines: same as current_data
    
    Returns: dict of pair -> {zones, price, has_data, emas}
    """
    candle_data = fetch_daily_candles(pairs, num_days=10)
    
    results = {}
    for pair in pairs:
        candles = candle_data.get(pair, [])
        if len(candles) < 2:
            # Not enough candle data, use EMA fallback
            emas = {}
            if gatelines and pair in gatelines:
                emas = gatelines[pair].get("emas", {})
            price = 0
            if current_data and pair in current_data:
                price = current_data[pair].get("close", 0)
            results[pair] = {
                "zones": [],
                "price": price,
                "has_data": True if emas else False,
                "emas": emas,
            }
            continue

        zones = find_snd_zones(candles)
        
        price = 0
        if current_data and pair in current_data:
            price = current_data[pair].get("close", 0)
        if price == 0 and candles:
            price = candles[0].get("close", 0)

        emas = {}
        if gatelines and pair in gatelines:
            emas = gatelines[pair].get("emas", {})

        results[pair] = {
            "zones": zones,
            "price": price,
            "has_data": True,
            "candles": candles,
            "emas": emas,
        }

    return results
