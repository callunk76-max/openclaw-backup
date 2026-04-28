import asyncio
from playwright.async_api import async_playwright

USERNAME = "197607121997021001"
PASSWORD = "x1x2x3x4"
BASE_URL = "https://dikerja.com"

async def debug_form():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print("[*] Navigating to login...")
            await page.goto(BASE_URL)
            await page.fill('input[name="username"], input[type="text"]', USERNAME)
            await page.fill('input[name="password"], input[type="password"]', PASSWORD)
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_load_state("networkidle")

            print("[*] Navigating to Aktivitas...")
            await page.click('text="Aktivitas"')
            await page.wait_for_load_state("networkidle")

            print("[*] Opening 'Tambah Data' modal...")
            await page.click('text="Tambah Data"')
            await page.wait_for_selector('text="Simpan"', state="visible")
            
            # Capture HTML of the modal to analyze the date field
            print("[*] Extracting modal HTML...")
            html = await page.content()
            with open("modal_dump.html", "w", encoding="utf-8") as f:
                f.write(html)
            
            # Take a specific screenshot of the date field area
            print("[*] Taking debug screenshot...")
            await page.screenshot(path="date_field_debug.png")
            
            print("[+] Debug data captured successfully.")

        except Exception as e:
            print(f"[-] Debug error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_form())
