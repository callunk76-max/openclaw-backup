import requests
import json
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
url = "https://query1.finance.yahoo.com/v8/finance/chart/EURUSD=X?interval=1d&range=2d"
res = requests.get(url, headers=headers)
print(res.status_code)
if res.status_code == 200:
    data = res.json()
    print(data['chart']['result'][0]['meta']['symbol'])
