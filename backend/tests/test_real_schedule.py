"""
Teste REAL: Agendar vídeos no TikTok Studio
============================================
Este script faz o UPLOAD REAL de vídeos para o TikTok Studio
e captura screenshots comprovando os agendamentos.

Requisitos:
- Vídeo real válido
- Sessões TikTok ativas (perfil_01 e perfil_02)
- Dias de agendamento: 10, 11, 12 de Janeiro @ 12:40
"""
import asyncio
import json
import shutil
from datetime import datetime
from pathlib import Path
import sys

# Setup paths
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

from core.uploader_monitored import upload_video_monitored
from playwright.async_api import async_playwright

APPROVED_DIR = BASE_DIR / "data" / "approved"
SCREENSHOT_DIR = BASE_DIR / "tests" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Source video - use a real video file
SOURCE_VIDEO = APPROVED_DIR / "p2_monitor_test.mp4"  # 37MB valid video


async def schedule_video_to_profile(profile: str, video_path: Path, schedule_date: str, schedule_time: str):
    """
    Agenda um vídeo para um perfil específico no TikTok Studio
    """
    schedule_datetime = f"{schedule_date}T{schedule_time}:00"
    session_name = f"tiktok_{profile}"
    
    print(f"\n📤 Agendando para {profile}")
    print(f"   Vídeo: {video_path.name}")
    print(f"   Data: {schedule_date} @ {schedule_time}")
    
    try:
        result = await upload_video_monitored(
            session_name=session_name,
            video_path=str(video_path),
            caption=f"Teste Agendamento - {schedule_date} {schedule_time}",
            hashtags=["teste", "synapse"],
            schedule_time=schedule_datetime,
            post=False,  # Don't actually post, just schedule
            enable_monitor=True
        )
        
        if result.get("success"):
            print(f"   ✅ Agendado com sucesso!")
            return True
        else:
            print(f"   ❌ Falha: {result.get('error', 'Unknown')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False


async def capture_scheduled_screenshot(profile: str, screenshot_name: str):
    """
    Captura screenshot da aba Scheduled do TikTok Studio
    """
    session_file = BASE_DIR / "data" / "sessions" / f"tiktok_{profile}.json"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        
        # Load cookies
        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                cookies = session_data.get('cookies', session_data)
                await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        try:
            await page.goto("https://www.tiktok.com/creator-center/content", timeout=60000)
            await page.wait_for_timeout(10000)
            
            # Try to navigate to Scheduled tab
            selectors = [
                'text=Scheduled',
                'text=Agendados',
                'a[href*="scheduled"]',
                '[data-e2e="scheduled"]'
            ]
            
            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=3000):
                        await element.click()
                        print(f"   ✅ Aba 'Scheduled' encontrada para {profile}")
                        break
                except:
                    continue
            
            await page.wait_for_timeout(5000)
            
            # Capture screenshot
            screenshot_path = SCREENSHOT_DIR / f"{screenshot_name}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"   📸 Screenshot: {screenshot_path.name}")
            
            return screenshot_path
            
        finally:
            await page.wait_for_timeout(5000)
            await browser.close()


async def main():
    print("=" * 70)
    print("TESTE REAL: AGENDAMENTO NO TIKTOK STUDIO")
    print("=" * 70)
    print(f"Data atual: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Check if video exists
    if not SOURCE_VIDEO.exists():
        print(f"\n❌ Vídeo não encontrado: {SOURCE_VIDEO}")
        print("   Procurando vídeos alternativos...")
        
        # Find any valid video
        found_video = None
        for f in APPROVED_DIR.glob("*.mp4"):
            if f.stat().st_size > 1000000:  # > 1MB
                found_video = f
                print(f"   ✅ Encontrado: {f.name} ({f.stat().st_size / 1024 / 1024:.1f}MB)")
                break
        
        if found_video is None:
            print("   ❌ Nenhum vídeo válido encontrado!")
            return
        
        video_to_use = found_video
    else:
        video_to_use = SOURCE_VIDEO
    
    print(f"\n📹 Usando vídeo: {video_to_use.name} ({video_to_use.stat().st_size / 1024 / 1024:.1f}MB)")
    
    # Schedule configuration
    schedules = [
        {"profile": "profile_01", "date": "2026-01-10", "time": "12:40"},
        {"profile": "profile_02", "date": "2026-01-10", "time": "12:40"},
        {"profile": "profile_01", "date": "2026-01-11", "time": "12:40"},
        {"profile": "profile_02", "date": "2026-01-11", "time": "12:40"},
        {"profile": "profile_01", "date": "2026-01-12", "time": "12:40"},
        {"profile": "profile_02", "date": "2026-01-12", "time": "12:40"},
    ]
    
    print("\n🎯 Agendamentos planejados:")
    for s in schedules:
        print(f"   • {s['profile']}: {s['date']} @ {s['time']}")
    
    # Execute schedules
    results = []
    for i, schedule in enumerate(schedules):
        print(f"\n{'='*50}")
        print(f"[{i+1}/{len(schedules)}] Processando...")
        
        # Create a copy of the video with unique name
        video_copy = APPROVED_DIR / f"test_schedule_{schedule['profile']}_{schedule['date'].replace('-', '')}_{i}.mp4"
        if not video_copy.exists():
            shutil.copy(video_to_use, video_copy)
        
        success = await schedule_video_to_profile(
            profile=schedule['profile'],
            video_path=video_copy,
            schedule_date=schedule['date'],
            schedule_time=schedule['time']
        )
        
        results.append({**schedule, "success": success})
    
    # Capture verification screenshots
    print("\n" + "=" * 50)
    print("📸 Capturando screenshots de verificação...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    screenshot_01 = await capture_scheduled_screenshot("profile_01", f"scheduled_profile_01_{timestamp}")
    screenshot_02 = await capture_scheduled_screenshot("profile_02", f"scheduled_profile_02_{timestamp}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 RESULTADO FINAL")
    print("=" * 70)
    
    success_count = sum(1 for r in results if r['success'])
    print(f"\n✅ Sucesso: {success_count}/{len(results)}")
    print(f"❌ Falha: {len(results) - success_count}/{len(results)}")
    
    print(f"\n📸 Screenshots capturados:")
    print(f"   • Perfil 01: {screenshot_01}")
    print(f"   • Perfil 02: {screenshot_02}")
    
    if success_count == len(results):
        print("\n🎉 TODOS OS AGENDAMENTOS CONCLUÍDOS COM SUCESSO!")
    else:
        print("\n⚠️  Alguns agendamentos falharam. Verifique os logs.")


if __name__ == "__main__":
    asyncio.run(main())
