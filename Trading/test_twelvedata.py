import requests

API_KEY = "5668c0334bdf4694a7ee8e3f2169c520"
BASE_URL = "https://api.twelvedata.com"
PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY"]

url = f"{BASE_URL}/time_series?symbol={','.join(PAIRS)}&interval=1day&outputsize=1&apikey={API_KEY}"
print(url)
response = requests.get(url).json()
for pair, data in response.items():
    print(pair, "->", data.get("values", [{}])[0])
