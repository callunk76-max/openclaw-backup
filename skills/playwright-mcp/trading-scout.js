const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page = await context.newPage();
  const results = {};

  // === 1. FOREX FACTORY — Latest trading systems/strategies ===
  try {
    await page.goto('https://www.forexfactory.com/forum/39-trading-systems', { timeout: 30000, waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    const systems = await page.evaluate(() => {
      const threads = document.querySelectorAll('.thread-title a');
      return Array.from(threads).slice(0, 15).map(t => t.textContent.trim() + ' | ' + t.href);
    });
    results.forexfactory_systems = systems;
  } catch (e) { results.forexfactory_systems = ['Error: ' + e.message]; }

  // === 2. MYFXBOOK — Top EAs ===
  try {
    await page.goto('https://www.myfxbook.com/forex-trading-systems', { timeout: 30000, waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    const eas = await page.evaluate(() => {
      const items = document.querySelectorAll('.system-item, .row');
      return Array.from(items).slice(0, 10).map(i => i.textContent.trim().substring(0, 150));
    });
    results.myfxbook_eas = eas;
  } catch (e) { results.myfxbook_eas = ['Error: ' + e.message]; }

  // === 3. MQL5 — Free EAs & Indicators ===
  try {
    await page.goto('https://www.mql5.com/en/market/product?sort=rating&tag=free', { timeout: 30000, waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    const mql5 = await page.evaluate(() => {
      const items = document.querySelectorAll('.product-card, .card');
      return Array.from(items).slice(0, 15).map(i => i.textContent.trim().substring(0, 200));
    });
    results.mql5_products = mql5;
  } catch (e) { results.mql5_products = ['Error: ' + e.message]; }

  // === 4. TRADINGVIEW — Popular indicators ===
  try {
    await page.goto('https://www.tradingview.com/scripts/', { timeout: 30000, waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);
    const tv = await page.evaluate(() => {
      const items = document.querySelectorAll('.tv-script-card, .script-card');
      return Array.from(items).slice(0, 15).map(i => i.textContent.trim().substring(0, 200));
    });
    results.tradingview_scripts = tv;
  } catch (e) { results.tradingview_scripts = ['Error: ' + e.message]; }

  // === 5. MQL5 FORUM — Free strategies discussion ===
  try {
    await page.goto('https://www.mql5.com/en/forum/476', { timeout: 30000, waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    const forum = await page.evaluate(() => {
      const items = document.querySelectorAll('.topic-title a, .post');
      return Array.from(items).slice(0, 10).map(i => i.textContent.trim().substring(0, 200));
    });
    results.mql5_forum = forum;
  } catch (e) { results.mql5_forum = ['Error: ' + e.message]; }

  // === 6. GITHUB — Open source trading bots ===
  try {
    await page.goto('https://github.com/topics/trading-bot?o=desc&s=stars', { timeout: 30000, waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    const github = await page.evaluate(() => {
      const repos = document.querySelectorAll('[data-testid="repo-list"] .Box-row, .repo-list-item');
      return Array.from(repos).slice(0, 10).map(r => r.textContent.trim().substring(0, 200));
    });
    results.github_trading_bots = github;
  } catch (e) { results.github_trading_bots = ['Error: ' + e.message]; }

  // === 7. FOREXSTRATEGIES — Free trading strategies ===
  try {
    await page.goto('https://www.forexstrategiesresources.com/', { timeout: 30000, waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    const fsi = await page.evaluate(() => {
      const items = document.querySelectorAll('.entry-title a, h2 a');
      return Array.from(items).slice(0, 10).map(i => i.textContent.trim() + ' | ' + i.href);
    });
    results.forex_strategies = fsi;
  } catch (e) { results.forex_strategies = ['Error: ' + e.message]; }

  // === 8. LITERATURE — Trading techniques ===
  try {
    await page.goto('https://www.babypips.com/learn/forex', { timeout: 30000, waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    const bp = await page.evaluate(() => {
      const items = document.querySelectorAll('a[href*="/learn/forex/"]');
      return Array.from(items).slice(0, 10).map(i => i.textContent.trim() + ' | ' + i.href);
    });
    results.babypips = bp;
  } catch (e) { results.babypips = ['Error: ' + e.message]; }

  fs.writeFileSync('/tmp/trading-scout-results.json', JSON.stringify(results, null, 2));
  console.log('DONE - results saved');
  await browser.close();
})();
