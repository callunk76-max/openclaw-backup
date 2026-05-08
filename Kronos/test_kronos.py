"""Quick Kronos prediction test using available sample data"""
import sys, pandas as pd, numpy as np
sys.path.insert(0, '/root/.openclaw/workspace/Kronos')
from model import Kronos, KronosTokenizer, KronosPredictor

# 1. Load Model and Tokenizer
print("Downloading tokenizer...")
tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
print("Downloading model (Kronos-small)...")
model = Kronos.from_pretrained("NeoQuasar/Kronos-small")
print("Model loaded!")

# 2. Init Predictor
predictor = KronosPredictor(model, tokenizer, max_context=512)

# 3. Prepare Data from finetune_csv sample
df = pd.read_csv("/root/.openclaw/workspace/Kronos/finetune_csv/data/HK_ali_09988_kline_5min_all.csv")
df['timestamps'] = pd.to_datetime(df['timestamps'])
print(f"Data loaded: {len(df)} rows, columns: {list(df.columns)}")
print(f"Date range: {df['timestamps'].min()} to {df['timestamps'].max()}")
print(f"Close price range: {df['close'].min():.2f} - {df['close'].max():.2f}")

lookback = 200
pred_len = 60

x_df = df.loc[:lookback-1, ['open', 'high', 'low', 'close', 'volume', 'amount']]
x_timestamp = df.loc[:lookback-1, 'timestamps']
y_timestamp = df.loc[lookback:lookback+pred_len-1, 'timestamps']

print(f"\nMaking prediction with {lookback} lookback, {pred_len} steps ahead...")

# 4. Predict
pred_df = predictor.predict(
    df=x_df,
    x_timestamp=x_timestamp,
    y_timestamp=y_timestamp,
    pred_len=pred_len,
    T=1.0,
    top_p=0.9,
    sample_count=1,
    verbose=True
)

print("\n✅ Prediction complete!")
print("\n=== Forecast Results (Close Price) ===")
results = pd.DataFrame({
    'date': y_timestamp,
    'actual': df.loc[lookback:lookback+pred_len-1, 'close'].values,
    'predicted': pred_df['close'].values
})
results['error_pct'] = abs(results['predicted'] - results['actual']) / results['actual'] * 100
print(results.head(10))
print(f"...\nMean Absolute Error: {np.mean(abs(results['predicted'] - results['actual'])):.4f}")
print(f"Mean Error %: {results['error_pct'].mean():.2f}%")
