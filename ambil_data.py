import asyncio
from playwright.async_api import async_playwright
import json
import time
from tqdm import tqdm

async def run():
    async with async_playwright() as p:
        # Gunakan headless=False agar Anda bisa melihat prosesnya dan membantu jika ada Cloudflare
        browser = await p.chromium.launch(headless=False) 
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        
        page = await context.new_page()
        
        # URL yang diberikan oleh user (Halaman Web RUP, bukan API)
        url = "https://data.inaproc.id/rup?jenis_klpd=4&instansi=D411"
        
        print(f"🚀 Membuka halaman RUP Inaproc: {url}")
        
        try:
            # Pergi ke halaman dan tunggu sampai network idle
            await page.goto(url, wait_until="networkidle")
            
            # Beri waktu tambahan untuk render JavaScript
            await asyncio.sleep(5)
            
            # Cek apakah kita terblokir Cloudflare
            if "Cloudflare" in await page.title() or await page.query_selector("text=Verify you are human"):
                print("\n⚠️ Cloudflare Challenge terdeteksi!")
                print("Silakan centang 'I am human' di jendela browser yang terbuka...")
                # Tunggu sampai user menyelesaikan challenge (timeout 60 detik)
                try:
                    await page.wait_for_selector("table", timeout=60000)
                    print("✅ Challenge selesai! Melanjutkan penarikan data...")
                except:
                    print("❌ Timeout: Challenge tidak selesai.")
                    await browser.close()
                    return

        except Exception as e:
            print(f"❌ Gagal membuka halaman: {e}")
            await browser.close()
            return

        semua_data = []
        page_num = 1
        
        print("📊 Mengekstrak data dari tabel...")
        
        while True:
            print(f"📄 Mengambil data halaman {page_num}...")
            
            # Tunggu tabel muncul
            try:
                await page.wait_for_selector("table", timeout=10000)
            except:
                print("❌ Tabel tidak ditemukan di halaman ini.")
                break
            
            # Ambil semua baris dari tabel (lewati header)
            rows = await page.query_selector_all("table tbody tr")
            
            if not rows:
                print("✅ Tidak ada baris data lagi.")
                break
                
            for row in rows:
                cols = await row.query_selector_all("td")
                if len(cols) >= 3:
                    # Mapping kolom (berdasarkan struktur umum tabel RUP)
                    # Kolom biasanya: No, Paket, Satker, Anggaran, dll
                    data = {
                        "package_name": await cols[1].inner_text(),
                        "satker": await cols[2].inner_text(),
                        "budget": await cols[3].inner_text(),
                        "page": page_num
                    }
                    semua_data.append(data)
            
            # Cari tombol "Next" atau tanda panah kanan
            next_button = await page.query_selector("a:has-text('Next'), button:has-text('Next'), .pagination-next, [aria-label='Next']")
            
            if next_button:
                await next_button.click()
                page_num += 1
                await asyncio.sleep(3) # Jeda antar halaman
            else:
                print("✅ Sudah mencapai halaman terakhir.")
                break
        
        # Simpan hasil ke file JSON
        with open(f"rup_bulukumba_extracted.json", "w", encoding="utf-8") as f:
            json.dump(semua_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n🎉 Selesai! Berhasil mengambil {len(semua_data)} data paket.")
        print(f"Data tersimpan di rup_bulukumba_extracted.json")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
