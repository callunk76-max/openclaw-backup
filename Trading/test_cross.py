import requests

API_KEY = "5668c0334bdf4694a7ee8e3f2169c520"
BASE_URL = "https://api.twelvedata.com"
# Only the 7 USD major pairs!
USD_PAIRS = ["EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD", "USD/CAD", "USD/CHF", "USD/JPY"]

url = f"{BASE_URL}/time_series?symbol={','.join(USD_PAIRS)}&interval=1day&outputsize=2&apikey={API_KEY}"
response = requests.get(url).json()

data_store = {}
for pair in USD_PAIRS:
    pair_data = response.get(pair)
    if pair_data and "values" in pair_data and len(pair_data["values"]) >= 2:
        today = pair_data["values"][0]
        yesterday = pair_data["values"][1]
        data_store[pair] = {
            "close": float(today["close"]),
            "high": float(yesterday["high"]),
            "low": float(yesterday["low"])
        }

print("EUR/USD:", data_store["EUR/USD"])
print("USD/JPY:", data_store["USD/JPY"])

# Calculate EUR/JPY synthetic
eur_jpy_h = data_store["EUR/USD"]["high"] * data_store["USD/JPY"]["high"]
eur_jpy_l = data_store["EUR/USD"]["low"] * data_store["USD/JPY"]["low"]
eur_jpy_c = data_store["EUR/USD"]["close"] * data_store["USD/JPY"]["close"]
print(f"Synthetic EUR/JPY -> H: {eur_jpy_h:.2f}, L: {eur_jpy_l:.2f}, C: {eur_jpy_c:.2f}")

# Compare to actual EUR/JPY
url_actual = f"{BASE_URL}/time_series?symbol=EUR/JPY&interval=1day&outputsize=2&apikey={API_KEY}"
res_actual = requests.get(url_actual).json()
act = res_actual["values"]
print(f"Actual EUR/JPY -> H: {float(act[1]['high']):.2f}, L: {float(act[1]['low']):.2f}, C: {float(act[0]['close']):.2f}")
