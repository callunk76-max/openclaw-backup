import requests

API_KEY = "5668c0334bdf4694a7ee8e3f2169c520"
BASE_URL = "https://api.twelvedata.com"
PAIRS = ["EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD", "USD/CAD", "USD/CHF", "USD/JPY"]

url = f"{BASE_URL}/time_series?symbol={','.join(PAIRS)}&interval=1day&outputsize=2&apikey={API_KEY}"
response = requests.get(url).json()

for pair in PAIRS:
    data = response.get(pair, {}).get("values", [])
    if len(data) == 2:
        print(f"{pair}: Today close={data[0]['close']}, Yest H={data[1]['high']} L={data[1]['low']}")
