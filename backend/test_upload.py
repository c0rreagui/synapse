import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.uploader_monitored import upload_video_monitored
from core.session_manager import get_session

async def test_upload():
    profile_id = "tiktok_profile_1770135259969"
    video_file = "ptiktok_profile_1770135259969_548f6e9c.mp4"
    video_path = f"D:\\APPS - ANTIGRAVITY\\Synapse\\backend\\data\\approved\\{video_file}"
    
    print(f"\n{'='*60}")
    print(f"TESTE DE UPLOAD - @vibe.corteseclips")
    print(f"{'='*60}")
    print(f"Video: {video_file}")
    print(f"Path: {video_path}")
    
    # Load session
    session_data = get_session(profile_id)
    if not session_data:
        print(f"\n❌ Erro: Sessao nao encontrada para {profile_id}")
        return
    
    print(f"\n✅ Sessao carregada: @{session_data.get('username')}")
    
    # Execute upload
    print(f"\n🚀 Iniciando upload...")
    try:
        result = await upload_video_monitored(
            session_name=profile_id,
            video_path=video_path,
            caption="Teste de upload - validacao de bugs corrigidos",
            post=True,  # Post immediately
            enable_monitor=True
        )
        
        print(f"\n{'='*60}")
        print(f"RESULTADO:")
        print(f"{'='*60}")
        print(result)
        
        if result.get('status') == 'success':
            print(f"\n✅ SUCESSO: Video postado!")
        else:
            print(f"\n❌ FALHA: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_upload())
