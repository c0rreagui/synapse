const { chromium } = require('@playwright/test');

(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();

    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', exception => console.log('PAGE ERROR:', exception));

    console.log('Navigating to DashboardPreview Story...');
    try {
        await page.goto('http://localhost:6006/iframe.html?args=&id=app-visualization-dashboardpreview--final-state&viewMode=story', { waitUntil: 'domcontentloaded', timeout: 30000 });

        console.log('Waiting 2s for render...');
        await page.waitForTimeout(2000);

        console.log('Capturing screenshot of Loaded State...');
        await page.screenshot({ path: 'public/splash_loaded.png' });
    } catch (e) {
        console.error('Script Error:', e);
    }

    await browser.close();
    console.log('Done!');
})();
