#!/usr/bin/env python3
"""Seed H1 state from CSV data."""
import csv, json, os
from datetime import datetime

SD = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(SD, "h1_data")
OUT = os.path.join(SD, "dashboard", "h1_candle.json")

PAIRS = [
    'EUR/USD','GBP/USD','AUD/USD','NZD/USD',
    'USD/CAD','USD/CHF','USD/JPY',
    'EUR/GBP','EUR/JPY','EUR/CAD','EUR/CHF','EUR/AUD','EUR/NZD',
    'GBP/JPY','GBP/CAD','GBP/CHF','GBP/AUD','GBP/NZD',
    'AUD/JPY','AUD/CAD','AUD/CHF','AUD/NZD',
    'NZD/JPY','NZD/CAD','NZD/CHF',
    'CAD/JPY','CAD/CHF','CHF/JPY','XAU/USD'
]

state = {}
for pair in PAIRS:
    f = pair.replace('/', '')
    fp = os.path.join(CSV, f + '_H1.csv')
    if not os.path.exists(fp):
        continue
    with open(fp) as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) < 2:
        continue
    
    p = rows[-2]  # previous H1
    c = rows[-1]  # last H1 (15:00 WIB)
    
    po, ph, pl, pc = float(p['Open']), float(p['High']), float(p['Low']), float(p['Close'])
    co, ch, cl, cc = float(c['Open']), float(c['High']), float(c['Low']), float(c['Close'])
    cv = int(c['Volume'])
    ct = int(datetime.strptime(c['Time'], '%Y.%m.%d %H:%M').timestamp())
    
    state[pair] = {
        'open_time': ct, 'open': co, 'high': ch, 'low': cl,
        'close': cc, 'volume': cv,
        'prev_h1_dir': 'BULLISH' if pc > po else 'BEARISH'
    }

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w') as f:
    json.dump(state, f, indent=2)

print(f'Seeded {len(state)} pairs:')
for p in list(state.keys())[:3]:
    s = state[p]
    print(f'  {p}: H-1={s["prev_h1_dir"]} (15:00 open={s["open"]:.5f})')
