import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================
USERNAME = "197607121997021001"
PASSWORD = "x1x2x3x4"
BASE_URL = "https://dikerja.com"

DESCRIPTIONS = [
    "Melakukan cek harian terhadap layanan Helpdesk LPSE Kab. Bulukumba",
    "Membantu tim verifikasi melakukan pelayanan pada penyedia atau user LPSE",
    "Melakukan layanan konsultasi pengadaan lainnya",
    "Melaksanakan pelayanan lainnya pada LPSE",
    "Melakukan cek harian terhadap kondisi server, layanan jaringan dan infrastruktur LPSE Kab.Bulukumba",
    "Memeriksa apakah ada instruksi-instruksi dari Adminstrator LKPP Pusat",
    "Memeriksa kembali data backup dari server LPSE"
]

def format_date_id(date_str):
    # Convert YYYY-MM-DD to DD/MM/YYYY
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%d/%m/%Y")

async def run_automation(target_date=None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print(f"[*] Navigating to {BASE_URL}...")
            await page.goto(BASE_URL)

            print("[*] Attempting login...")
            await page.fill('input[name="username"], input[type="text"]', USERNAME)
            await page.fill('input[name="password"], input[type="password"]', PASSWORD)
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_load_state("networkidle")

            print("[*] Navigating to 'Aktivitas' menu...")
            await page.click('text="Aktivitas"')
            await page.wait_for_load_state("networkidle")

            raw_date = target_date if target_date else datetime.now().strftime("%Y-%m-%d")
            fill_date = format_date_id(raw_date)
            print(f"[*] Target date for entries: {fill_date} (from {raw_date})")

            for idx, desc in enumerate(DESCRIPTIONS):
                print(f"[*] Processing entry {idx+1}/{len(DESCRIPTIONS)}: {desc[:30]}...")
                
                await page.click('text="Tambah Data"')
                await page.wait_for_selector('#side_form', state="visible")
                await asyncio.sleep(1)
                
                # 1. Tanggal - Use formatted date and force value via JS
                try:
                    await page.fill('#tanggal', fill_date)
                    await page.evaluate(f'document.getElementById("tanggal").value = "{fill_date}"')
                except:
                    pass
                
                # 2. Sasaran Kinerja
                await page.click('text="Pilih Sasaran Kerja"')
                await asyncio.sleep(0.5)
                try:
                    await page.locator('li, div').filter(has_text="Non Sasaran").first.click(force=True)
                except:
                    await page.click('text="Non Sasaran"', force=True)
                
                # 3. Nama Aktivitas
                await page.click('text="Pilih Aktivitas"')
                await asyncio.sleep(0.5)
                try:
                    await page.locator('li, div').filter(has_text=desc[:20]).first.click(force=True)
                except:
                    await page.locator('li, div[role="option"], .dropdown-item').first.click(force=True)
                
                # 4. Hasil, Satuan, Waktu
                try:
                    # Find input fields based on order/placeholder since IDs might be missing
                    inputs = await page.query_selector_all('input[type="text"], input[type="number"]')
                    if len(inputs) >= 3:
                        # Hasil
                        await inputs[0].fill("1")
                        # Satuan
                        await inputs[1].fill("Kegiatan")
                        # Waktu
                        await inputs[2].fill("60")
                    else:
                        # Fallback to generic selectors
                        await page.fill('input[placeholder="Hasil"]', "1")
                        await page.fill('input[placeholder="Satuan"]', "Kegiatan")
                        await page.fill('input[placeholder="Waktu"]', "60")
                except Exception as e:
                    print(f"[-] Field fill error: {e}")
                
                # 5. Keterangan
                await page.fill('textarea', desc)
                
                # Submit
                print("[*] Submitting form...")
                try:
                    await page.evaluate('() => { const btn = Array.from(document.querySelectorAll("button")).find(el => el.textContent.includes("Simpan")); if(btn) btn.click(); }')
                except:
                    await page.click('button:has-text("Simpan")', force=True)
                
                # Verification: Check if the drawer closes
                try:
                    await page.wait_for_selector('#side_form', state="hidden", timeout=10000)
                    print(f"[+] Entry {idx+1} submitted and modal closed.")
                except:
                    print(f"[-] Warning: Modal did not close for entry {idx+1}.")
                
                await asyncio.sleep(2)

            print(f"[***] ALL ENTRIES FOR {fill_date} COMPLETED! [***]")

        except Exception as e:
            print(f"[-] Error occurred: {e}")
            await page.screenshot(path="error_debug.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    import sys
    target = None
    if len(sys.argv) > 1:
        target = sys.argv[1]
    asyncio.run(run_automation(target))
