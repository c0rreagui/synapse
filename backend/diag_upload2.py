import asyncio
import os
import sys
sys.path.append('/app')

async def diag():
    from core.browser import launch_browser_for_profile
    profile = 'tiktok_profile_1773615375054'

    print('Launching browser...')
    p, browser, context, page = await launch_browser_for_profile(
        profile, headless=False
    )

    print('Navigating to TikTok Studio...')
    try:
        await page.goto('https://www.tiktok.com/tiktokstudio/upload', wait_until='domcontentloaded', timeout=30000)
    except Exception as e:
        print('Navigation error: ' + str(e))

    # Wait longer for content to load
    print('Waiting 30s for content to load...')
    await page.wait_for_timeout(30000)

    url = page.url
    title = await page.title()
    print('Current URL: ' + url)
    print('Page title: ' + title)

    # Take screenshot
    await page.screenshot(path='/app/data/diag_screenshot2.png', full_page=False)
    print('Screenshot saved')

    # Check for any file inputs
    file_inputs = await page.locator('input[type=file]').count()
    print('File inputs found: ' + str(file_inputs))

    # Check for various upload button texts
    buttons_to_check = [
        'Selecionar video',
        'Selecionar',
        'Select video',
        'Select file',
        'Upload',
        'Carregar',
        'Enviar',
    ]
    for btn_text in buttons_to_check:
        try:
            count = await page.locator('button:has-text("' + btn_text + '")').count()
            if count > 0:
                print('Button found: "' + btn_text + '" (' + str(count) + ')')
        except:
            pass

    # Check all visible buttons
    try:
        all_buttons = await page.locator('button').all_text_contents()
        for i, btn in enumerate(all_buttons[:10]):
            print('  button[' + str(i) + ']: ' + repr(btn))
    except:
        pass

    # Check for iframe
    iframes = await page.locator('iframe').count()
    print('Iframes found: ' + str(iframes))

    # Get page text snippet
    try:
        body_text = await page.locator('body').inner_text()
        lines = [l.strip() for l in body_text.split('\n') if l.strip()]
        for line in lines[:20]:
            print('  TEXT: ' + line)
    except Exception as e:
        print('Could not get body text: ' + str(e))

    # Check for CAPTCHA/verification elements in HTML
    try:
        html = await page.content()
        if 'captcha' in html.lower():
            print('CAPTCHA found in HTML!')
        if 'secsdk' in html.lower():
            print('SecSDK (anti-bot) found in HTML!')
    except:
        pass

    await context.close()
    await p.stop()
    print('Done.')

asyncio.run(diag())
