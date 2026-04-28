import asyncio
from trading_scraper import scrape_tradingview_powers
async def main():
    powers = await scrape_tradingview_powers()
    print("Powers found:", powers)
asyncio.run(main())
