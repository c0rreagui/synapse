"""
Teste Visual End-to-End: Aprovação em Massa
Validação: Screenshot do TikTok Studio mostrando agendamentos
"""
import os
import json
import shutil
import asyncio
from datetime import datetime
from pathlib import Path
import requests
from playwright.async_api import async_playwright

# Configuração
BASE_DIR = Path(__file__).parent.parent
PENDING_DIR = BASE_DIR / "data" / "pending"
APPROVED_DIR = BASE_DIR / "data" / "approved"
API_BASE = "http://localhost:8000/api/v1"
SCREENSHOT_DIR = BASE_DIR / "tests" / "screenshots"

PENDING_DIR.mkdir(parents=True, exist_ok=True)
APPROVED_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def check_backend():
    """Verifica se backend está online"""
    try:
        r = requests.get(f"{API_BASE.replace('/api/v1', '')}/health", timeout=2)
        return r.ok
    except:
        return False

def create_mock_videos(count=6):
    """Cria vídeos mock em pending/"""
    print(f"\n📦 Criando {count} vídeos mock...")
    
    # Create minimal MP4
    mock_video = BASE_DIR / "data" / "test_mock.mp4"
    if not mock_video.exists():
        with open(mock_video, 'wb') as f:
            # Minimal MP4 header
            f.write(b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom')
    
    profiles = ["perfil_01_cortes", "perfil_02_ibope"]
    video_ids = []
    
    for i in range(count):
        profile_id = profiles[i % 2]
        video_id = f"test_mass_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"
        video_ids.append(video_id)
        
        # Copy video
        video_path = PENDING_DIR / f"{video_id}.mp4"
        shutil.copy(mock_video, video_path)
        
        # Metadata
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
    """Aprova vídeos via API"""
    print("\n🚀 Aprovando vídeos em massa...")
    
    # Distribuição: 2 vídeos por dia (10, 11, 12)
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

async def visual_verification_tiktok():
    """Navega ao TikTok Studio e tira screenshot"""
    print("\n📸 Iniciando verificação visual (TikTok Studio)...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        # Load cookies from session file
        session_file = BASE_DIR / "data" / "sessions" / "tiktok_profile_01.json"
        if session_file.exists():
            print(f"  → Carregando sessão: {session_file.name}")
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                # Handle both formats: direct array or {"cookies": [...]}
                cookies = session_data.get('cookies', session_data) if isinstance(session_data, dict) else session_data
                await context.add_cookies(cookies)
        else:
            print("  ⚠️  Nenhuma sessão encontrada, login manual necessário")
        
        page = await context.new_page()
        
        try:
            print("  → Acessando TikTok Studio...")
            await page.goto("https://www.tiktok.com/creator-center/content", timeout=60000)
            
            # Wait a bit for cookies to take effect
            await page.wait_for_timeout(5000)
            
            # Check if logged in
            try:
                # If we see a profile element, we're logged in
                await page.wait_for_selector('[data-e2e="profile-icon"]', timeout=10000)
                print("  ✅ Login automático bem-sucedido!")
            except:
                print("  ⏳ Aguardando login manual (60s)...")
                await page.wait_for_timeout(60000)
            
            # Navigate to Scheduled tab
            print("  → Buscando aba 'Scheduled'...")
            try:
                # Try multiple selectors for the Scheduled tab
                scheduled_selectors = [
                    'text="Scheduled"',
                    'text="Agendados"',
                    '[data-e2e="scheduled-tab"]',
                    'button:has-text("Scheduled")',
                    'a:has-text("Scheduled")'
                ]
                
                for selector in scheduled_selectors:
                    try:
                        await page.click(selector, timeout=5000)
                        print(f"  ✅ Aba 'Scheduled' encontrada!")
                        break
                    except:
                        continue
                
                await page.wait_for_timeout(5000)
            except:
                print("  ⚠️  Aba 'Scheduled' não encontrada, tirando print da tela atual")
            
            # Screenshot
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = SCREENSHOT_DIR / f"tiktok_studio_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"  📸 Screenshot salvo: {screenshot_path.name}")
            
            # Validation
            content = await page.content()
            detected_days = []
            for day in ["10", "11", "12"]:
                if f"Jan {day}" in content or f"January {day}" in content or f"2026-01-{day}" in content or f"1/{day}/2026" in content:
                    detected_days.append(day)
                    print(f"  ✅ Dia {day} detectado")
            
            if len(detected_days) == 3:
                print("\n🎉 TESTE PASSOU: Todos os 3 dias confirmados!")
            else:
                print(f"\n⚠️  Apenas {len(detected_days)}/3 dias detectados. Verifique o screenshot manualmente.")
            
            return screenshot_path
            
        finally:
            print("\n  ⏸️  Browser ficará aberto por 10s para você revisar...")
            await page.wait_for_timeout(10000)
            await browser.close()

def main():
    print("=" * 70)
    print("TESTE VISUAL: APROVAÇÃO EM MASSA - DIAS 10, 11, 12 @ 12:40")
    print("=" * 70)
    
    # Check backend
    if not check_backend():
        print("\n❌ ERRO: Backend offline! Execute:")
        print("   cd backend && python -m uvicorn app.main:app --reload")
        return
    
    print("✅ Backend online")
    
    # Step 1: Create mocks
    video_ids = create_mock_videos(6)
    
    # Step 2: Approve via API
    approve_videos_mass(video_ids)
    
    # Step 3: Visual verification
    try:
        screenshot = asyncio.run(visual_verification_tiktok())
        print("\n" + "=" * 70)
        print(f"✅ TESTE CONCLUÍDO")
        print(f"📸 Screenshot: {screenshot}")
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ Erro na verificação visual: {e}")

if __name__ == "__main__":
    main()
