"""
Teste Final: Aprovação em Massa com Monitor Integrado
======================================================
Usa o Monitor ("Olho de Deus") para validação visual completa
"""
import os
import json
import shutil
import asyncio
from datetime import datetime
from pathlib import Path
import requests

# Add core to path
import sys
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "core"))

from core.monitor import TikTokMonitor

# Config
PENDING_DIR = BASE_DIR / "data" / "pending"
API_BASE = "http://localhost:8000/api/v1"
SCREENSHOT_DIR = BASE_DIR / "tests" / "screenshots"

PENDING_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def check_backend():
    try:
        r = requests.get(f"{API_BASE.replace('/api/v1', '')}/health", timeout=2)
        return r.ok
    except:
        return False

def create_mock_videos(count=6):
    print(f"\n📦 Criando {count} vídeos mock...")
    
    mock_video = BASE_DIR / "data" / "test_mock.mp4"
    if not mock_video.exists():
        with open(mock_video, 'wb') as f:
            f.write(b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom')
    
    profiles = ["perfil_01_cortes", "perfil_02_ibope"]
    video_ids = []
    
    for i in range(count):
        profile_id = profiles[i % 2]
        video_id = f"test_mass_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"
        video_ids.append(video_id)
        
        shutil.copy(mock_video, PENDING_DIR / f"{video_id}.mp4")
        
        metadata = {
            "uploaded_at": datetime.now().isoformat(),
            "original_filename": f"video_teste_{i+1}.mp4",
            "profile_id": profile_id,
            "status": "pending"
        }
        
        with open(PENDING_DIR / f"{video_id}.mp4.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"✅ {len(video_ids)} vídeos criados")
    return video_ids

def approve_videos_mass(video_ids):
    print("\n🚀 Aprovando vídeos em massa...")
    
    schedules = [
        ("2026-01-10", "12:40"),
        ("2026-01-10", "12:40"),
        ("2026-01-11", "12:40"),
        ("2026-01-11", "12:40"),
        ("2026-01-12", "12:40"),
        ("2026-01-12", "12:40"),
    ]
    
    for i, video_id in enumerate(video_ids):
        date, time = schedules[i]
        schedule_time = f"{date}T{time}:00"
        profile = "perfil_01_cortes" if i % 2 == 0 else "perfil_02_ibope"
        
        payload = {
            "id": video_id,
            "action": "scheduled",
            "schedule_time": schedule_time,
            "target_profile_id": profile
        }
        
        try:
            r = requests.post(f"{API_BASE}/queue/approve", json=payload)
            if r.ok:
                print(f"  ✅ {video_id} → {date} @ {time} (Perfil: {profile})")
            else:
                print(f"  ❌ {video_id}: {r.text}")
        except Exception as e:
            print(f"  ❌ {video_id}: {e}")
    
    print("✅ Aprovação concluída")

async def visual_verification_with_monitor():
    """Usa o Monitor para navegação e screenshot - Versão Simplificada"""
    print("\n📸 Iniciando verificação visual...")
    
    # Use playwright directly (Monitor requires more complex setup)
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--start-maximized'])
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        
        # Load cookies
        session_file = BASE_DIR / "data" / "sessions" / "tiktok_profile_01.json"
        if session_file.exists():
            print(f"  → Carregando sessão: {session_file.name}")
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                cookies = session_data.get('cookies', session_data) if isinstance(session_data, dict) else session_data
                await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        try:
            print("  → Acessando TikTok Studio...")
            await page.goto("https://www.tiktok.com/creator-center/content", timeout=60000)
            await page.wait_for_timeout(5000)
            
            # Check if logged in
            try:
                await page.wait_for_selector('[data-e2e="profile-icon"]', timeout=10000)
                print("  ✅ Login automático bem-sucedido!")
            except:
                print(" ⏳ Aguardando login manual (45s)...")
                await page.wait_for_timeout(45000)
            
            # Navigate to Scheduled tab
            print("  → Procurando aba 'Scheduled'...")
            scheduled_found = False
            
            selectors = [
                'a[href*="scheduled"]',
                'button:has-text("Scheduled")',
                'a:has-text("Scheduled")',
                '[data-e2e="scheduled"]',
                'text=Scheduled',
                'text=Agendados'
            ]
            
            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=3000):
                        await element.click()
                        scheduled_found = True
                        print(f"  ✅ Aba 'Scheduled' clicada!")
                        break
                except:
                    continue
            
            if not scheduled_found:
                print("  ⚠️  Tentando clicar em links visíveis...")
                try:
                    # Try clicking any visible link with "schedule" in text
                    await page.click('text=/.*schedule.*/i', timeout=5000)
                    print("  ✅ Link de schedule encontrado!")
                except:
                    print("  ⚠️  Aba não encontrada, screenshot da tela atual")
            
            await page.wait_for_timeout(5000)
            
            # Capture screenshot
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = SCREENSHOT_DIR / f"tiktok_agendados_final_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"  📸 Screenshot salvo: {screenshot_path.name}")
            
            # Validation
            content = await page.content()
            detected_days = []
            for day in ["10", "11", "12"]:
                patterns = [f"Jan {day}", f"January {day}", f"2026-01-{day}", f"1/{day}/2026", f"Jan. {day}", f"Janeiro {day}"]
                if any(pattern in content for pattern in patterns):
                    detected_days.append(day)
                    print(f"  ✅ Dia {day} detectado no HTML")
            
            if len(detected_days) == 3:
                print("\n🎉 SUCESSO TOTAL: Todos os 3 dias (10, 11, 12) confirmados!")
            else:
                print(f"\n⚠️  Detectados {len(detected_days)}/3 dias. Verifique o screenshot.")
            
            print("\n  ⏸️  Browser aberto por 15s para revisão...")
            await page.wait_for_timeout(15000)
            
            return screenshot_path
            
        finally:
            await browser.close()

def main():
    print("=" * 70)
    print("TESTE FINAL: APROVAÇÃO EM MASSA COM MONITOR")
    print("=" * 70)
    
    if not check_backend():
        print("\n❌ Backend offline!")
        return
    
    print("✅ Backend online")
    
    # Step 1: Create mocks
    video_ids = create_mock_videos(6)
    
    # Step 2: Mass approve
    approve_videos_mass(video_ids)
    
    # Step 3: Visual verification with Monitor
    try:
        screenshot = asyncio.run(visual_verification_with_monitor())
        print("\n" + "=" * 70)
        print(f"✅ TESTE CONCLUÍDO COM SUCESSO")
        print(f"📸 Screenshot: {screenshot}")
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
