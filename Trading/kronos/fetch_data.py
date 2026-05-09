"""Fetch H1 OHLC data for all 29 pairs via TwelveData (free tier)."""
import sys, os, time, pandas as pd, requests
sys.path.insert(0, os.path.dirname(__file__))
from config import PAIRS, DATA_DIR, TIMEFRAME, TWELVEDATA_KEY

TD_INTERVAL = {"1h": "1h", "4h": "4h", "1d": "1day", "5min": "5min"}

def fetch_pair(pair):
    """Fetch a pair via TwelveData."""
    symbol = f"{pair[:3]}/{pair[3:]}" if pair != "XAUUSD" else "XAU/USD"
    interval = TD_INTERVAL.get(TIMEFRAME, "1h")

    url = (f"https://api.twelvedata.com/time_series"
           f"?symbol={symbol}&interval={interval}"
           f"&outputsize=5000&apikey={TWELVEDATA_KEY}")

    try:
        r = requests.get(url, timeout=30)
        data = r.json()
        values = data.get("values")
        if not values:
            err = data.get("message", data.get("error", str(data)[:100]))
            print(f"  ❌ {pair}: {err}")
            return None

        rows = [{
            "timestamps": v["datetime"],
            "open": float(v["open"]),
            "high": float(v["high"]),
            "low": float(v["low"]),
            "close": float(v["close"]),
            "volume": float(v.get("volume", 0)),
            "amount": 0,
        } for v in values]

        df = pd.DataFrame(rows)
        df["timestamps"] = pd.to_datetime(df["timestamps"])
        df = df.sort_values("timestamps").reset_index(drop=True)
        df = df[["timestamps", "open", "close", "high", "low", "volume", "amount"]]
        print(f"  ✅ {pair}: {len(df)} rows (H1)")
        return df
    except Exception as e:
        print(f"  ❌ {pair}: {e}")
        return None

def fetch_all():
    """Fetch all pairs, respecting 8 calls/min rate limit."""
    os.makedirs(DATA_DIR, exist_ok=True)
    results = {}
    delay = 8  # seconds (8 calls/min free tier)

    print(f"📡 Fetching {len(PAIRS)} pairs H1 via TwelveData...")
    print("=" * 55)

    for i, pair in enumerate(PAIRS):
        if i > 0:
            print(f"  ⏳ {delay}s...")
            time.sleep(delay)

        df = fetch_pair(pair)
        if df is not None:
            fpath = f"{DATA_DIR}/{pair}.csv"
            df.to_csv(fpath, index=False)
            results[pair] = fpath
        else:
            results[pair] = None

    success = sum(1 for v in results.values() if v is not None)
    print("=" * 55)
    print(f"📊 Done: ✅ {success}/{len(PAIRS)} pairs")
    return results

if __name__ == "__main__":
    fetch_all()
