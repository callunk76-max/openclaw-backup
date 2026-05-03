import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0")
        page = await context.new_page()
        print("Loading SIKaP...")
        response = await page.goto("https://sikap.inaproc.id/eproc4", wait_until="networkidle")
        print("Status:", response.status)
        title = await page.title()
        print("Title:", title)
        await browser.close()

asyncio.run(main())
