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

    # Wait for page to load + CAPTCHA to appear
    print('Waiting 25s...')
    await page.wait_for_timeout(25000)

    # Test exact selectors from uploader_monitored.py
    captcha_selectors = [
        'text="Selecione 2 objetos"',
        'text="Select 2 objects"',
        'text="Which of these objects"',
        'text="Selecione 2 objetos que tem o mesmo formato"',
        '[class*="captcha"]',
        '[id*="captcha"]',
    ]

    print('\n=== Testing CAPTCHA selectors (exact from code) ===')
    for sel in captcha_selectors:
        try:
            count = await page.locator(sel).count()
            print('  ' + sel + ' => ' + str(count) + ' matches')
        except Exception as e:
            print('  ' + sel + ' => ERROR: ' + str(e))

    # Test additional selectors
    print('\n=== Testing broader selectors ===')
    broader = [
        'text=Selecione 2 objetos',
        'text=Select 2 objects',
        'text=captcha',
        'text=Confirmar',
        '.captcha-verify-container',
        '#captcha-verify-container',
        '[data-testid*="captcha"]',
        '.verify-captcha-container',
        'div.captcha_verify_container',
        'div[class*="verify"]',
        'div[class*="Verify"]',
        'text=mesmo formato',
    ]
    for sel in broader:
        try:
            count = await page.locator(sel).count()
            if count > 0:
                print('  MATCH: ' + sel + ' => ' + str(count))
            else:
                print('  miss:  ' + sel)
        except Exception as e:
            print('  ERROR: ' + sel + ' => ' + str(e))

    # Check outer HTML for captcha-related classes
    print('\n=== HTML analysis ===')
    try:
        html = await page.content()
        import re
        # Find all class names containing captcha or verify
        classes = re.findall(r'class="([^"]*(?:captcha|verify|Captcha|Verify)[^"]*)"', html)
        for c in classes[:10]:
            print('  class: ' + c)
        ids = re.findall(r'id="([^"]*(?:captcha|verify|Captcha|Verify)[^"]*)"', html)
        for i in ids[:10]:
            print('  id: ' + i)
    except:
        pass

    await context.close()
    await p.stop()
    print('\nDone.')

asyncio.run(diag())
