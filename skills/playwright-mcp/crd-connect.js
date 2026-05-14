const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: false, args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  
  console.log('Navigating to Chrome Remote Desktop...');
  await page.goto('https://remotedesktop.google.com/support', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(2000);
  
  // Take screenshot
  await page.screenshot({ path: '/tmp/crd-start.png', fullPage: false });
  console.log('Screenshot saved');
  
  // Look for the access code input field
  const pageText = await page.evaluate(() => document.body.innerText);
  console.log('Page text (first 500 chars):', pageText.substring(0, 500));
  
  await browser.close();
})();
