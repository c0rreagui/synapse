"""
Human-like interaction helpers for Playwright.
Provides Bézier mouse movements, Gaussian typing, and natural click patterns
to avoid bot detection by TikTok and similar platforms.
"""
import random
import math
from playwright.async_api import Page


async def human_move(page: Page, x: float, y: float, duration_ms: int = None):
    """
    Move mouse along a cubic Bézier curve with slight jitter,
    mimicking natural human arm movement.
    """
    if duration_ms is None:
        duration_ms = random.randint(200, 600)

    # Current position (fallback to a reasonable default)
    try:
        start = await page.evaluate("() => ({x: window._mouseX || 400, y: window._mouseY || 300})")
        sx, sy = start.get("x", 400), start.get("y", 300)
    except Exception:
        sx, sy = random.randint(300, 500), random.randint(200, 400)

    # Generate 2 control points for cubic Bézier
    dx, dy = x - sx, y - sy
    cp1x = sx + dx * random.uniform(0.2, 0.5) + random.uniform(-40, 40)
    cp1y = sy + dy * random.uniform(0.0, 0.3) + random.uniform(-30, 30)
    cp2x = sx + dx * random.uniform(0.5, 0.8) + random.uniform(-40, 40)
    cp2y = sy + dy * random.uniform(0.7, 1.0) + random.uniform(-30, 30)

    # Number of steps scales with distance
    dist = math.sqrt(dx * dx + dy * dy)
    steps = max(10, min(60, int(dist / 15)))

    delay_per_step = max(1, duration_ms / steps)

    for i in range(1, steps + 1):
        t = i / steps
        # Ease-in-out (slow start and end, fast middle)
        t_ease = t * t * (3 - 2 * t)

        # Cubic Bézier
        u = 1 - t_ease
        bx = u**3 * sx + 3 * u**2 * t_ease * cp1x + 3 * u * t_ease**2 * cp2x + t_ease**3 * x
        by = u**3 * sy + 3 * u**2 * t_ease * cp1y + 3 * u * t_ease**2 * cp2y + t_ease**3 * y

        # Add micro-jitter (human hand tremor)
        jitter = max(0.5, 3 * (1 - t))  # More jitter at start, less at end
        bx += random.gauss(0, jitter)
        by += random.gauss(0, jitter)

        await page.mouse.move(bx, by)
        await page.wait_for_timeout(delay_per_step)

    # Track position for next call
    await page.evaluate(f"() => {{ window._mouseX = {x}; window._mouseY = {y}; }}")


async def human_click(page: Page, locator, timeout: int = 5000):
    """
    Click an element with human-like behavior:
    1. Scroll into view
    2. Move mouse to element with Bézier curve
    3. Brief hover pause
    4. Click with slight offset from center
    """
    try:
        await locator.scroll_into_view_if_needed(timeout=timeout)
    except Exception:
        pass

    await locator.wait_for(state="visible", timeout=timeout)

    # Get element bounding box
    box = await locator.bounding_box()
    if not box:
        # Fallback to basic click
        await locator.click(timeout=timeout)
        return

    # Click at slight offset from center (humans don't click dead center)
    cx = box["x"] + box["width"] * random.uniform(0.35, 0.65)
    cy = box["y"] + box["height"] * random.uniform(0.35, 0.65)

    # Move to element with Bézier curve
    await human_move(page, cx, cy)

    # Brief hover pause (humans pause before clicking)
    await page.wait_for_timeout(random.randint(50, 200))

    # Click with natural delay between mousedown and mouseup
    await page.mouse.click(cx, cy, delay=random.randint(40, 120))


async def human_type(page: Page, text: str):
    """
    Type text with human-like timing:
    - Gaussian inter-key delay (not uniform)
    - Faster for common digraphs
    - Longer pauses at word boundaries
    - Occasional micro-pauses (thinking)
    """
    fast_digraphs = {"th", "he", "in", "er", "an", "re", "on", "at", "en", "nd",
                     "ti", "es", "or", "te", "of", "ed", "is", "it", "al", "ar"}

    # Keys that keyboard.press() understands (named keys only)
    _press_keys = {' ': 'Space', '\n': 'Enter', '\t': 'Tab'}

    for i, char in enumerate(text):
        # Base delay: Gaussian centered at 90ms, std 40ms
        delay = max(20, random.gauss(90, 40))

        # Fast digraphs
        if i > 0 and text[i-1:i+1].lower() in fast_digraphs:
            delay *= 0.6

        # Slower at word boundaries
        if char == ' ':
            delay = max(80, random.gauss(150, 50))
        elif char == '\n':
            delay = max(150, random.gauss(300, 80))

        # Occasional thinking pause (3% chance)
        if random.random() < 0.03:
            await page.wait_for_timeout(random.randint(400, 900))

        # Wait the human delay before typing
        await page.wait_for_timeout(int(delay))

        if char in _press_keys:
            await page.keyboard.press(_press_keys[char])
        else:
            # type() handles Unicode characters (accents, emojis, etc.)
            await page.keyboard.type(char)


async def human_scroll(page: Page, direction: str = "down", amount: int = None):
    """
    Scroll with human-like behavior: variable speed, slight pauses.
    """
    if amount is None:
        amount = random.randint(200, 500)

    delta = amount if direction == "down" else -amount

    # Break scroll into chunks (humans scroll in bursts)
    chunks = random.randint(3, 6)
    for i in range(chunks):
        chunk_delta = delta / chunks + random.gauss(0, 20)
        await page.mouse.wheel(0, chunk_delta)
        await page.wait_for_timeout(random.randint(30, 100))
