import asyncio
import os
import sys
import json
import logging
from playwright.async_api import async_playwright
from datetime import datetime

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.session_manager import get_session_path

async def debug_dom():
    session_name = "tiktok_profile_02"
    session_path = get_session_path(session_name)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=session_path)
        page = await context.new_page()
        
        print("🚀 Navegando para Upload...")
        await page.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=120000)
        await page.wait_for_timeout(5000)
        
        # Ativa agendamento
        print("🕒 Procurando switch...")
        selectors = [
            'div:has-text("Programar vídeo")',
            'label:has-text("Programar vídeo")',
            'span:has-text("Programar vídeo")',
            '[class*="schedule"]'
        ]
        
        found = False
        for sel in selectors:
            try:
                el = page.locator(sel).last
                if await el.is_visible():
                    print(f"✅ Switch encontrado com: {sel}")
                    await el.click(force=True)
                    found = True
                    break
            except:
                continue
        
        if not found:
            print("⚠️ Switch não encontrado pelos seletores padrão. Tentando clique forçado via texto...")
            await page.get_by_text("Programar vídeo").last.click(force=True)
            found = True

        await page.wait_for_timeout(2000)
        
        # Encontra o badge de tempo
        print("🔍 Procurando Badge...")
        badge = page.locator('[class*="tux-badge"], [class*="time-picker-input"], [class*="schedule-time-picker"]').first
        if await badge.is_visible():
            box = await badge.bounding_box()
            print(f"✅ Badge encontrado em: {box}")
            
            # Clica para abrir picker
            await badge.click()
            await page.wait_for_timeout(2000)
            
            # Captura o DOM ao redor do picker
            print("📸 Capturando estado do Picker...")
            elements = await page.evaluate("""() => {
                const results = [];
                const all = document.querySelectorAll('*');
                all.forEach(el => {
                    const box = el.getBoundingClientRect();
                    // Filtra elementos que apareceram após o click na área do picker (centro/baixo)
                    if (box.top > 400 && box.width > 20 && box.height > 10) {
                        results.append({
                            tag: el.tagName,
                            text: el.innerText.substring(0, 50),
                            classes: el.className,
                            box: {x: box.x, y: box.y, w: box.width, h: box.height},
                            role: el.getAttribute('role'),
                            id: el.id
                        });
                    }
                });
                return results;
            }""")
            
            with open("picker_debug.json", "w", encoding="utf-8") as f:
                json.dump(elements, f, indent=2)
            
            await page.screenshot(path="picker_debug.png")
            print(f"📊 {len(elements)} elementos capturados em picker_debug.json")
        else:
            print("❌ Badge não encontrado")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_dom())
