import yfinance as yf
pairs = ["EURUSD=X", "GBPUSD=X"]
data = yf.download(pairs, period="2d", interval="1d", group_by="ticker", auto_adjust=False)
print(data)
