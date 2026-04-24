import cloudscraper
import json
import time
import sqlite3
from datetime import datetime

# Konfigurasi
instansi = "D411"
jenis = 4
tahun = 2026
limit = 100
offset = 0
semua_data = []
DB_PATH = '/root/.openclaw/workspace/App/sirup_bulukumba/bulukumba.db'

# Inisialisasi cloudscraper
scraper = cloudscraper.create_scraper()

print(f"🚀 Mulai tarik data tender {instansi} tahun {tahun} menggunakan cloudscraper...")

while True:
    url = f"https://data.inaproc.id/api/tender?instansi={instansi}&jenis={jenis}&limit={limit}&offset={offset}&tahun={tahun}"
    
    try:
        # Menggunakan scraper untuk melewati Cloudflare
        res = scraper.get(url, timeout=30)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        print(f"❌ Error di offset {offset}: {e}")
        break

    items = data.get('data', [])
    total = data.get('total', 0)

    if not items:
        print("✅ Data habis / tidak ada.")
        break

    semua_data.extend(items)
    print(f"📦 Ambil {len(items)} data. Total terkumpul: {len(semua_data)}/{total}")

    if len(semua_data) >= total:
        break

    offset += limit
    time.sleep(2) # Jeda lebih lama agar lebih aman

# Simpan ke JSON untuk backup
nama_file = f"tender_{instansi}_{tahun}_cloud.json"
with open(nama_file, "w", encoding="utf-8") as f:
    json.dump(semua_data, f, ensure_ascii=False, indent=2)

# --- INTEGRASI KE DATABASE ---
print("\n🛠️ Mengimpor data ke bulukumba.db...")
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Hapus data lama agar tidak duplikat
    cursor.execute("DELETE FROM procurement")
    
    # Insert data baru
    # Kita perlu memetakan field dari API Inaproc ke kolom DB kita
    for item in semua_data:
        # Penyesuaian field (Sesuaikan dengan schema DB sirup_bulukumba)
        # source_id, package_name, satker, budget, dll
        cursor.execute('''
            INSERT INTO procurement (
                source_id, package_name, satker, budget, 
                procurement_method, procurement_type, work_description, 
                location_raw, selection_date, funding_source, 
                is_umkm, within_country, volume
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item.get('source_id'), 
            item.get('package_name'), 
            item.get('satker'), 
            item.get('budget'), 
            item.get('procurement_method'), 
            item.get('procurement_type'), 
            item.get('work_description'), 
            item.get('location'), 
            item.get('selection_date'), 
            item.get('funding_source'), 
            item.get('is_umkm'), 
            item.get('within_country'), 
            item.get('volume')
        ))
    
    conn.commit()
    conn.close()
    print(f"✅ Berhasil mengimpor {len(semua_data)} data ke database!")
except Exception as e:
    print(f"❌ Gagal impor ke DB: {e}")

print(f"\nSelesai. Total {len(semua_data)} data tersimpan di {nama_file} dan database.")
