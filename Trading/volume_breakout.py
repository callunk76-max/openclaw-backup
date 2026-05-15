#!/usr/bin/env python3
"""
Volume Breakout Scanner — H1 | Callunk Signal System
=====================================================
Scan 28 major/minor pairs + XAUUSD.
Timeframe: H1 (60 menit)

Filter rules:
  1️⃣ Volume ≥ 1.5x MA20
  2️⃣ Body candle ≥ 60% total range
  3️⃣ Close di extreme (shadow ≤ 20% range)
  
Output: hanya pair yang lolos semua filter + status gold
"""

import requests, json, os, sys, time
from datetime import datetime

WIB_OFFSET = 7 * 3600
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── KONFIGURASI ──
TF = "60"                        # H1 = 60 menit
VOLUME_MULTIPLIER = 1.5          # minimal volume vs MA20
BODY_THRESHOLD = 0.60            # minimal body ratio
CLOSE_THRESHOLD = 0.20           # maksimal shadow ratio

# ── PAIRS ──
FOREX_PAIRS = [
    "EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD",
    "USD/CAD", "USD/CHF", "USD/JPY",
    "EUR/GBP", "EUR/JPY", "EUR/CAD", "EUR/CHF", "EUR/AUD", "EUR/NZD",
    "GBP/JPY", "GBP/CAD", "GBP/CHF", "GBP/AUD", "GBP/NZD",
    "AUD/JPY", "AUD/CAD", "AUD/CHF", "AUD/NZD",
    "NZD/JPY", "NZD/CAD", "NZD/CHF",
    "CAD/JPY", "CAD/CHF", "CHF/JPY",
]
ALL_PAIRS = FOREX_PAIRS + ["XAU/USD"]

# ── FILE STATE ──
VOL_FILE = os.path.join(SCRIPT_DIR, "volume_history_h1.json")
NOTIFIED_FILE = os.path.join(SCRIPT_DIR, "notified_breakouts.json")

# ── TIME HELPERS ──
def wib_now():
    return datetime.fromtimestamp(time.time() + WIB_OFFSET)

def ts_wib():
    n = wib_now()
    return n.strftime("%H:%M"), n.strftime("%A, %d %b %Y")

def ts_unix():
    return int(time.time())

# ── DATA FETCH ──
def tv_ticker(pair):
    if pair == "XAU/USD":
        return None  # handled separately
    base, quote = pair.split("/")
    return f"OANDA:{base}{quote}"

def scan_forex_h1():
    """Fetch H1 OHLCV + candle open time for forex pairs"""
    tickers = [tv_ticker(p) for p in FOREX_PAIRS]
    cols = [f"{c}|{TF}" for c in ["open", "high", "low", "close", "volume", "time"]]
    
    try:
        payload = {"symbols": {"tickers": tickers}, "columns": cols}
        r = requests.post(
            "https://scanner.tradingview.com/forex/scan",
            json=payload,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20
        )
        data = r.json()
        results = {}
        for row in data.get("data", []):
            s = row["s"].replace("OANDA:", "")
            pair = f"{s[:3]}/{s[3:]}" if len(s) == 6 else s
            results[pair] = {"open": float(row["d"][0]), "high": float(row["d"][1]),
                            "low": float(row["d"][2]), "close": float(row["d"][3]),
                            "volume": int(row["d"][4]),
                            "time": int(row["d"][5]) if row["d"][5] else 0}
        return results
    except Exception as e:
        return {"__error__": str(e)}

def scan_gold_h1():
    """Fetch H1 gold data from TV commodities/CFD scanner"""
    try:
        cols = [f"{c}|{TF}" for c in ["open", "high", "low", "close", "volume"]]
        payload = {"symbols": {"tickers": ["TVC:GOLD"]}, "columns": cols}
        r = requests.post(
            "https://scanner.tradingview.com/cfd/scan",
            json=payload,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        )
        d = r.json()
        if d.get("data"):
            row = d["data"][0]["d"]
            return {"open": float(row[0]), "high": float(row[1]),
                    "low": float(row[2]), "close": float(row[3]),
                    "volume": int(row[4])}
    except:
        pass
    # Fallback
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=8)
        g = r.json()
        p = g["price"]
        return {"open": p, "high": p + 10, "low": p - 10, "close": p, "volume": 0}
    except:
        return None

