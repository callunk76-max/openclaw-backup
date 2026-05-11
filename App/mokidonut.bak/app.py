from flask import Flask, render_template, jsonify
import json
import os
import csv
import subprocess
import re
import sys
from datetime import datetime, timezone, timedelta
import time as time_module

sys.path.insert(0, '/root/.openclaw/workspace/Trading')
import trading_signal
import trading_snd

app = Flask(__name__)

BASE = "/root/.openclaw/workspace/Trading"
SIGNALS_CSV = f"{BASE}/kronos/data/signals.csv"
PREDICTIONS_CSV = f"{BASE}/kronos/data/predictions.csv"
SIGNAL_HISTORY = f"{BASE}/signal_history.json"
POSITIONS_FILE = f"{BASE}/positions.json"
PREV_SIGNAL_FILE = f"{BASE}/previous_signal.json"

WITA = timezone(timedelta(hours=8))

_cache = {}
_cache_time = {}
def cached(key, ttl=60):
    def deco(f):
        def wrapper(*a, **kw):
            now = time_module.time()
            if key in _cache and (now - _cache_time.get(key, 0)) < ttl:
                return _cache[key]
            r = f(*a, **kw)
            _cache[key] = r
            _cache_time[key] = now
            return r
        return wrapper
    return deco

# ─── Loaders ──────────────────────────────────────────────
def load_signals():
    if not os.path.exists(SIGNALS_CSV): return []
    with open(SIGNALS_CSV) as f:
        return list(csv.DictReader(f))

def load_predictions():
    if not os.path.exists(PREDICTIONS_CSV): return []
    with open(PREDICTIONS_CSV) as f:
        return list(csv.DictReader(f))

def load_history():
    if not os.path.exists(SIGNAL_HISTORY): return {}
    with open(SIGNAL_HISTORY) as f:
        return json.load(f)

def load_positions():
    if not os.path.exists(POSITIONS_FILE): return {}
    try:
        with open(POSITIONS_FILE) as f: return json.load(f)
    except: return {}

def get_last_run():
    log = f"{BASE}/kronos/kronos_cron.log"
    if not os.path.exists(log): return None
    try:
        r = subprocess.run(['tail','-1',log], capture_output=True, text=True)
        m = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', r.stdout)
        return m.group(1) if m else r.stdout.strip()[:50]
    except: return None

# ─── System ──────────────────────────────────────────────
def get_uptime():
    try:
        with open('/proc/uptime') as f:
            s = float(f.readline().split()[0])
        return f"{int(s//86400)}d {int((s%86400)//3600)}h"
    except: return "--"
def get_cpu():
    try:
        l = os.getloadavg()[0]; c = os.cpu_count() or 1
        return f"{round(l/c*100,1)}%"
    except: return "--"
def get_ram():
    try:
        with open('/proc/meminfo') as f: d = f.read()
        mt = re.search(r'MemTotal:\s+(\d+)', d)
        ma = re.search(r'MemAvailable:\s+(\d+)', d)
        if mt and ma:
            t = round(int(mt.group(1))/1024/1024,1)
            u = round(t - int(ma.group(1))/1024/1024,1)
            return f"{u}G/{t}G"
        return "--"
    except: return "--"
def get_disk():
    try:
        r = subprocess.run(['df','-h','/'], capture_output=True, text=True)
        return r.stdout.strip().split('\n')[1].split()[4]
    except: return "--"

# ─── Data fetchers ───────────────────────────────────────
@cached('strength', 60)
def fetch_strength():
    try:
        sp, n = trading_signal.calculate_powers()
        ps = trading_signal.get_all_strengths()
        return {'sorted_powers': [{'currency':c,'power':round(n[c],2)} for c,_ in sp], 'pair_strengths': ps}
    except Exception as e: return {'error': str(e)}

@cached('gates', 60)
def fetch_gates():
    try: return trading_signal.get_ema_gates()
    except Exception as e: return {'error': str(e)}

@cached('snd', 120)
def fetch_snd():
    try:
        g = fetch_gates()
        return trading_snd.analyze_all_pairs(trading_signal.PAIRS, g if isinstance(g,dict) else None, g if isinstance(g,dict) else None)
    except Exception as e: return {'error': str(e)}

@cached('market_ctx', 60)
def fetch_market_context():
    try: return trading_signal.get_market_context(trading_signal.PAIRS)
    except: return {}

@cached('pivots', 120)
def fetch_pivots():
    try: return trading_signal.get_pivot_levels(trading_signal.PAIRS)
    except: return {}

def norm(pair):
    if '/' not in pair and len(pair) >= 6:
        return pair[:3] + '/' + pair[3:]
    return pair

# ─── Routes ───────────────────────────────────────────────
@app.route('/')
def home(): return render_template('index.html')

@app.route('/api/stats')
def api_stats():
    return jsonify({'uptime':get_uptime(),'cpu':get_cpu(),'ram':get_ram(),'disk':get_disk()})

