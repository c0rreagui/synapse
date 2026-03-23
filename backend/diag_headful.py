import asyncio
import os
import sys
sys.path.append('/app')

async def diag():
    from core.browser import launch_browser_for_profile
    profile = 'tiktok_profile_1773615375054'

    print('Launching browser (headless=False)...')
    p, browser, context, page = await launch_browser_for_profile(
        profile, headless=False
    )

    disp = os.environ.get('DISPLAY', 'not set')
    print('DISPLAY=' + disp)

    print('Navigating to TikTok Studio...')
    try:
        await page.goto('https://www.tiktok.com/tiktokstudio/upload', wait_until='domcontentloaded', timeout=30000)
    except Exception as e:
        print('Navigation error: ' + str(e))

    print('Waiting 20s for page to fully load...')
    await page.wait_for_timeout(20000)

    url = page.url
    title = await page.title()
    print('URL: ' + url)
    print('Title: ' + title)

    await page.screenshot(path='/app/data/diag_headful.png', full_page=False)
    print('Screenshot saved')

    # Check for CAPTCHA
    captcha_class = await page.locator('[class*="captcha"]').count()
    captcha_id = await page.locator('[id*="captcha"]').count()
    print('captcha class matches: ' + str(captcha_class))
    print('captcha id matches: ' + str(captcha_id))

    # Check for upload elements
    file_inputs = await page.locator('input[type=file]').count()
    print('file inputs: ' + str(file_inputs))

    # Check buttons
    try:
        all_buttons = await page.locator('button').all_text_contents()
        for i, btn in enumerate(all_buttons[:15]):
            if btn.strip():
                print('  button: ' + repr(btn.strip()))
    except:
        pass

    # Get page text
    try:
        body_text = await page.locator('body').inner_text()
        lines = [l.strip() for l in body_text.split('\n') if l.strip()]
        for line in lines[:25]:
            print('  TEXT: ' + line)
    except:
        pass

    await context.close()
    await p.stop()
    print('Done.')

asyncio.run(diag())