# ── VOLUME HISTORY (MA20 rolling) ──
def load_vol_history():
    try:
        with open(VOL_FILE) as f:
            return json.load(f)
    except:
        return {"h1": {}}

def save_vol_history(h):
    os.makedirs(SCRIPT_DIR, exist_ok=True)
    with open(VOL_FILE, "w") as f:
        json.dump(h, f)

def get_ma20(h, pair, current_vol):
    pair_data = h.get("h1", {}).get(pair, [])
    if len(pair_data) >= 20:
        return sum(pair_data[-20:]) / 20
    elif len(pair_data) > 5:
        return sum(pair_data) / len(pair_data)
    else:
        # Seed: estimate from current candle
        return max(current_vol * 0.7, 1)

def update_vol(h, pair, vol, ts):
    if vol <= 0:
        return h
    h1 = h.setdefault("h1", {})
    pair_d = h1.setdefault(pair, [])
    pair_d.append(vol)
    if len(pair_d) > 30:
        h1[pair] = pair_d[-30:]
    h["_last_update"] = ts
    return h

# ── H1 CANDLE TRACKING ──
H1_STATE_FILE = os.path.join(SCRIPT_DIR, "dashboard", "h1_candle.json")

def save_h1_state(states):
    """Simpan snapshot candle H1 saat ini"""
    os.makedirs(os.path.dirname(H1_STATE_FILE), exist_ok=True)
    with open(H1_STATE_FILE, "w") as f:
        json.dump(states, f)

def load_h1_state():
    try:
        with open(H1_STATE_FILE) as f:
            return json.load(f)
    except:
        return {}

def check_h1_volume(pair, current_dir, current_vol, prev_h1_dict):
    """Compare volume candle H1 skrg vs H1 sebelumnya.
    Kalo volume H1 sebelumnya > H1 skrg → arah H1 sebelumnya yg SAH.
    """
    if not prev_h1_dict or not isinstance(prev_h1_dict, dict):
        return {"sah_dir": current_dir, "note": "Data H1 sebelumnya belum ada"}
    
    prev_dir = prev_h1_dict.get("direction", current_dir)
    prev_vol = prev_h1_dict.get("volume", 0)
    if prev_vol > 0 and current_vol > 0 and prev_vol > current_vol:
        return {
            "sah_dir": prev_dir,
            "note": f"Volume H1 sblmnya ({prev_vol:,}) > H1 skrg ({current_vol:,}) — arah H1 sblmnya yg SAH ({prev_dir})",
            "prev_dir": prev_dir, "prev_vol": prev_vol, "current_vol": current_vol
        }
    else:
        return {
            "sah_dir": current_dir,
            "note": f"Volume H1 skrg ({current_vol:,}) >= H1 sblmnya ({prev_vol:,}) — arah H1 skrg yg SAH ({current_dir})",
            "prev_dir": prev_dir, "prev_vol": prev_vol, "current_vol": current_vol
        }

# ── BREAKOUT HISTORY ──
HISTORY_FILE = os.path.join(SCRIPT_DIR, "dashboard", "breakout_history.json")
HISTORY_CANDLES = 15  # simpan 15 scan terakhir (~3-4 jam dengan interval 15min)

def load_breakout_history():
    try:
        with open(HISTORY_FILE) as f:
            return json.load(f)
    except:
        return {"scans": []}

def save_breakout_history(history):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

