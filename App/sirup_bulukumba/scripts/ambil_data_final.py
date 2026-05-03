import asyncio
from playwright.async_api import async_playwright
import json
import time
from tqdm import tqdm

async def run():
    print("🐢 Menginisialisasi Mode Siput (Sangat Lambat & Stabil)...")
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
            print(f"🌐 Menghubungi server Inaproc: {url}")
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                print(f"✅ Halaman utama terbuka.")
            except Exception as e:
                print(f"⚠️ Timeout awal: {e}. Mencoba lanjut...")
            
            print("⏳ Menunggu render awal (15 detik)...")
            await asyncio.sleep(15)
            
            if not await page.query_selector("table"):
                print("❌ Tabel tidak ditemukan. Kemungkinan terblokir Cloudflare.")
                await browser.close()
                return
            
            print("📊 Tabel terdeteksi! Memulai ekstraksi data presisi...")
            
            semua_data = []
            page_num = 1
            
            while True:
                print(f"📄 Mengambil data halaman {page_num}...", end="\r")
                
                success = False
                for attempt in range(3):
                    try:
                        await page.wait_for_selector("table", timeout=15000)
                        rows = await page.query_selector_all("table tbody tr")
                        if rows:
                            for row in rows:
                                cols = await row.query_selector_all("td")
                                # Mapping kolom sesuai permintaan User:
                                # Col 2: Satker, 4: Cara, 5: Metode, 6: Jenis, 7: Nama, 8: Kode RUP, 11: Nilai
                                if len(cols) >= 12:
                                    semua_data.append({
                                        "satker": await cols[2].inner_text(),
                                        "cara_pengadaan": await cols[4].inner_text(),
                                        "metode": await cols[5].inner_text(),
                                        "jenis": await cols[6].inner_text(),
                                        "package_name": await cols[7].inner_text(),
                                        "kode_rup": await cols[8].inner_text(),
                                        "budget": await cols[11].inner_text(),
                                        "page": page_num
                                    })
                            
                            # SIMPAN SETIAP HALAMAN
                            with open("rup_bulukumba_final.json", "w", encoding="utf-8") as f:
                                json.dump(semua_data, f, ensure_ascii=False, indent=2)
                            
                            success = True
                            break
                    except Exception as e:
                        print(f"\n⚠️ Percobaan {attempt+1}/3 gagal di hal {page_num}: {e}")
                        await asyncio.sleep(10 * (attempt + 1))
                        try:
                            await page.reload(wait_until="domcontentloaded")
                        except:
                            pass
                
                if not success:
                    print(f"\n❌ Gagal total di halaman {page_num}. Berhenti untuk mengamankan data.")
                    break
                
                next_button = await page.query_selector("a:has-text('Berikutnya'), button:has-text('Berikutnya'), a:has-text('>')")
                if next_button:
                    await next_button.click()
                    page_num += 1
                    await asyncio.sleep(15) 
                else:
                    print("\n✅ Sudah mencapai halaman terakhir.")
                    break
            
            with open("rup_//bulukumba_final.json", "w", encoding="utf-8") as f:
                json.dump(semua_data, f, ensure_ascii=False, indent=2)
                
            print(f"\n🎉 SELESAI! Total {len(semua_data)} data tersimpan di rup_bulukumba_final.json")
            
        except Exception as e:
            print(f"💥 CRITICAL ERROR: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
EOF
