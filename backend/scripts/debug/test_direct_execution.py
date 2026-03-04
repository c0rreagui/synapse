"""
TESTE COMPLETO END-TO-END COM LOGS DETALHADOS
Testa aprovacao -> queue_worker -> upload com captura de erros
"""
import asyncio
import os
import sys
import logging
import time

# Setup Windows event loop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from core.manual_executor import execute_approved_video

async def test_direct_execution(video_id, profile_name):
    """
    Testa execucao direta do manual_executor (bypass queue_worker)
    para identificar exatamente onde o erro ocorre
    """
    print("\n" + "="*70)
    print(f"TESTE DIRETO: {video_id} -> {profile_name}")
    print("="*70)
    
    # Check if file exists in approved
    approved_dir = r"C:\APPS - ANTIGRAVITY\Synapse\backend\data\approved"
    video_file = f"{video_id}.mp4"
    video_path = os.path.join(approved_dir, video_file)
    json_path = os.path.join(approved_dir, f"{video_file}.json")
    
    if not os.path.exists(video_path):
        print(f"ERRO: Video nao encontrado em approved/: {video_path}")
        return
    
    print(f"\n1. Arquivo encontrado: {video_file}")
    print(f"   JSON: {'SIM' if os.path.exists(json_path) else 'NAO'}")
    
    print(f"\n2. Iniciando execucao do manual_executor...")
    print(f"   (Verifique se uma janela do navegador abre)")
    
    try:
        start = time.time()
        result = await execute_approved_video(video_file)
        duration = time.time() - start
        
        print(f"\n3. RESULTADO RETORNADO:")
        print(f"   Tempo: {duration:.1f}s")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
        
        if result.get('status') == 'error':
            print(f"\n>>> FALHOU COM ERRO <<<")
        elif result.get('status') == 'ready':
            print(f"\n>>> SUCESSO <<<")
        else:
            print(f"\n>>> STATUS DESCONHECIDO <<<")
            
        return result
        
    except Exception as e:
        print(f"\n>>> EXCECAO DURANTE EXECUCAO <<<")
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

async def main():
    print("\n" + "#"*70)
    print("#  TESTE END-TO-END COM DIAGNOSTICO COMPLETO")
    print("#"*70)
    
    # Test with Profile 1
    print("\nTestando com Perfil 1...")
    result1 = await test_direct_execution("p1_f854fcba", "tiktok_profile_01")
    
    print("\n" + "="*70)
    print("TESTE CONCLUIDO")
    print("="*70)
    
    if result1 and result1.get('status') == 'ready':
        print("\nSUCESSO! O bot conseguiu processar o video.")
        print("O problema anterior era provavelmente timing do queue_worker.")
    else:
        print("\nFALHA! Ha um bug no manual_executor ou uploader.")
        print("Verifique os logs acima para diagnostico.")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
