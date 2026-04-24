import asyncio
from playwright.async_api import async_playwright
import json
import time
from tqdm import tqdm

async def run():
    print("🛠️ Menginisialisasi Playwright (Mode Ultra-Stable)...")
    async with async_//playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True) 
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )
            page = await context.new_page()
            
            await page.set_extra_http_headers({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "max-age=0",
                "Upgrade-Insecure-Requests": "1"
            })
            
            url = "https://data.inaproc.id/rup?jenis_klpd=4&instansi=D411"
            print(f"🌐 Menghubungi server Inaproc...")
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                print(f"✅ Koneksi berhasil.")
            except Exception as e:
                print(f"⚠️ Timeout awal: {e}. Mencoba lanjut...")
            
            await asyncio.sleep(10)
            
            if not await page.query_selector("table"):
                print("❌ Tabel tidak ditemukan. Kemungkinan terblokir Cloudflare.")
                await browser.close()
                return
            
            print("📊 Tabel terdeteksi! Memulai ekstraksi data...")
            
            try:
                dropdown = await page.query_selector("select")
                if dropdown:
                    await dropdown.select_option("100")
                    await asyncio.sleep(3)
                    print("✅ Entri diubah ke 100.")
            except:
                print("⚠️ Menggunakan entri default.")

            semua_data = []
            page_num = 1
            
            while True:
                print(f"📄 Mengambil data halaman {page_num}...", end="\r")
                
                # RETRY MECHANISM: Coba sampai 3 kali jika halaman gagal load
                success = False
                for attempt in range(3):
                    try:
                        await page.wait_for_selector("table", timeout=15000)
                        rows = await page.query_selector_all("table tbody tr")
                        if rows:
                            for row in rows:
                                cols = await row.query_selector_all("td")
                                if len(cols) >= 3:
                                    semua_data.append({
                                        "package_name": await cols[1].inner_text(),
                                        "satker": await cols[2].inner_text(),
                                        "budget": await cols[3].inner_text(),
                                        "page": page_num
                                    })
                            success = True
                            break
                    except Exception as e:
                        print(f"\n⚠️ Percobaan {attempt+1}/3 gagal di hal {page_num}: {e}")
                        await asyncio.sleep(5 * (attempt + 1))
                        await page.reload(wait_until="domcontentloaded")
                
                if not success:
                    print(f"\n❌ Gagal mengambil halaman {page_num} setelah 3 kali coba. Melewati halaman ini...")
                
                # SIMPAN PERIODIK: Simpan setiap 5 halaman agar data tidak hilang jika crash
                if page_num % 5 == 0:
                    with open("rup_bulukumba_backup.json", "w", encoding="utf-8") as f:
                        json.dump(semua_data, f, ensure_ascii=False, indent=2)
                
                next_btn = await page.query_selector("a:has-text('Berikutnya'), button:has-text('Berikutnya'), a:has-text('>')")
                if next_btn:
                    await next_btn.click()
                    page_num += 1
                    await asyncio.sleep(5) # Jeda lebih lama agar lebih stabil
                else:
                    print("\n✅ Sudah mencapai halaman terakhir.")
                    break
            
            with open("rup_bulukumba_final.json", "w", encoding="utf-8") as f:
                json.dump(semua_data, f, ensure_ascii=False, indent=2)
                
            print(f"\n🎉 SELESAI! Total {len(semua_data)} data tersimpan di rup_bulukumba_final.json")
            
        except Exception as e:
            print(f"💥 CRITICAL ERROR: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
