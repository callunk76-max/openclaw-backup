#!/usr/bin/env python3
"""Comprehensive H1 data analysis for 28 pairs + Gold."""
import pandas as pd
import numpy as np
import json
from pathlib import Path

DATA_DIR = Path("/root/.openclaw/workspace/Trading/data_h1")
RESULTS = {}

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period, min_periods=period).mean()
    avg_loss = loss.rolling(period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def calc_atr(df, period=14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def analyze_pair(fname):
    pair = fname.replace("_H1.csv", "")
    df = pd.read_csv(DATA_DIR / fname)
    df.columns = [c.strip() for c in df.columns]
    df["Time"] = pd.to_datetime(df["Time"], format="%Y.%m.%d %H:%M")
    df = df.sort_values("Time").reset_index(drop=True)
    
    n = len(df)
    price = df["Close"]
    
    # Basic stats
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    change = latest["Close"] - prev["Close"]
    change_pct = (change / prev["Close"]) * 100
    
    # Volatility (ATR)
    atr14 = calc_atr(df)
    curr_atr = atr14.iloc[-1]
    avg_price = price.mean()
    atr_pct = (curr_atr / avg_price) * 100
    
    # RSI
    rsi14 = calc_rsi(price)
    curr_rsi = rsi14.iloc[-1]
    
    # SMA
    sma20 = price.rolling(20).mean().iloc[-1]
    sma50 = price.rolling(50).mean().iloc[-1]
    sma200 = price.rolling(200).mean().iloc[-1]
    
    # Trend direction
    trend = "UP" if sma20 > sma50 > sma200 else ("DOWN" if sma20 < sma50 < sma200 else "SIDEWAYS/SHUFFLE")
    
    # Price vs SMAs
    above_sma20 = "YES" if latest["Close"] > sma20 else "NO"
    above_sma50 = "YES" if latest["Close"] > sma50 else "NO"
    above_sma200 = "YES" if latest["Close"] > sma200 else "NO"
    
    # Support/Resistance (last 100 candles)
    recent = df.tail(100)
    recent_highs = recent["High"]
    recent_lows = recent["Low"]
    
    # Multi-timeframe S/R using pivot logic
    pivot = (recent["High"] + recent["Low"] + recent["Close"]) / 3
    r1 = 2 * pivot - recent["Low"]
    s1 = 2 * pivot - recent["High"]
    
    curr_res = r1.iloc[-1]
    curr_sup = s1.iloc[-1]
    nearest_res = recent_highs.max()
    nearest_sup = recent_lows.min()
    
    # Volume analysis
    avg_vol = df["Volume"].mean()
    latest_vol = latest["Volume"]
    vol_ratio = latest_vol / avg_vol if avg_vol > 0 else 1
    
    # Recent price range (last 20 vs full)
    last20_range = recent["High"].max() - recent["Low"].min()
    full_range = df["High"].max() - df["Low"].min()
    range_pct = (last20_range / full_range) * 100 if full_range > 0 else 0
    
    # MACD
    ema12 = price.ewm(span=12).mean()
    ema26 = price.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    macd_hist = macd - signal
    macd_bull = "BULL" if macd.iloc[-1] > signal.iloc[-1] else "BEAR"
    hist_trend = "STRENGTHENING" if macd_hist.iloc[-1] > macd_hist.iloc[-2] else "WEAKENING"
    
    # Bollinger Bands (20,2)
    bb_mid = sma20
    bb_std = price.rolling(20).std()
    bb_upper = bb_mid + 2 * bb_std.iloc[-1]
    bb_lower = bb_mid - 2 * bb_std.iloc[-1]
    bb_pos = (latest["Close"] - bb_lower) / (bb_upper - bb_lower) * 100  # 0=lower, 100=upper
    
    # RSI extremes count (last 50)
    last50_rsi = rsi14.tail(50)
    oversold_count = (last50_rsi < 30).sum()
    overbought_count = (last50_rsi > 70).sum()
    
    results = {
        "pair": pair,
        "n_candles": n,
        "date_from": str(df["Time"].iloc[0]),
        "date_to": str(df["Time"].iloc[-1]),
        "latest_close": round(latest["Close"], 5),
        "change_1h": round(change, 5),
        "change_pct_1h": round(change_pct, 3),
        "high_24h": round(recent_highs.tail(24).max(), 5),
        "low_24h": round(recent_lows.tail(24).min(), 5),
        "rsi_14": round(curr_rsi, 1),
        "atr_14": round(curr_atr, 5),
        "atr_pct": round(atr_pct, 3),
        "sma_20": round(sma20, 5),
        "sma_50": round(sma50, 5),
        "sma_200": round(sma200, 5),
        "above_sma20": above_sma20,
        "above_sma50": above_sma50,
        "above_sma200": above_sma200,
        "trend": trend,
        "bb_upper": round(bb_upper, 5),
        "bb_lower": round(bb_lower, 5),
        "bb_position_pct": round(bb_pos, 1),
        "macd_signal": macd_bull,
        "macd_trend": hist_trend,
        "nearest_resistance_100": round(nearest_res, 5),
        "nearest_support_100": round(nearest_sup, 5),
        "pivot_resistance": round(curr_res, 5),
        "pivot_support": round(curr_sup, 5),
        "volume_ratio_vs_avg": round(vol_ratio, 2),
        "volatility_rank_20_100": f"{round(range_pct, 1)}%",
        "oversold_50candles": int(oversold_count),
        "overbought_50candles": int(overbought_count),
        "volume": int(latest_vol)
    }
    return pair, results

# Analyze all pairs
files = sorted(DATA_DIR.glob("*_H1.csv"))
print(f"Analyzing {len(files)} pairs...\n")
all_results = {}

for f in files:
    try:
        pair, res = analyze_pair(f.name)
        all_results[pair] = res
    except Exception as e:
        print(f"ERROR: {f.name} -> {e}")

# Save JSON
with open(DATA_DIR / "analysis_results.json", "w") as fp:
    json.dump(all_results, fp, indent=2)

# ============ PRINT SUMMARY TABLE ============
print(f"{'PAIR':<12} {'CLOSE':>10} {'CHG%':>7} {'RSI14':>6} {'ATR%':>7} {'TREND':<20} {'MACD':<10} {'VOL':>6} {'S/R':<30}")
print("=" * 115)

trending_up = []
trending_down = []
oversold = []
overbought = []
for pair, r in sorted(all_results.items()):
    chg = f"{r['change_pct_1h']:+.2f}%"
    sr = f"S:{r['nearest_support_100']} R:{r['nearest_resistance_100']}"
    macd_str = f"{r['macd_signal']}/{r['macd_trend']}"
    print(f"{pair:<12} {r['latest_close']:>10} {chg:>7} {r['rsi_14']:>6} {r['atr_pct']:>6}% {r['trend']:<20} {macd_str:<10} {r['volume_ratio_vs_avg']:>5.1f}x {sr:<30}")
    
    if "UP" in r['trend']:
        trending_up.append(pair)
    elif "DOWN" in r['trend']:
        trending_down.append(pair)
    if r['rsi_14'] < 35:
        oversold.append((pair, r['rsi_14']))
    if r['rsi_14'] > 65:
        overbought.append((pair, r['rsi_14']))

print(f"\n{'='*115}")
print(f"\n📈 BULLISH TREND: {len(trending_up)} pairs")
print(", ".join(trending_up[:15]) + ("..." if len(trending_up) > 15 else ""))
print(f"\n📉 BEARISH TREND: {len(trending_down)} pairs")
print(", ".join(trending_down[:15]) + ("..." if len(trending_down) > 15 else ""))
print(f"\n⚡ OVERSOLD (RSI < 35): {oversold}")
print(f"⚡ OVERBOUGHT (RSI > 65): {overbought}")

# ============ STRATEGY INSIGHTS ============
print("\n\n" + "="*80)
print("                 STRATEGY INSIGHTS")
print("="*80)

# 1. Volatility leaders
vol_ranked = sorted(all_results.items(), key=lambda x: x[1]["atr_pct"], reverse=True)
print("\n🔥 HIGHEST VOLATILITY (ATR%):")
for p, r in vol_ranked[:6]:
    print(f"  {p:<10} ATR: {r['atr_pct']}%  |  RSI: {r['rsi_14']}  |  Trend: {r['trend']}")

print("\n❄️  LOWEST VOLATILITY (ATR%):")
for p, r in vol_ranked[-6:]:
    print(f"  {p:<10} ATR: {r['atr_pct']}%  |  RSI: {r['rsi_14']}  |  Trend: {r['trend']}")

# 2. Momentum plays (strong MACD + volume)
print("\n🚀 STRONG MOMENTUM (MACD Bull + Volume > avg):")
for p, r in sorted(all_results.items(), key=lambda x: x[1]["volume_ratio_vs_avg"], reverse=True):
    if r['macd_signal'] == 'BULL' and r['volume_ratio_vs_avg'] > 1.2:
        print(f"  {p:<10} Vol: {r['volume_ratio_vs_avg']:.1f}x  RSI: {r['rsi_14']}  ATR: {r['atr_pct']}%")

print("\n💀 BEARISH MOMENTUM (MACD Bear + Volume > avg):")
for p, r in sorted(all_results.items(), key=lambda x: x[1]["volume_ratio_vs_avg"], reverse=True):
    if r['macd_signal'] == 'BEAR' and r['volume_ratio_vs_avg'] > 1.2:
        print(f"  {p:<10} Vol: {r['volume_ratio_vs_avg']:.1f}x  RSI: {r['rsi_14']}  ATR: {r['atr_pct']}%")

# 3. Mean reversion candidates
print("\n🔄 MEAN REVERSION CANDIDATES (BB extremes):")
for p, r in sorted(all_results.items(), key=lambda x: abs(50 - x[1]['bb_position_pct']), reverse=True):
    if r['bb_position_pct'] > 90 or r['bb_position_pct'] < 10:
        direction = "OVERBOUGHT (short)" if r['bb_position_pct'] > 90 else "OVERSOLD (long)"
        print(f"  {p:<10} BB Position: {r['bb_position_pct']:.0f}%  |  {direction}  |  RSI: {r['rsi_14']}")

print("\n✅ Analysis complete. Results saved to analysis_results.json")
