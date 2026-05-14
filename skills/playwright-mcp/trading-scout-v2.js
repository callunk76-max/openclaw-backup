const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const context = await browser.newContext({ 
    viewport: { width: 1920, height: 1080 },
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36'
  });
  const page = await context.newPage();
  const results = {};

  // Helper function
  async function scrapePage(url, selector, maxItems, waitFor, label) {
    try {
      await page.goto(url, { timeout: 60000, waitUntil: 'domcontentloaded' });
      if (waitFor) await page.waitForSelector(waitFor, { timeout: 10000 });
      await page.waitForTimeout(3000);
      const data = await page.evaluate((sel, max) => {
        const items = document.querySelectorAll(sel);
        return Array.from(items).slice(0, max).map(i => i.textContent.trim().substring(0, 250));
      }, selector, maxItems);
      results[label] = data.length > 0 ? data : ['(empty - page may have different structure)'];
    } catch (e) {
      results[label] = ['Error: ' + e.message.substring(0, 100)];
    }
  }

  // === 1. MQL5 Market — Free EAs ===
  await scrapePage(
    'https://www.mql5.com/en/market/product?sort=rating&tag=free',
    '.product-card__title, .product-card__description, .ai-card__title, [class*="title"]',
    20,
    '.product-card, .card, [class*="product"]',
    'mql5_free_products'
  );

  // === 2. MQL5 Code Base — Free indicators ===
  await scrapePage(
    'https://www.mql5.com/en/code',
    '.code-item__title a, .code-item, .code-card, [class*="code"]',
    20,
    null,
    'mql5_code_base'
  );

  // === 3. GitHub — TradingView indicators ===
  await scrapePage(
    'https://github.com/topics/pine-script-indicator?o=desc&s=stars',
    'h3 a, .repo-list-item, [data-testid="repo-list"] a',
    15,
    null,
    'github_pine_indicators'
  );

  // === 4. GitHub — MT4 EAs ===
  await scrapePage(
    'https://github.com/topics/mt4-expert-advisor?o=desc&s=stars',
    'h3 a, .repo-list-item',
    15,
    null,
    'github_mt4_eas'
  );

  // === 5. GitHub — Trading bots ===
  await scrapePage(
    'https://github.com/topics/algorithmic-trading?o=desc&s=stars',
    'h3 a, .repo-list-item',
    15,
    null,
    'github_algo_trading'
  );

  // === 6. GitHub — DeFi trading bots ===
  await scrapePage(
    'https://github.com/topics/defi-trading-bot?o=desc&s=stars',
    'h3 a, .repo-list-item',
    15,
    null,
    'github_defi_bots'
  );

  // === 7. Meteora DLMM — Latest pools (for arbitrage) ===
  await scrapePage(
    'https://app.meteora.ag/dlmm/pools',
    '[class*="pool"], [class*="row"], td, [class*="token"]',
    20,
    null,
    'meteora_pools'
  );

  // === 8. CoinGecko — Trending ===
  await scrapePage(
    'https://www.coingecko.com/en/coins/trending',
    'table tr, [class*="coin"], [class*="trend"]',
    20,
    null,
    'coingecko_trending'
  );

  // === 9. DeFiLlama — Yields ===
  await scrapePage(
    'https://defillama.com/yields',
    'table tr, [class*="row"], [class*="pool"]',
    25,
    null,
    'defillama_yields'
  );

  // === 10. DexScreener — Trending pairs ===
  await scrapePage(
    'https://dexscreener.com/trending',
    '[class*="pair"], tr, [class*="token"]',
    20,
    null,
    'dexscreener_trending'
  );

  fs.writeFileSync('/root/.openclaw/workspace/skills/playwright-mcp/trading-scout-v2.json', JSON.stringify(results, null, 2));
  console.log('DONE - V2 results saved');
  console.log(JSON.stringify(results, null, 2));
  await browser.close();
})().catch(e => { console.error('Fatal:', e.message); process.exit(1); });
