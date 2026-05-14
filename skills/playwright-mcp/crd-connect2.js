const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  
  console.log('Navigating to Chrome Remote Desktop...');
  await page.goto('https://remotedesktop.google.com/support', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(3000);
  
  await page.screenshot({ path: '/tmp/crd-page.png' });
  console.log('Screenshot saved to /tmp/crd-page.png');
  
  // Get page text to understand layout
  const text = await page.evaluate(() => document.body.innerText);
  console.log('--- PAGE TEXT ---');
  console.log(text.substring(0, 1500));
  
  // Try to find the access code input
  const inputs = await page.$$('input');
  console.log(`Found ${inputs.length} input fields`);
  for (let i = 0; i < inputs.length; i++) {
    const type = await inputs[i].getAttribute('type');
    const placeholder = await inputs[i].getAttribute('placeholder');
    const id = await inputs[i].getAttribute('id');
    console.log(`Input ${i}: type=${type}, placeholder=${placeholder}, id=${id}`);
  }
  
  await browser.close();
})();
