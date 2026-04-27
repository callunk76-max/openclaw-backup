import yfinance as yf
import pandas as pd

PAIRS = [
    "EURUSD=X", "GBPUSD=X", "AUDUSD=X", "NZDUSD=X", "USDCAD=X", "USDCHF=X", "USDJPY=X",
    "EURGBP=X", "EURJPY=X", "EURCAD=X", "EURCHF=X", "EURAUD=X", "EURNZD=X",
    "GBPJPY=X", "GBPCAD=X", "GBPCHF=X", "GBPAUD=X", "GBPNZD=X",
    "AUDJPY=X", "AUDCAD=X", "AUDCHF=X", "AUDNZD=X",
    "NZDJPY=X", "NZDCAD=X", "NZDCHF=X",
    "CADJPY=X", "CADCHF=X", "CHFJPY=X"
]

try:
    # Try downloading just 2 pairs with history
    data = yf.download("EURUSD=X GBPUSD=X", period="2d", interval="1d", group_by="ticker", auto_adjust=False, progress=False)
    print("YF Data:")
    print(data)
except Exception as e:
    print("YF Error:", e)
