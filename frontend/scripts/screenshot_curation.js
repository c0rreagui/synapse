const { chromium } = require('playwright');

(async () => {
    console.log('Starting Playwright...');
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
    const page = await context.newPage();

    await page.goto('http://localhost:3000/clipper');

    console.log('Waiting for network idle...');
    await page.waitForLoadState('networkidle');

    console.log('Clicking Curation tab...');
    await page.click('button:has-text("Curation")');

    console.log('Waiting for 5 seconds to let UI load/hydrate/API fetch...');
    await page.waitForTimeout(5000);

    // Add some visual indicators to make sure the scroll happens if there are videos
    await page.evaluate(() => window.scrollTo(0, 300));
    await page.waitForTimeout(1000);

    const screenshotPath = 'C:\\\\Users\\\\guico\\\\.gemini\\\\antigravity\\\\brain\\\\0f67fbfc-b5ca-40fa-88a1-dba4c469fd3c\\\\curation_fixed_ui_2.png';
    await page.screenshot({ path: screenshotPath, fullPage: false });
    console.log('Screenshot saved to ' + screenshotPath);

    await browser.close();
})();
