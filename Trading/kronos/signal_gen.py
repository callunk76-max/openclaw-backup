"""Generate BUY/SELL signals from Kronos predictions"""
import sys, os, json
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from config import PAIRS, DATA_DIR, SIGNAL_FILE

def generate_signals(predictions_file=None):
    """Generate BUY/SELL signals from Kronos prediction results."""
    if predictions_file is None:
        predictions_file = f"{DATA_DIR}/predictions.csv"

    if not os.path.exists(predictions_file):
        print(f"❌ No predictions file found at {predictions_file}")
        return []

    df = pd.read_csv(predictions_file)

    signals = []
    for _, row in df.iterrows():
        pair = row['pair']
        prediction = row['price_pred']
        current = row['price_now']
        mape = row['mape']
        direction = row['direction']
        confidence = row['confidence']

        # Signal logic:
        # - Strong BUY: UP prediction + confidence > 70% + mape < 3%
        # - BUY: UP prediction + confidence > 50%
        # - Strong SELL: DOWN prediction + confidence > 70% + mape < 3%
        # - SELL: DOWN prediction + confidence > 50%
        # - NEUTRAL: otherwise

        change_pct = abs(prediction - current) / current * 100

        signal = "NEUTRAL"
        strength = "LOW"

        if direction == "UP" and confidence >= 70 and change_pct > 0.1:
            signal = "STRONG_BUY"
            strength = "HIGH"
        elif direction == "UP" and confidence >= 50:
            signal = "BUY"
            strength = "MEDIUM"
        elif direction == "DOWN" and confidence >= 70 and change_pct > 0.1:
            signal = "STRONG_SELL"
            strength = "HIGH"
        elif direction == "DOWN" and confidence >= 50:
            signal = "SELL"
            strength = "MEDIUM"

        signals.append({
            'pair': pair,
            'signal': signal,
            'strength': strength,
            'current_price': current,
            'predicted_price': round(prediction, 5),
            'change_pct': round(change_pct, 3),
            'confidence': confidence,
            'mape': mape,
            'direction': direction,
        })

    # Save signals
    sf = pd.DataFrame(signals)
    sf.to_csv(SIGNAL_FILE, index=False)

    # Summary
    strong_buys = [s for s in signals if s['signal'] == 'STRONG_BUY']
    buys = [s for s in signals if s['signal'] == 'BUY']
    strong_sells = [s for s in signals if s['signal'] == 'STRONG_SELL']
    sells = [s for s in signals if s['signal'] == 'SELL']
    neutrals = [s for s in signals if s['signal'] == 'NEUTRAL']

    print(f"\n📊 SIGNALS GENERATED")
    print("=" * 50)
    print(f"🟢 STRONG BUY : {len(strong_buys)}")
    for s in strong_buys:
        print(f"   {s['pair']} → {s['predicted_price']} ({s['change_pct']}%)")
    print(f"🟢 BUY        : {len(buys)}")
    for s in buys:
        print(f"   {s['pair']} → {s['predicted_price']} ({s['change_pct']}%)")
    print(f"🔴 SELL       : {len(sells)}")
    for s in sells:
        print(f"   {s['pair']} → {s['predicted_price']} ({s['change_pct']}%)")
    print(f"🔴 STRONG SELL: {len(strong_sells)}")
    for s in strong_sells:
        print(f"   {s['pair']} → {s['predicted_price']} ({s['change_pct']}%)")
    print(f"⚪ NEUTRAL    : {len(neutrals)}")
    print(f"\n💾 Saved to {SIGNAL_FILE}")

    return signals

def get_signal_summary():
    """Get short text summary for Telegram."""
    if not os.path.exists(SIGNAL_FILE):
        return "❌ Belum ada sinyal. Jalanin batch_predict dulu."

    df = pd.read_csv(SIGNAL_FILE)
    strong_buys = df[df['signal'] == 'STRONG_BUY']
    buys = df[df['signal'] == 'BUY']
    strong_sells = df[df['signal'] == 'STRONG_SELL']
    sells = df[df['signal'] == 'SELL']

    msg = "📊 *Kronos Signals*\n"
    if not strong_buys.empty:
        msg += f"\n🟢 *STRONG BUY ({len(strong_buys)})*\n"
        for _, r in strong_buys.iterrows():
            msg += f"  {r['pair']} → {r['predicted_price']} ({r['change_pct']}%)\n"
    if not buys.empty:
        msg += f"\n🟢 *BUY ({len(buys)})*\n"
        for _, r in buys.iterrows():
            msg += f"  {r['pair']} → {r['predicted_price']} ({r['change_pct']}%)\n"
    if not strong_sells.empty:
        msg += f"\n🔴 *STRONG SELL ({len(strong_sells)})*\n"
        for _, r in strong_sells.iterrows():
            msg += f"  {r['pair']} → {r['predicted_price']} ({r['change_pct']}%)\n"
    if not sells.empty:
        msg += f"\n🔴 *SELL ({len(sells)})*\n"
        for _, r in sells.iterrows():
            msg += f"  {r['pair']} → {r['predicted_price']} ({r['change_pct']}%)\n"

    return msg

if __name__ == "__main__":
    generate_signals()