def record_breakout_scan(breakouts, time_str):
    """Record which pairs had breakout in this scan"""
    history = load_breakout_history()
    scan_entry = {
        "time": time_str,
        "ts": int(time.time()),
        "breakout_pairs": [b["pair"] for b in breakouts]
    }
    history.setdefault("scans", []).append(scan_entry)
    # Keep only last N scans
    if len(history["scans"]) > HISTORY_CANDLES:
        history["scans"] = history["scans"][-HISTORY_CANDLES:]
    save_breakout_history(history)
    return history

def get_recent_breakout_status(pair, history):
    """Check if pair had breakout in last 4 scans (now + 3 candles back)"""
    scans = history.get("scans", [])
    hist = {"h1": False, "h2": False, "h3": False}
    newest_ago = None
    
    # Reverse newest first, then pad to 4 entries for consistent mapping
    recent = list(reversed(scans))[:4]
    # Pad with empty scans so index 0=now, 1=h1, 2=h2, 3=h3 always
    while len(recent) < 4:
        recent.append({"breakout_pairs": []})
    
    for i, scan in enumerate(recent):
        if pair in scan.get("breakout_pairs", []):
            if i == 0:
                hist["now"] = True
                newest_ago = 0
            elif i == 1:
                hist["h1"] = True
                if newest_ago is None: newest_ago = 1
            elif i == 2:
                hist["h2"] = True
                if newest_ago is None: newest_ago = 2
            elif i == 3:
                hist["h3"] = True
                if newest_ago is None: newest_ago = 3
    
    if newest_ago is None:
        return None
    return {
        "newest": newest_ago,
        "hist": hist,
        "consolidating": hist.get("h1", False) and hist.get("h2", False) and hist.get("h3", False)
    }

# ── NOTIFICATION TRACKING (dedup) ──
COOLDOWN_SECS = 7200  # 2 jam, jangan notif pair yg sama

def load_notified():
    try:
        with open(NOTIFIED_FILE) as f:
            return json.load(f)
    except:
        return {"breakouts": []}

def save_notified(n):
    with open(NOTIFIED_FILE, "w") as f:
        json.dump(n, f)

def is_new_breakout(pair, direction):
    """Cek apakah breakout ini sudah dinotifikasi dalam cooldown period"""
    n = load_notified()
    now = ts_unix()
    for b in n.get("breakouts", []):
        if b["pair"] == pair and b["direction"] == direction:
            if now - b["ts"] < COOLDOWN_SECS:
                return False
    return True

def mark_notified(pair, direction):
    n = load_notified()
    n.setdefault("breakouts", [])
    n["breakouts"].append({"pair": pair, "direction": direction, "ts": ts_unix()})
    # Hapus yg expired
    now = ts_unix()
    n["breakouts"] = [b for b in n["breakouts"] if now - b["ts"] < COOLDOWN_SECS * 2]
    save_notified(n)

# ── CANDLE ANALYZER ──
def analyze(o, h, l, c, vol, ma20):
    result = {
        "pass": False,
        "vol_pass": False, "body_pass": False, "close_pass": False,
        "direction": None,
        "vol_ratio": 0, "body_pct": 0,
        "range": h - l,
        "body": abs(c - o),
    }
    rng = result["range"]
    if rng == 0:
        return result
    
    body = result["body"]
    body_pct = (body / rng) * 100
    
    upper_shadow = h - max(o, c)
    lower_shadow = min(o, c) - l
    
    # Filter 1: Volume
    if vol > 0:
        vol_ratio = vol / ma20 if ma20 > 0 else 0
        result["vol_pass"] = vol_ratio >= VOLUME_MULTIPLIER
        result["vol_ratio"] = round(vol_ratio, 2)
    else:
        # Gold / zero-volume: bypass
        result["vol_pass"] = True
        result["vol_ratio"] = 1.0
    
    # Filter 2: Body candle
    result["body_pass"] = body_pct >= (BODY_THRESHOLD * 100)
    result["body_pct"] = round(body_pct, 1)
    
    # Filter 3: Close di extreme
    if c > o:  # Bullish
        result["direction"] = "BULLISH"
        shadow_ratio = (upper_shadow / rng) if rng > 0 else 1
        result["close_pass"] = shadow_ratio <= CLOSE_THRESHOLD
    else:       # Bearish
        result["direction"] = "BEARISH"
        shadow_ratio = (lower_shadow / rng) if rng > 0 else 1
        result["close_pass"] = shadow_ratio <= CLOSE_THRESHOLD
    
    result["pass"] = result["vol_pass"] and result["body_pass"] and result["close_pass"]
    return result

