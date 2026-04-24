import asyncio
from playwright.async_api import async_playwright
import json
import time
from tqdm import tqdm

async def run():
    print("🛠️ Menginisialisasi Playwright...")
    async with async_playwright() as p:
        try:
            # Gunakan headless=True agar tidak tergantung pada Display/X11 di WSL
            browser = await p.chromium.launch(headless=True) 
            print("✅ Browser berhasil diluncurkan.")
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )
            page = await context.new_page()
            print("✅ Halaman baru berhasil dibuka.")
            
            url = "https://data.inaproc.id/rup?jenis_klpd=4&instansi=D411"
            print(f"🌐 Mencoba mengakses: {url} ...")
            
            # Gunakan domcontentloaded agar lebih cepat dan tidak menunggu semua asset
            response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            print(f"✅ Halaman terbuka dengan status: {response.status}")
            
            # Beri waktu untuk render JS
            await asyncio.sleep(5)
            
            # Cek apakah ada tabel
            if not await page.query_selector("table"):
                print("❌ Tabel tidak ditemukan. Kemungkinan terblokir Cloudflare atau halaman kosong.")
                await browser.close()
                return
            
            print("📊 Tabel ditemukan! Mulai ekstraksi data...")
            
            # Atur entri per halaman ke 100 jika memungkinkan
            try:
                entry_dropdown = await page.query_selector("select")
                if entry_dropdown:
                    await entry_dropdown.select_option("100")
                    await asyncio.sleep(3)
                    print("✅ Berhasil mengubah entri ke 100.")
            except:
                print("⚠️ Gagal mengubah entri per halaman, menggunakan default.")

            semua_data = []
            page_num = 1
            
            while True:
                print(f"📄 Mengambil data halaman {page_num}...")
                try:
                    await page.wait_for_selector("table", timeout=10000)
                    rows = await page.query_selector_all("table tbody tr")
                    if not rows:
                        break
                        
                    for row in rows:
                        cols = await row.query_selector_all("td")
                        if len(cols) >= 3:
                            semua_data.append({
                                "package_name": await cols[1].inner_text(),
                                "satker": await cols[2].inner_//text(),
                                "budget": await cols[3].inner_text(),
                                "page": page_num
                            })
                    
                    # Cari tombol Next
                    next_button = await page.query_selector("a:has-text('Berikutnya'), button:has-text('Berikutnya'), a:has-text('>')")
                    if next_button:
                        await next_button.click()
                        page_num += 1
                        await asyncio.sleep(3)
                    else:
                        print("✅ Sudah mencapai halaman terakhir.")
                        break
                except Exception as e:
                    print(f"⚠️ Error di halaman {page_num}: {e}")
                    break
            
            with open("rup_bulukumba_debug.json", "w", encoding="utf-8") as f:
                json.dump(semua_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n🎉 Selesai! Total {len(semua_data)} data tersimpan di rup_bulukumba_debug.json")
            
        except Exception as e:
            print(f"💥 CRITICAL ERROR: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
