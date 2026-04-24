import requests
import json
import time
from datetime import datetime

instansi = "D411" # Kode instansi
jenis = 4 # 4 = Tender
tahun = 2026 # Filter tahun
limit = 100
offset = 0
semua_data = []

print(f"Mulai tarik data tender {instansi} tahun {tahun}...")

while True:
    url = f"https://data.inaproc.id/api/tender?instansi={instansi}&jenis={jenis}&limit={limit}&offset={offset}&tahun={tahun}"

    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        print(f"Error di offset {offset}: {e}")
        break

    items = data.get('data', [])
    total = data.get('total', 0)

    if not items:
        print("Data 2026 habis / tidak ada.")
        break

    semua_data.extend(items)
    print(f"Ambil {len(items)} data. Total 2026 terkumpul: {len(semua_data)}/{total}")

    if len(semua_data) >= total:
        break

    offset += limit
    time.sleep(1.5) # jeda biar gak kena blok Cloudflare

# Simpan ke file JSON
nama_file = f"tender_{instansi}_{tahun}.json"
with open(nama_file, "w", encoding="utf-8") as f:
    json.dump(semua_data, f, ensure_ascii=False, indent=2)

print(f"\nSelesai. Total {len(semua_data)} data tahun {tahun} tersimpan di {nama_file}")
