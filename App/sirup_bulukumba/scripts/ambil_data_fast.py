import asyncio
from playwright.async_api import async_playwright
import json
import time
from tqdm import tqdm

async def run():
    async with async_playwright() as p:
        # Gunakan headless=False agar Anda bisa melihat prosesnya
        browser = await p.chromium.launch(headless=False) 
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        
        page = await context.new_page()
        url = "https://data.inaproc.id/rup?jenis_klpd=4&instansi=D411"
        
        print(f"🚀 Membuka halaman RUP Inaproc: {url}")
        
        try:
            await page.goto(url, wait_until="networkidle")
            await asyncio.sleep(5)
            
            if "Cloudflare" in await page.title() or await page.query_selector("text=Verify you are human"):
                print("\n⚠️ Cloudflare Challenge terdeteksi!")
                print("Silakan centang 'I am human' di jendela browser yang terbuka...")
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

        # --- OPTIMASI: UBAH ENTRI PER HALAMAN KE 100 ---
        try:
            print("⚙️ Mengatur entri per halaman ke 100...")
            entry_dropdown = await page.query_selector("select") 
            if entry_dropdown:
                await entry_dropdown.select_option("100")
                await asyncio.sleep(3) 
                print("✅ Berhasil mengubah entri ke 100!")
            else:
                print("⚠️ Dropdown entri tidak ditemukan, menggunakan default (20).")
        except Exception as e:
            print(f"⚠️ Gagal mengubah entri: {e}")

        semua_data = []
        page_num = 1
        
        print("📊 Mengekstrak data dari tabel...")
        
        while True:
            print(f"📄 Mengambil data halaman {page_num}...")
            
            try:
                await page.wait_for_selector("table", timeout=10000)
            except:
                print("❌ Tabel tidak ditemukan di halaman ini.")
                break
            
            rows = await page.query_selector_all("table tbody tr")
            if not rows:
                print("✅ Tidak ada baris data lagi.")
                break
                
            for row in rows:
                cols = await row.query_selector_all("td")
                if len(cols) >= 3:
                    data = {
                        "package_name": await cols[1].inner_text(),
                        "satker": await cols[2].inner_text(),
                        "budget": await cols[3].inner_text(),
                        "page": page_num
                    }
                    semua_data.append(data)
            
            # Cari tombol 'Berikutnya'
            next_button = await page.query_selector("a:has-text('Berikutnya'), button:has-text('Berikutnya'), a:has-text('>')")
            
            if next_button:
                await next_button.click()
                page_num += 1
                await asyncio.sleep(3) 
            else:
                print("✅ Sudah mencapai halaman terakhir atau tombol 'Berikutnya' tidak ditemukan.")
                break
        
        with open(f"rup_bulukumba_fast_extracted.json", "w", encoding="utf-8") as f:
            json.dump(semua_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n🎉 Selesai! Berhasil mengambil {len(semua_data)} data paket.")
        print(f"Data tersimpan di rup_bulukumba_fast_extracted.json")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