# ── MAIN SCAN ──
def scan():
    TIME_STR, DATE_STR = ts_wib()
    
    vol_h = load_vol_history()
    now = ts_unix()
    if "_last_update" in vol_h and now - vol_h["_last_update"] > 604800:
        vol_h = {"h1": {}}
    
    # Load H1 state (track candle open times)
    h1_state = load_h1_state()
    
    # Fetch
    forex = scan_forex_h1()
    gold = scan_gold_h1()
    
    if isinstance(forex, dict) and "__error__" in forex:
        return None, f"❌ Forex API error: {forex['__error__']}"
    
    all_data = dict(forex or {})
    if gold:
        all_data["XAU/USD"] = gold
    
    results = []
    breakouts = []
    h1_prev_check = []
    
    for pair, candle in all_data.items():
        o, h, l, c = candle["open"], candle["high"], candle["low"], candle["close"]
        v = candle.get("volume", 0)
        t = candle.get("time", 0)  # candle open time
        
        ma20 = get_ma20(vol_h, pair, v)
        
        if v > 0:
            vol_h = update_vol(vol_h, pair, v, now)
        
        # Track H1 candle by open TIME — only check breakout when candle completes
        prev_time = h1_state.get(pair, {}).get("open_time", 0)
        new_h1 = prev_time > 0 and t != prev_time
        
        # Store current H1 data (for dashboard display)
        # But breakout is only valid on COMPLETED H1 candle
        if new_h1:
            # Previous H1 completed — pake prev_h1_dir yg udah ada (dari seed/scan sblm)
            old_state = h1_state.get(pair, {})
            prev_dir = old_state.get("prev_h1_dir")
            if not prev_dir:
                # Fallback: hitung dari perbandingan open
                prev_open = old_state.get("open", 0)
                prev_dir = "BULLISH" if o > prev_open else "BEARISH"
            
            # Reset H1 state dan simpan prev_h1_dir
            h1_state[pair] = {"open_time": t, "open": o, "high": h, "low": l, "close": c,
                           "volume": v, "prev_h1_dir": prev_dir}
            
            # Current H1 candle (with prev_h1_dir for H-1 display)
            now_dir = "BULLISH" if c > o else "BEARISH"
            now_a = analyze(o, h, l, c, v, ma20)
            d = {"pair": pair, "price": c, "open": o, "high": h, "low": l,
                    "volume": v, "ma20": round(ma20, 0), "direction": now_dir,
                    "body_pct": now_a.get("body_pct",0), "vol_ratio": now_a.get("vol_ratio",0),
                    "range": h - l,
                    "vol_pass": now_a.get("vol_pass",False),
                    "body_pass": now_a.get("body_pass",False),
                    "close_pass": now_a.get("close_pass",False),
                    "pass": now_a.get("pass",False), "_completed_h1": False,
                    "prev_h1_dir": prev_dir}
            results.append(d)
        else:
            # Update current H1 state (incomplete candle)
            if pair not in h1_state:
                h1_state[pair] = {"open_time": t, "open": o, "high": h, "low": l, "close": c, "volume": v}
            else:
                s = h1_state[pair]
                if h > s["high"]: s["high"] = h
                if l < s["low"]: s["low"] = l
                s["close"] = c
                s["volume"] = max(s["volume"], v)
            
            # Current candle — tambah prev_h1_dir kalo ada
            now_dir = "BULLISH" if c > o else "BEARISH"
            now_a = analyze(o, h, l, c, v, ma20)
            d = {"pair": pair, "price": c, "open": o, "high": h, "low": l,
                  "volume": v, "ma20": round(ma20, 0), "direction": now_dir,
                  "body_pct": now_a.get("body_pct",0), "vol_ratio": now_a.get("vol_ratio",0),
                  "range": h - l,
                  "vol_pass": now_a.get("vol_pass",False),
                  "body_pass": now_a.get("body_pass",False),
                  "close_pass": now_a.get("close_pass",False),
                  "pass": now_a.get("pass",False), "_completed_h1": False}
            prev_dir = h1_state.get(pair, {}).get("prev_h1_dir")
            if prev_dir:
                d["prev_h1_dir"] = prev_dir
            results.append(d)
    
    save_h1_state(h1_state)
    save_vol_history(vol_h)
    
    # Post-process: add prev_h1_dir + direction
    for d in results:
        pair = d["pair"]
        state = h1_state.get(pair, {})
        prev_dir = state.get("prev_h1_dir")
        if prev_dir:
            d["prev_h1_dir"] = prev_dir
        dir_now = "BULLISH" if d["price"] > d["open"] else "BEARISH"
        d["direction"] = dir_now
    
    return results, breakouts, TIME_STR, DATE_STR

