"""
👁️ TESTE COMPLETO COM OLHO DE DEUS ATIVO
==========================================
Executa upload monitorado com todos os vídeos, capturando:
- Screenshots em cada etapa
- DOM/HTML completo
- Traces do Playwright
- Logs de console
- Cookies/Storage
"""
import asyncio
import sys
import os
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.uploader_monitored import upload_video_monitored

# Diretórios
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_VIDEOS_DIR = os.path.join(BASE_DIR, "tests", "test_videos")
PENDING_DIR = os.path.join(BASE_DIR, "data", "pending")

async def run_full_test():
    print("👁️ TESTE COMPLETO COM OLHO DE DEUS")
    print("=" * 60)
    
    # Encontrar vídeos de teste
    video_files = [f for f in os.listdir(TEST_VIDEOS_DIR) if f.endswith('.mp4')][:3]  # Limitar a 3
    
    if not video_files:
        print("❌ Nenhum vídeo de teste encontrado!")
        return
    
    print(f"📹 {len(video_files)} vídeos encontrados")
    
    # Configurar agendamentos
    schedules = [
        {"date": "2026-01-11", "time": "10:00", "profile": "tiktok_profile_01"},
        {"date": "2026-01-12", "time": "14:00", "profile": "tiktok_profile_01"},
        {"date": "2026-01-13", "time": "18:00", "profile": "tiktok_profile_02"},
    ]
    
    results = []
    
    for i, video_file in enumerate(video_files):
        schedule = schedules[i % len(schedules)]
        video_path = os.path.join(TEST_VIDEOS_DIR, video_file)
        
        print(f"\n{'='*60}")
        print(f"🎬 TESTE {i+1}/{len(video_files)}: {video_file}")
        print(f"📅 Agendamento: {schedule['date']}T{schedule['time']}")
        print(f"👤 Perfil: {schedule['profile']}")
        print(f"📦 Tamanho: {os.path.getsize(video_path) / 1024 / 1024:.1f}MB")
        print("=" * 60)
        
        try:
            result = await upload_video_monitored(
                session_name=schedule['profile'],
                video_path=video_path,
                caption=f"🔍 Teste Olho de Deus #{i+1} #SynapseTest #Debug",
                schedule_time=f"{schedule['date']}T{schedule['time']}",
                post=True,  # Tentar de verdade
                enable_monitor=True  # OLHO DE DEUS ATIVO
            )
            
            results.append({
                "video": video_file,
                "profile": schedule['profile'],
                "schedule": f"{schedule['date']}T{schedule['time']}",
                "status": result.get("status", "unknown"),
                "message": result.get("message", "N/A"),
                "monitor_report": result.get("monitor_report", "N/A"),
                "trace_file": result.get("trace_file", "N/A")
            })
            
            print(f"\n📊 RESULTADO: {result.get('status', 'unknown')}")
            if result.get('message'):
                print(f"💬 Mensagem: {result['message']}")
            if result.get('monitor_report'):
                print(f"📁 Relatório: {result['monitor_report']}")
            if result.get('trace_file'):
                print(f"🔍 Trace: {result['trace_file']}")
                
        except Exception as e:
            print(f"❌ ERRO: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "video": video_file,
                "profile": schedule['profile'],
                "status": "error",
                "message": str(e)
            })
        
        # Pausa entre testes
        if i < len(video_files) - 1:
            print("\n⏳ Aguardando 5s para próximo teste...")
            await asyncio.sleep(5)
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO FINAL")
    print("=" * 60)
    
    success = sum(1 for r in results if r.get("status") == "ready")
    failed = len(results) - success
    
    print(f"✅ Sucesso: {success}")
    print(f"❌ Falhas: {failed}")
    print()
    
    for r in results:
        status_icon = "✅" if r.get("status") == "ready" else "❌"
        print(f"{status_icon} {r['video']}: {r.get('status', 'unknown')} - {r.get('message', 'N/A')[:50]}")
    
    # Listar relatórios gerados
    print("\n📁 RELATÓRIOS DO OLHO DE DEUS:")
    monitor_dir = os.path.join(BASE_DIR, "MONITOR", "runs")
    if os.path.exists(monitor_dir):
        runs = sorted(os.listdir(monitor_dir), reverse=True)[:3]
        for run in runs:
            print(f"  - {run}")
            readme = os.path.join(monitor_dir, run, "README.md")
            if os.path.exists(readme):
                print(f"    📖 {readme}")

if __name__ == "__main__":
    asyncio.run(run_full_test())
