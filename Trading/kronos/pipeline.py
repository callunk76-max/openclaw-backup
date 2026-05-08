#!/usr/bin/env python3
"""Kronos Pipeline — Smart 15-min cron runner.

Runs every 15 min via cron:
1. Check if data needs refreshing (once daily for FX_DAILY)
2. Run predictions on latest data
3. Generate BUY/SELL signals
4. Save signals for the trading system

For 5min intraday (future): Lower the REFRESH_INTERVAL.
"""
import sys, os, time, json, pickle
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR, SIGNAL_FILE

# How often to refresh data from API (seconds)
# Daily data: refresh every 12 hours
# 5min data: refresh every 30-60 min
REFRESH_INTERVAL = 2 * 3600   # 2 jam (H1 data changes every hour)
DATA_META_FILE = f"{DATA_DIR}/.data_meta.json"

def is_data_stale():
    """Check if data needs refreshing."""
    if not os.path.exists(DATA_META_FILE):
        return True

    try:
        with open(DATA_META_FILE) as f:
            meta = json.load(f)
        last_fetch = datetime.fromisoformat(meta.get("last_fetch", "2000-01-01"))
        elapsed = (datetime.now() - last_fetch).total_seconds()

        if elapsed < REFRESH_INTERVAL:
            print(f"⏳ Data fresh ({elapsed/3600:.1f}h ago). Skip fetch.")
            return False
        return True
    except:
        return True

def refresh_data():
    """Fetch fresh data and save metadata."""
    from fetch_data import fetch_all
    results = fetch_all()

    # Save metadata
    meta = {
        "last_fetch": datetime.now().isoformat(),
        "pairs_fetched": sum(1 for v in results.values() if v is not None),
        "pairs_total": len(results),
    }
    with open(DATA_META_FILE, "w") as f:
        json.dump(meta, f, indent=2)

    return results

def run_predictions():
    """Run predictions on available data."""
    from batch_predict import predict_all
    return predict_all()

def run_signals():
    """Generate BUY/SELL signals."""
    from signal_gen import generate_signals
    signals = generate_signals()
    return signals

def run():
    """Run the full pipeline smartly."""
    start = time.time()
    print(f"🚀 Kronos Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Step 1: Refresh data if stale
    if is_data_stale():
        print("\n📡 [1/3] Fetching fresh data...")
        refresh_data()
    else:
        print("\n📡 [1/3] Using cached data ✅")

    # Step 2: Run predictions
    print("\n🔮 [2/3] Running predictions...")
    results = run_predictions()

    # Step 3: Generate signals
    print("\n📊 [3/3] Generating signals...")
    signals = run_signals()

    elapsed = time.time() - start
    print(f"\n⏱ Done in {elapsed:.1f}s")

    # Create status file for /OpenPosisi integration
    status = {
        "timestamp": datetime.now().isoformat(),
        "pairs_predicted": len(results) if results else 0,
        "elapsed_seconds": round(elapsed, 1),
        "next_refresh": (datetime.now() + timedelta(seconds=REFRESH_INTERVAL)).isoformat(),
    }
    with open(f"{DATA_DIR}/.status.json", "w") as f:
        json.dump(status, f, indent=2)

    # Summary for Telegram
    strong_buys = [s for s in signals if s.get('signal') == 'STRONG_BUY']
    strong_sells = [s for s in signals if s.get('signal') == 'STRONG_SELL']

    if strong_buys or strong_sells:
        sb = ", ".join([s['pair'] for s in strong_buys[:5]])
        ss = ", ".join([s['pair'] for s in strong_sells[:5]])
        extra = f"... dan {len(strong_buys)-5} lagi" if len(strong_buys) > 5 else ""
        msg = f"📊 *Kronos Signals*\n🟢 BUY: {sb} {extra}\n🔴 SELL: {ss}\n⏱ {elapsed:.0f}s"
    else:
        msg = "📊 Kronos: No strong signals today"

    return signals, msg

if __name__ == "__main__":
    signals, msg = run()
    print("\n" + "="*40)
    print(msg)
