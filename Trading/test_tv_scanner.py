import requests

PAIRS = [
    "EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY",
    "EURGBP", "EURJPY", "EURCAD", "EURCHF", "EURAUD", "EURNZD",
    "GBPJPY", "GBPCAD", "GBPCHF", "GBPAUD", "GBPNZD",
    "AUDJPY", "AUDCAD", "AUDCHF", "AUDNZD",
    "NZDJPY", "NZDCAD", "NZDCHF",
    "CADJPY", "CADCHF", "CHFJPY"
]

tickers = [f"OANDA:{p}" for p in PAIRS]

payload = {
    "symbols": {"tickers": tickers},
    "columns": ["close", "high[1]", "low[1]"]
}

url = "https://scanner.tradingview.com/forex/scan"
response = requests.post(url, json=payload).json()

for row in response.get("data", []):
    print(row["s"], row["d"])
