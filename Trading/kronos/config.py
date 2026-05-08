"""Config — Kronos x Callunk H1 Trading"""

# ===== 28 PAIRS + XAUUSD =====
PAIRS = [
    "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD",
    "CADCHF", "CADJPY", "CHFJPY",
    "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD", "EURUSD",
    "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
    "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD",
    "USDCAD", "USDCHF", "USDJPY",
    "XAUUSD"  # Gold
]

# ===== KRONOS H1 SETTINGS =====
LOOKBACK = 240       # 240 jam (~10 days history)
PRED_LEN = 24        # 24 jam prediksi ke depan
TIMEFRAME = "1h"     # H1 (1 hour candles)
MAX_CONTEXT = 512

# ===== DATA SOURCE =====
# TwelveData free tier: 8 calls/min, 5000 data points per call
TWELVEDATA_KEY = "5668c0334bdf4694a7ee8e3f2169c520"

# ===== PATHS =====
DATA_DIR = "/root/.openclaw/workspace/Trading/kronos/data"
KRONOS_REPO = "/root/.openclaw/workspace/Kronos"
SIGNAL_FILE = f"{DATA_DIR}/signals.csv"
