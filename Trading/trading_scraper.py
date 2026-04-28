import asyncio
from playwright.async_api import async_playwright
import time

# This URL is the shared chart link
CHART_URL = "https://www.tradingview.com/chart/sIXNurXP/?symbol=CRYPTO%3ABTCUSD"

async def scrape_tradingview_powers():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        # Use a realistic user agent to avoid detection
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print(f"Navigating to {CHART_URL}...")
            # Change to domcontentloaded to avoid timeout on heavy assets
            await page.goto(CHART_URL, wait_until="domcontentloaded", timeout=60000)
            
            # Give ample time for the indicator JS to execute and render the table
            print("Waiting for indicator to render...")
            await asyncio.sleep(15) 
            
            # Extract all text from the page to find the power values
            # TradingView indicators often render in a way that inner_text captures them
            content = await page.inner_text("body")
            
            target_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'NZD', 'CAD', 'CHF']
            powers = {}
            
            # Split content into words to find currency + value pairs
            words = content.split()
            for i in range(len(words) - 1):
                word = words[i].strip()
                if word in target_currencies:
                    val_text = words[i+1].strip()
                    try:
                        # Handle cases where value might have commas or symbols
                        clean_val = val_text.replace(',', '.').replace(' ', '')
                        val = float(clean_val)
                        powers[word] = val
                    except ValueError:
                        continue
            
            await browser.close()
            return powers
            
        except Exception as e:
            print(f"Scraper Error: {e}")
            await browser.close()
            return None
