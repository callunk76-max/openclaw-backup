import asyncio
from playwright.async_api import async_playwright
import os

CHART_URL = "https://www.tradingview.com/chart/sIXNurXP/?symbol=CRYPTO%3ABTCUSD"
SCREENSHOT_PATH = "/root/.openclaw/workspace/Trading/tv_snapshot.jpg"

async def take_tradingview_screenshot():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print(f"Navigating to {CHART_URL}...")
            await page.goto(CHART_URL, wait_until="domcontentloaded", timeout=60000)
            
            print("Waiting for indicators to render...")
            await asyncio.sleep(20) 
            
            # Take a full page screenshot
            await page.screenshot(path=SCREENSHOT_PATH, full_page=True)
            print(f"Screenshot saved to {SCREENSHOT_PATH}")
            return True
        except Exception as e:
            print(f"Screenshot Error: {e}")
            return False
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(take_tradingview_screenshot())