# ── FORMAT OUTPUT ──
def format_signal(results, breakouts, time_str, date_str):
    """Format output untuk dikirim ke Telegram"""
    lines = []
    
    if breakouts:
        recs = generate_recommendations(breakouts)
        
        lines.append(f"🚨 **BREAKOUT DETECTED!** 🚨")
        lines.append(f"🕒 {time_str} WIB | H1")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        
        # Recommendations ranked
        lines.append("\n📊 **RANKING REKOMENDASI**")
        for i, rec in enumerate(recs[:5]):
            dir_icon = "🟢" if rec["direction"] == "BULLISH" else "🔴"
            pair_display = "🥇 XAUUSD" if rec["pair"] == "XAU/USD" else rec["pair"]
            medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i] if i < 5 else f"{i+1}️⃣"
            
            lines.append(f"\n{medal} {pair_display}")
            lines.append(f"   {dir_icon} **{rec['direction']}** @ ${rec['price']} | Skor: {rec['score']}")
            lines.append(f"   📏 Body: {rec['body_pct']}% | Vol: {rec['vol_ratio']}x MA20")
            for reason in rec["reasons"][:3]:
                lines.append(f"   💡 {reason}")
        
        lines.append("\n━━━━━━━━━━━━━━━━━━━━")
        lines.append("👑 Cuy — callunk.my.id")
        return "\n".join(lines)
    
    # No breakout — tetap kirim ringkasan
    passed = [r for r in results if r["pass"]]
    candidates = [r for r in results if sum([r["vol_pass"], r["body_pass"], r["close_pass"]]) >= 2 and not r["pass"]]
    passed.sort(key=lambda x: x["vol_ratio"], reverse=True)
    candidates.sort(key=lambda x: x["vol_ratio"], reverse=True)
    
    lines.append(f"📡 **VOLUME BREAKOUT SCAN**")
    lines.append(f"🕒 {time_str} WIB | H1 | {date_str}")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    
    if passed:
        lines.append(f"\n🚨 **{len(passed)} BREAKOUT** 🚨")
        for b in passed:
            dir_icon = "🟢" if b["direction"] == "BULLISH" else "🔴"
            pd = "🥇 XAUUSD" if b["pair"] == "XAU/USD" else b["pair"]
            lines.append(f"\n{pd} {dir_icon}")
            lines.append(f"   Body: {b['body_pct']}% | Vol: {b['vol_ratio']}x")
    else:
        lines.append(f"\n✅ Tidak ada breakout ({len(results)} pair dipindai)")
    
    if candidates:
        lines.append(f"\n━━━ WATCH LIST (2/3 filter) ━━━")
        for r in candidates[:5]:
            tags = []
            if r["vol_pass"]: tags.append("VOL")
            if r["body_pass"]: tags.append("BODY")
            if r["close_pass"]: tags.append("CLS")
            dir_icon = "🟢" if r["direction"] == "BULLISH" else "🔴"
            lines.append(f"\n{r['pair']} {dir_icon}")
            lines.append(f"   ✅ {', '.join(tags)} | Vol: {r['vol_ratio']}x | Body: {r['body_pct']}%")
    
    # Gold summary
    gold = next((r for r in results if r["pair"] == "XAU/USD"), None)
    if gold:
        lines.append(f"\n━━━ 🥇 GOLD ━━━")
        lines.append(f"   ${gold['price']:,.2f} | Body: {gold['body_pct']}% | {gold['direction']}")
    
    lines.append("\n━━━━━━━━━━━━━━━━━━━━")
    lines.append("👑 Cuy — callunk.my.id")
    return "\n".join(lines)

