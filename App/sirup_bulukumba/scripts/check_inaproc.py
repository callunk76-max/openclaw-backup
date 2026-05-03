import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        try:
            print("Navigating to data.inaproc.id...")
            await page.goto("https://data.inaproc.id", wait_until="networkidle", timeout=60000)
            content = await page.content()
            with open("inaproc_content.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("Content saved to inaproc_content.html")
            print("Page Title:", await page.title())
        except Exception as e:
            print(f"Error: {e}")
        await browser.close()

asyncio.run(run())
