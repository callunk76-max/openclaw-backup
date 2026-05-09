"""Batch predict all 28 pairs using Kronos"""
import sys, os, pandas as pd, numpy as np
sys.path.insert(0, "/root/.openclaw/workspace/Kronos")
sys.path.insert(0, os.path.dirname(__file__))
from model import Kronos, KronosTokenizer, KronosPredictor
from config import PAIRS, LOOKBACK, PRED_LEN, MAX_CONTEXT, DATA_DIR

def load_model():
    """Load Kronos model and tokenizer once."""
    print("📥 Loading Kronos-small...")
    tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
    model = Kronos.from_pretrained("NeoQuasar/Kronos-small")
    predictor = KronosPredictor(model, tokenizer, max_context=MAX_CONTEXT)
    print("✅ Model loaded!")
    return predictor

def predict_single(predictor, pair):
    """Predict one pair."""
    fpath = f"{DATA_DIR}/{pair}.csv"
    if not os.path.exists(fpath):
        print(f"  ⏭️  {pair}: No data file")
        return None

    df = pd.read_csv(fpath)
    df['timestamps'] = pd.to_datetime(df['timestamps'])

    if len(df) < LOOKBACK + PRED_LEN:
        print(f"  ⏭️  {pair}: Only {len(df)} rows, need {LOOKBACK + PRED_LEN}")
        return None

    # Use the latest data
    end_idx = len(df) - 1
    start_idx = end_idx - LOOKBACK + 1 - PRED_LEN

    if start_idx < 0:
        start_idx = 0

    lookback_end = start_idx + LOOKBACK

    x_df = df.loc[start_idx:lookback_end-1, ['open', 'high', 'low', 'close', 'volume', 'amount']]
    x_timestamp = df.loc[start_idx:lookback_end-1, 'timestamps']
    y_timestamp = df.loc[lookback_end:lookback_end+PRED_LEN-1, 'timestamps']
    actual = df.loc[lookback_end:lookback_end+PRED_LEN-1, 'close'].values

    try:
        pred_df = predictor.predict(
            df=x_df,
            x_timestamp=x_timestamp,
            y_timestamp=y_timestamp,
            pred_len=PRED_LEN,
            T=1.0,
            top_p=0.9,
            sample_count=1
        )

        # Calculate metrics
        pred_close = pred_df['close'].values
        actual_close = actual[:len(pred_close)]
        mae = np.mean(np.abs(pred_close - actual_close))
        mape = np.mean(np.abs(pred_close - actual_close) / actual_close) * 100

        # Direction accuracy
        pred_dir = pred_close[-1] - x_df['close'].iloc[-1]
        actual_dir = actual_close[-1] - x_df['close'].iloc[-1]
        dir_correct = (pred_dir * actual_dir) > 0

        result = {
            'pair': pair,
            'mae': round(mae, 4),
            'mape': round(mape, 2),
            'direction': 'UP' if pred_dir > 0 else 'DOWN',
            'dir_actual': 'UP' if actual_dir > 0 else 'DOWN',
            'dir_correct': dir_correct,
            'price_now': round(x_df['close'].iloc[-1], 5),
            'price_pred': round(pred_close[-1], 5),
            'price_target': round(pred_close[-1], 5),
            'confidence': round(max(0, 100 - mape * 2), 1),
        }

        print(f"  ✅ {pair}: predict={pred_close[-1]:.5f} | dir={result['direction']} | mape={mape:.1f}% | conf={result['confidence']}%")
        return result

    except Exception as e:
        print(f"  ❌ {pair}: Error - {e}")
        return None

def predict_all():
    """Predict all pairs."""
    predictor = load_model()

    results = []
    print(f"\n🔮 Predicting {len(PAIRS)} pairs (lookback={LOOKBACK}, pred_len={PRED_LEN})...")
    print("=" * 60)

    for pair in PAIRS:
        result = predict_single(predictor, pair)
        if result:
            results.append(result)

    # Save results
    if results:
        rf = pd.DataFrame(results)
        rf.to_csv(f"{DATA_DIR}/predictions.csv", index=False)
        print(f"\n📊 Results saved to {DATA_DIR}/predictions.csv")
        print(f"   {len(results)}/{len(PAIRS)} pairs predicted successfully")
    else:
        print("\n❌ No predictions generated")

    return results

if __name__ == "__main__":
    predict_all()
