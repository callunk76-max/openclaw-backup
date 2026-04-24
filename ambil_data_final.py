import asyncio
from playwright.async_api import async_playwright
import json
import time
from tqdm import tqdm

async def run():
    print("🛠️ Menginisialisasi Playwright (Mode Background)...")
    async with async_playwright() as p:
        try:
            # HARUS headless=True agar bisa jalan di WSL tanpa X-Server
            browser = await p.chromium.launch(headless=True) 
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )
            page = await context.new_page()
            
            # Header manual untuk mengelabui bot detection
            await page.set_extra_http_headers({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*" + "/*;q=0.8",
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "max-age=0",
                "Upgrade-Insecure-Requests": "1"
            })
            
            url = "https://data.inaproc.id/rup?jenis_klpd=4&instansi=D411"
            print(f"🌐 Menghubungi server Inaproc...")
            
            # Gunakan 'commit' agar tidak hang menunggu network idle
            try:
                response = await page.goto(url, wait_until="commit", timeout=30000)
                print(f"✅ Koneksi berhasil. Status: {response.status}")
            except Exception as e:
                print(f"⚠️ Timeout awal, mencoba lanjut... ({e})")
            
            # Jeda untuk render JavaScript
            print("⏳ Menunggu render konten (10 detik)...")
            await asyncio.sleep(10)
            
            # Cek apakah ada tabel
            if not await page.query_selector("table"):
                print("❌ Tabel tidak ditemukan. Anda kemungkinan terblokir Cloudflare.")
                print("💡 SARAN: Jika ini terjadi, cara tercepat adalah export JSON manual dari browser laptop Anda dan kirim ke saya.")
                await browser.close()
                return
            
            print("📊 Tabel terdeteksi! Memulai ekstraksi data...")
            
            # Coba set entri ke 100
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
                try:
                    await page.wait_for_selector("table", timeout=5000)
                    rows = await page.query_selector_all("table tbody tr")
                    if not rows:
                        break
                        
                    for row in rows:
                        cols = await row.query_selector_all("td")
                        if len(cols) >= 3:
                            semua_data.append({
                                "package_name": await cols[1].inner_text(),
                                "satker": await cols[2].inner_text(),
                                "budget": await cols[3].inner_text(),
                                "page": page_num
                            })
                    
                    # Cari tombol 'Berikutnya' atau '>'
                    next_btn = await page.query_selector("a:has-text('Berikutnya'), button:has-text('Berikutnya'), a:has-text('>')")
                    if next_btn:
                        await next_btn.click()
                        page_num += 1
                        await asyncio.sleep(3)
                    else:
                        print("\n✅ Sudah mencapai halaman terakhir.")
                        break
                except Exception as e:
                    print(f"\n⚠️ Error di hal {page_num}: {e}")
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
