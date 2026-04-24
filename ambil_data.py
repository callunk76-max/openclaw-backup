import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import json
import time
from tqdm import tqdm

async def run():
    async with async_playwright() as p:
        # headless=True agar berjalan di background.
        # Ubah ke False jika ingin melihat browsernya terbuka.
        browser = await p.chromium.launch(headless=True) 
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        page = await context.new_page()
        
        # Mengaktifkan stealth mode
        try:
            await stealth_async(page)
        except Exception:
            from playwright_stealth import stealth
            await stealth(page)
        
        instansi = "D411"
        tahun = 2026
        limit = 100
        offset = 0
        semua_data = []
        
        print(f"🚀 Memulai penarikan data Inaproc untuk {instansi} tahun {tahun}...")
        
        # Request pertama untuk mendapatkan total data
        try:
            url_init = f"https://data.inaproc.id/api/tender?instansi={instansi}&jenis=4&limit={limit}&offset=0&tahun={tahun}"
            response = await page.goto(url_init, wait_until="networkidle")
            text = await page.inner_text('body')
            initial_data = json.loads(text)
            total_data = initial_data.get('total', 0)
        except Exception as e:
            print(f"❌ Gagal koneksi awal: {e}")
            await browser.close()
            return

        if total_data == 0:
            print("✅ Tidak ada data ditemukan.")
            await browser.close()
            return

        print(f"📊 Total data yang ditemukan: {total_data}")
        
        # Inisialisasi Progres Bar
        pbar = tqdm(total=total_data, desc="Downloading Data", unit="pkg")
        
        # Masukkan data dari request pertama
        first_items = initial_data.get('data', [])
        semua_data.extend(first_items)
        pbar.update(len(first_items))

        offset = limit
        while len(semua_data) < total_data:
            url = f"https://data.inaproc.id/api/tender?instansi={instansi}&jenis=4&limit={limit}&offset={offset}&tahun={tahun}"
            
            try:
                response = await page.goto(url, wait_until="networkidle")
                if response.status == 403:
                    await asyncio.sleep(5)
                    continue
                
                text = await page.inner_text('body')
                json_data = json.loads(text)
                items = json_data.get('data', [])
                
                if not items:
                    break
                    
                semua_data.extend(items)
                pbar.update(len(items))
                
            except Exception as e:
                print(f"\n⚠️ Error di offset {offset}: {e}")
                await asyncio.sleep(5)
                continue
                
            offset += limit
            await asyncio.sleep(2)
            
        pbar.close()
        
        # Simpan hasil ke file JSON
        with open(f"tender_{instansi}_{tahun}.json", "w", encoding="utf-8") as f:
            json.dump(semua_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n🎉 Selesai! Total {len(semua_data)} data tersimpan di tender_{instansi}_{tahun}.json")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