@app.route('/api/signals')
def api_signals():
    signals = load_signals()
    predictions = load_predictions()
    history = load_history()
    positions = load_positions()
    gates = fetch_gates()
    snd_data = fetch_snd()
    market_ctx = fetch_market_context()
    pivots = fetch_pivots()

    last_run = get_last_run()
    now = datetime.now(WITA).strftime("%Y-%m-%d %H:%M:%S")

    # Pre-load gaps
    gaps = {}
    if os.path.exists(PREV_SIGNAL_FILE):
        try:
            with open(PREV_SIGNAL_FILE) as f:
                gaps = json.load(f).get('gaps', {})
        except: pass

    pred_lookup = {p['pair']: p for p in predictions}
    hist_pairs = history.get('history', {})

    # Accuracy per pair
    pair_accuracy = {}
    pair_dir_totals = {}
    for p in predictions:
        pk = norm(p['pair'])
        dc = p.get('dir_correct', '').lower()
        if dc == 'true':
            pair_accuracy[pk] = pair_accuracy.get(pk, 0) + 1
            pair_dir_totals[pk] = pair_dir_totals.get(pk, 0) + 1
        elif dc == 'false':
            pair_dir_totals[pk] = pair_dir_totals.get(pk, 0) + 1

    enriched = []
    counts = {"STRONG_BUY":0,"BUY":0,"SELL":0,"STRONG_SELL":0,"NEUTRAL":0}

    for s in signals:
        pair = s['pair']
        signal_type = s['signal']
        counts[signal_type] = counts.get(signal_type, 0) + 1

        h = hist_pairs.get(pair, {})
        p = pred_lookup.get(pair, {})
        pos = positions.get(pair, {})

        # Norm key
        nk = norm(pair)

        # EMA Gates
        g = gates.get(nk, {}) if isinstance(gates, dict) else {}
        emas = g.get('emas', {})
        cg = g.get('close', 0)
        gate_status = {}
        for per in ['20','50','100','200']:
            ev = emas.get(per)
            gate_status[per] = {'value': round(ev,5) if ev else 0, 'above': bool(ev and cg and cg > ev)}

        # SnD
        snd_pair = snd_data.get(nk, {}) if isinstance(snd_data, dict) else {}
        snd_nearest = None
        price_snd = float(s.get('current_price', 0)) or 0
        for z in (snd_pair.get('zones') or []):
            mid = z.get('mid', 0)
            if mid and price_snd:
                dist = abs(mid - price_snd) / price_snd * 100
                if snd_nearest is None or dist < snd_nearest['distance']:
                    snd_nearest = {'type':z['type'],'top':z['top'],'bottom':z['bottom'],'mid':z['mid'],'distance':round(dist,2),'ema_label':z.get('ema_label','')}

        # Market Context
        ctx = market_ctx.get(nk, {})
        entry = None
        dir_sig = "BUY" if "BUY" in signal_type else ("SELL" if "SELL" in signal_type else None)
        if dir_sig and price_snd:
            entry = trading_signal.calculate_entry_levels(nk, dir_sig, pivots, price_snd, (ctx.get('atr_60') if ctx else None))

        # Gap
        gap = gaps.get(nk, gaps.get(pair, 0))

        # Performance
        acc_total = pair_dir_totals.get(nk, 0)
        acc_correct = pair_accuracy.get(nk, 0)
        acc_pct = round(acc_correct / acc_total * 100, 1) if acc_total > 0 else None

        enriched.append({
            'pair': pair,
            'signal': signal_type,
            'current_price': s.get('current_price','--'),
            'predicted_price': s.get('predicted_price','--'),
            'change_pct': s.get('change_pct','0'),
            'confidence': s.get('confidence','0'),
            'direction': s.get('direction','--'),
            'dir_correct': p.get('dir_correct',''),
            'stars': h.get('stars', 0),
            'consecutive': h.get('consecutive', 0),
            'crown_date': h.get('crown_date', ''),
            'in_position': pair in positions,
            'pos_type': pos.get('type', ''),
            # 4 Gate
            'gate_bull': g.get('bull',0),
            'gate_emas': gate_status,
            # SnD
            'snd_nearest': snd_nearest,
            # Market Context
            'market': {
                'adx': round(ctx.get('adx_60',0),1) if ctx else None,
                'rsi': round(ctx.get('rsi_60',50),1) if ctx else None,
                'atr': round(ctx.get('atr_60',0),5) if ctx else None,
            } if ctx else None,
            # Entry SL/TP
            'entry': entry,
            # Gap
            'gap': round(gap, 2) if isinstance(gap, (int,float)) else None,
            # Performance
            'accuracy': acc_pct,
            'accuracy_count': acc_total,
        })

    summary = {
        'total': len(enriched),
        'strong_buy': counts['STRONG_BUY'],
        'buy': counts['BUY'],
        'sell': counts['SELL'],
        'strong_sell': counts['STRONG_SELL'],
        'neutral': counts['NEUTRAL'],
        'accuracy': calculate_accuracy(predictions),
        'positions': len(positions),
    }

    return jsonify({'signals': enriched, 'summary': summary, 'last_run': last_run, 'now': now})

@app.route('/api/positions')
def api_positions():
    positions = load_positions()
    signals = load_signals()
    gates = fetch_gates()
    sl = {s['pair']: s for s in signals}
    enr = []
    for pair,pos in positions.items():
        s = sl.get(pair, {})
        nk = norm(pair)
        g = gates.get(nk, {}) if isinstance(gates, dict) else {}
        enr.append({'pair':pair,'type':pos.get('type',''),'signal':s.get('signal','N/A'),'current_price':s.get('current_price',str(g.get('close',0))),'confidence':s.get('confidence','0'),'ema_status':{'bull':g.get('bull',0),'bear':g.get('bear',0)}})
    return jsonify({'positions':enr,'count':len(enr)})

@app.route('/api/strength')
def api_strength():
    return jsonify(fetch_strength())

@app.route('/api/gates')
def api_gates():
    return jsonify(fetch_gates())

@app.route('/api/snd')
def api_snd():
    return jsonify(fetch_snd())

def calculate_accuracy(predictions):
    t=c=0
    for p in predictions:
        d = p.get('dir_correct','').lower()
        if d=='true': c+=1; t+=1
        elif d=='false': t+=1
    return round(c/t*100,1) if t else 0

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)
