"""Master script: Fetch → Predict → Signal — all 28 pairs"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))

from config import DATA_DIR
from fetch_data import fetch_all
from batch_predict import predict_all
from signal_gen import generate_signals, get_signal_summary

def run_all():
    """Run full pipeline."""
    start = time.time()
    print("🚀 KRONOS x Callunk — Full Pipeline")
    print(f"   28 Forex Pairs | 5min Timeframe | {time.strftime('%Y-%m-%d %H:%M')}")
    print("=" * 55)

    # Step 1: Fetch data
    print("\n[1/3] Fetching data from Yahoo Finance...")
    data = fetch_all()
    success = sum(1 for v in data.values() if v is not None)
    if success == 0:
        print("❌ No data fetched. Aborting.")
        return
    print(f"✅ {success}/28 pairs fetched")

    # Step 2: Predict
    print("\n[2/3] Running Kronos predictions...")
    results = predict_all()
    if not results:
        print("❌ No predictions generated. Aborting.")
        return
    print(f"✅ {len(results)}/{len(results)} pairs predicted")

    # Step 3: Generate signals
    print("\n[3/3] Generating BUY/SELL signals...")
    signals = generate_signals()

    elapsed = time.time() - start
    print(f"\n⏱ Total time: {elapsed:.1f}s")
    print("✅ Pipeline complete!")

    # Print summary for Telegram
    print("\n" + "=" * 55)
    print(get_signal_summary())

    return signals

def save_to_trading_system(signals):
    """Save top signals to a format usable by the trading system."""
    if not signals:
        return

    # Get actionable signals (STRONG_BUY, BUY, STRONG_SELL, SELL)
    actionable = [s for s in signals if s['signal'] != 'NEUTRAL']
    if not actionable:
        print("No actionable signals today")
        return

    # Save as JSON for the trading system
    output = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_signals': len(actionable),
        'signals': actionable
    }

    with open(f"{DATA_DIR}/trading_signals.json", 'w') as f:
        json.dump(output, f, indent=2)

    print(f"💾 Trading signals saved to {DATA_DIR}/trading_signals.json")

if __name__ == "__main__":
    signals = run_all()
    if signals:
        save_to_trading_system(signals)
