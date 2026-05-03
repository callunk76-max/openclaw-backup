import asyncio
from playwright.async_api import async_playwright
import json
import time
from tqdm import tqdm

async def run():
    print("🐢 Menginisialisasi Mode Siput (Sangat Lambat & Stabil)...")
    async with async_playwright() as p:
        try:
            # Headless=True untuk kestabilan di WSL
            browser = await p.chromium.launch(headless=True) 
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )
            page = await context.new_page()
            
            # Header untuk meniru browser asli
            await page.set_extra_http_headers({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "max-age=0",
                "Upgrade-Insecure-Requests": "1"
            })
            
            url = "https://data.inaproc.id/rup?jenis_klpd=4&instansi=D411"
            print(f"🌐 Menghubungi server Inaproc: {url}")
            
            # Menggunakan 'domcontentloaded' agar tidak hang menunggu networkidle
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                print(f"✅ Halaman utama terbuka.")
            except Exception as e:
                print(f"⚠️ Timeout awal: {e}. Mencoba lanjut...")
            
            # Jeda awal yang lama untuk membiarkan Cloudflare/JS selesai render
            print("⏳ Menunggu render awal (15 detik)...")
            await asyncio.sleep(15)
            
            # Cek apakah tabel muncul
            if not await page.query_selector("table"):
                print("❌ Tabel tidak ditemukan. Kemungkinan terblokir Cloudflare.")
                await browser.close()
                return
            
            print("📊 Tabel terdeteksi! Memulai penarikan data mode siput...")
            
            semua_data = []
            page_num = 1
            
            while True:
                print(f"📄 Mengambil data halaman {page_num}...", end="\r")
                try:
                    # Tunggu tabel benar-benar ada
                    await page.wait_for_selector("table", timeout=10000)
                    
                    # Ambil baris tabel
                    rows = await page.query_selector_all("table tbody tr")
                    if not rows:
                        print("\n✅ Tidak ada baris data lagi.")
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
                    
                    # Cari tombol 'Berikutnya' secara spesifik
                    next_button = await page.query_selector("a:has-text('Berikutnya'), button:has-text('Berikutnya')")
                    
                    if next_button:
                        # Klik tombol 'Berikutnya'
                        await next_button.click()
                        page_num += 1
                        # JEDA SANGAT LAMA untuk menghindari deteksi bot
                        print(f" l Berhasil ambil hal {page_num-1}. Menunggu 15 detik sebelum halaman berikutnya...")
                        await asyncio.sleep(15) 
                    else:
                        print("\n✅ Sudah mencapai halaman terakhir (Tombol 'Berikutnya' tidak ditemukan).")
                        break
                except Exception as e:
                    print(f"\n⚠️ Error di halaman {page_num}: {e}")
                    # Jika error, coba tunggu lebih lama lalu lanjut
                    await asyncio.sleep(20)
                    continue
            
            # Simpan hasil
            with open("rup_bulukumba_siput.json", "w", encoding="utf-8") as f:
                json.dump(semua_data, f, ensure_ascii=False, indent=2)
                
            print(f"\n🎉 SELESAI! Total {len(semua_data)} data tersimpan di rup_bulukumba_siput.json")
            
        except Exception as e:
            print(f"💥 CRITICAL ERROR: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
EOF