# ── RECOMMENDATION ENGINE ──
def generate_recommendations(results):
    """Generate recommendations — volume-based H1 comparison"""
    recs = []
    for r in results:
        if not r.get("pass", False) or not r.get("_completed_h1", False):
            continue
        pair, direction = r["pair"], r.get("direction", "")
        current_vol = r.get("volume", 0)
        prev_data = r.get("prev_h1_data")
        reasons = []
        if prev_data:
            vc = check_h1_volume(pair, direction, current_vol, prev_data)
            sah = vc["sah_dir"]
            reasons.append(vc["note"])
            reasons.append("✅ AMAN — arah sesuai" if direction == sah else f"⚠️ TIDAK AMAN — arah skrg ({direction}) ≠ arah volume ({sah})")
        else:
            reasons.append("📡 Data H1 sebelumnya belum ada")
            reasons.append("✅ AMAN — belum ada perbandingan")
        reasons.append("💥 H1 selesai — breakout terkonfirmasi")
        recs.append({"pair": pair, "direction": direction, "price": r.get("price", 0), "reasons": reasons})
    recs.sort(key=lambda x: ("✅" not in x["reasons"][0] if x["reasons"] else True, x["pair"]))
    return recs


def save_dashboard_data(results, breakouts, time_str, date_str):
    """Simpan data ke JSON untuk dashboard"""
    dashboard_dir = os.path.join(SCRIPT_DIR, "dashboard")
    os.makedirs(dashboard_dir, exist_ok=True)
    
    # Load history WITHOUT recording current scan (biar mapping H-1/H-2/H-3 konsisten)
    breakout_history = load_breakout_history()
    
    recommendations = generate_recommendations(results)
    
    data = {
        "updated": f"{date_str} {time_str} WIB",
        "updated_ts": int(time.time()),
        "total_pairs": len(results),
        "breakout_count": len(breakouts),
        "recommendations": [],
        "pairs": []
    }
    
    for r in sorted(results, key=lambda x: (not x.get("pass", False), -(x.get("vol_ratio", 0) or 0))):
        recent = get_recent_breakout_status(r["pair"], breakout_history)
        entry = {
            "pair": r["pair"],
            "price": r["price"],
            "direction": r.get("direction", "N/A"),
            "pass": r.get("pass", False),
            "recent_breakout": recent,
            "breakout_hist": recent["hist"] if recent else None,
            "breakout_consolidating": recent["consolidating"] if recent else False,
            "filters": {
                "volume": r.get("vol_pass", False),
                "body": r.get("body_pass", False),
                "close": r.get("close_pass", False)
            },
            "body_pct": r.get("body_pct", 0),
            "vol_ratio": r.get("vol_ratio", 0),
            "range": r.get("range", 0),
            "open": r.get("open", 0),
            "high": r.get("high", 0),
            "low": r.get("low", 0),
            "volume": r.get("volume", 0),
            "prev_h1_data": r.get("prev_h1_data"),
            "prev_h1_dir": r.get("prev_h1_dir"),
            "searah": r.get("searah"),
        }
        data["pairs"].append(entry)
    
    # Build recommendations
    final_recs = []
    
    # Current breakouts (highest priority)
    for r in recommendations:
        r["type"] = "current"
        final_recs.append(r)
    
    # History pairs — volume comparison with prev_h1 if available
    for entry in data["pairs"]:
        if entry.get("breakout_hist") and not entry.get("pass", False):
            reasons = []
            dh = entry.get("current_h1") or {}
            prev_h1 = entry.get("prev_h1")
            direction = entry.get("direction", "")
            current_vol = entry.get("volume", 0)
            
            if prev_h1:
                vol_check = check_h1_volume(entry["pair"], direction, current_vol, prev_h1)
                sah_dir = vol_check["sah_dir"]
                reasons.append(vol_check["note"])
                if direction == sah_dir:
                    reasons.append("✅ AMAN — arah sesuai volume terbesar")
                else:
                    reasons.append(f"⚠️ TIDAK AMAN — arah skrg ({direction}) berlawanan dgn volume ({sah_dir})")
            else:
                reasons.append("📡 Data H1 sebelumnya belum tersedia — belum bisa bandingin")
            
            if entry.get("breakout_consolidating"):
                reasons.append("⚠️ Trend udah 3 jam berturut-turut — hati-hati")
            
            # Label: H-1 / H-2 / H-3
            bh = entry.get("breakout_hist", {})
            lbl = "H-1" if bh.get("h1") else "H-2" if bh.get("h2") else "H-3" if bh.get("h3") else "H-?"
            reasons.append(f"💥 {lbl}")
            
            final_recs.append({"type": "history", "pair": entry["pair"],
                "direction": entry["direction"], "price": entry["price"],
                "reasons": reasons})
    
    # Sort: current breakouts first, then AMAN dulu
    def sort_key(x):
        type_order = 0 if x["type"] == "current" else 1
        is_aman = "✅" in (x["reasons"][0] if x["reasons"] else "")
        return (type_order, 0 if is_aman else 1, x["pair"])
    final_recs.sort(key=sort_key)
    final_recs = [{"rank": i+1, **r} for i, r in enumerate(final_recs[:15])]
    
    data["recommendations"] = final_recs
    
    path = os.path.join(dashboard_dir, "data.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    
    return path, final_recs

# ── ENTRY POINT ──
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--dashboard", action="store_true", help="Save dashboard JSON + print signal")
    parser.add_argument("--record-scan", action="store_true", help="Record current scan to history")
    args = parser.parse_args()
    
    result = scan()
    if result is None or len(result) < 4:
        err = result[1] if isinstance(result, tuple) and len(result) > 1 else "Unknown error"
        print(f"❌ {err}")
        sys.exit(1)
    
    results, breakouts, time_str, date_str = result
    
    # Cek breakout baru (belum dinotifikasi)
    new_breakouts = [b for b in breakouts if is_new_breakout(b["pair"], b["direction"])]
    for b in new_breakouts:
        mark_notified(b["pair"], b["direction"])
    
    recs = []
    # Record breakout jika pakai --record-scan dulu
    if args.record_scan:
        record_breakout_scan(breakouts, time_str)
    
    if args.dashboard or args.json:
        _, recs = save_dashboard_data(results, breakouts, time_str, date_str)
    
    if not args.json:
        output = format_signal(results, breakouts, time_str, date_str)
        print(output)
    
    # Save recs to file for Telegram notification
    recs_file = os.path.join(SCRIPT_DIR, "dashboard", "recommendations.txt")
    if recs:
        with open(recs_file, "w") as f:
            for r in recs:
                aman = "✅" if any("✅" in x for x in r.get("reasons", [])) else "⚠️"
                f.write(f"{aman} {r['pair']} {r['direction']} @ ${r['price']}\n")
    
    sys.exit(0)
