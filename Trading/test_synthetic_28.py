import requests

API_KEY = "5668c0334bdf4694a7ee8e3f2169c520"
BASE_URL = "https://api.twelvedata.com"
USD_PAIRS = ["EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD", "USD/CAD", "USD/CHF", "USD/JPY"]

url = f"{BASE_URL}/time_series?symbol={','.join(USD_PAIRS)}&interval=1day&outputsize=2&apikey={API_KEY}"
response = requests.get(url).json()

data = {}
for p in USD_PAIRS:
    today = response[p]["values"][0]
    yest = response[p]["values"][1]
    data[p] = {
        "c": float(today["close"]),
        "h": float(today["high"]),
        "l": float(today["low"])
    }

def get_hlc(pair):
    if pair in data: return data[pair]
    
    b, q = pair.split('/')
    # cross pair synthesis
    b_usd = f"{b}/USD"
    usd_b = f"USD/{b}"
    q_usd = f"{q}/USD"
    usd_q = f"USD/{q}"
    
    # Base is quoted against USD, Quote is quoted against USD
    if b_usd in data and q_usd in data:
        # e.g. EUR/GBP = EUR/USD / GBP/USD
        return {
            "h": data[b_usd]["h"] / data[q_usd]["l"],
            "l": data[b_usd]["l"] / data[q_usd]["h"],
            "c": data[b_usd]["c"] / data[q_usd]["c"]
        }
    # Base is quoted against USD, USD is quoted against Quote
    elif b_usd in data and usd_q in data:
        # e.g. EUR/JPY = EUR/USD * USD/JPY
        return {
            "h": data[b_usd]["h"] * data[usd_q]["h"],
            "l": data[b_usd]["l"] * data[usd_q]["l"],
            "c": data[b_usd]["c"] * data[usd_q]["c"]
        }
    # USD is quoted against Base, Quote is quoted against USD
    elif usd_b in data and q_usd in data:
        # e.g. CAD/AUD = (1/USD/CAD) / AUD/USD = 1 / (USD/CAD * AUD/USD)
        return {
            "h": 1.0 / (data[usd_b]["l"] * data[q_usd]["l"]),
            "l": 1.0 / (data[usd_b]["h"] * data[q_usd]["h"]),
            "c": 1.0 / (data[usd_b]["c"] * data[q_usd]["c"])
        }
    # USD is quoted against Base, USD is quoted against Quote
    elif usd_b in data and usd_q in data:
        # e.g. CAD/CHF = USD/CHF / USD/CAD
        return {
            "h": data[usd_q]["h"] / data[usd_b]["l"],
            "l": data[usd_q]["l"] / data[usd_b]["h"],
            "c": data[usd_q]["c"] / data[usd_b]["c"]
        }
    return None

PAIRS = [
    "EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD", "USD/CAD", "USD/CHF", "USD/JPY",
    "EUR/GBP", "EUR/JPY", "EUR/CAD", "EUR/CHF", "EUR/AUD", "EUR/NZD",
    "GBP/JPY", "GBP/CAD", "GBP/CHF", "GBP/AUD", "GBP/NZD",
    "AUD/JPY", "AUD/CAD", "AUD/CHF", "AUD/NZD",
    "NZD/JPY", "NZD/CAD", "NZD/CHF",
    "CAD/JPY", "CAD/CHF", "CHF/JPY"
]

strengths = {}
for p in PAIRS:
    hlc = get_hlc(p)
    ratio = (hlc["c"] - hlc["l"]) / (hlc["h"] - hlc["l"])
    ratio = max(0, min(1, ratio))
    if ratio >= 0.97: s = 9
    elif ratio >= 0.90: s = 8
    elif ratio >= 0.75: s = 7
    elif ratio >= 0.60: s = 6
    elif ratio >= 0.50: s = 5
    elif ratio >= 0.40: s = 4
    elif ratio >= 0.25: s = 3
    elif ratio >= 0.10: s = 2
    elif ratio >= 0.03: s = 1
    else: s = 0
    strengths[p] = s

CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'NZD', 'CAD', 'CHF']
sums = {c: 0 for c in CURRENCIES}
for p, score in strengths.items():
    b, q = p.split('/')
    sums[b] += score
    sums[q] += (9 - score)
norm = {c: val / 7 for c, val in sums.items()}
print("Powers:", sorted(norm.items(), key=lambda x: x[1], reverse=True))
