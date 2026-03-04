"""
TESTE FINAL ISOLADO - SEM RACE CONDITIONS
"""
import asyncio
import sys
import logging
import os

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

from core.manual_executor import execute_approved_video

async def test():
    print("\n" + "="*70)
    print("TESTE FINAL - test_final.mp4 (Perfil 1, Privacy: Somente Eu)")
    print("="*70)
    
    print("\nChamando manual_executor.execute_approved_video()...")
    print("Aguarde: navegador vai abrir, fazer login, upload, selecionar privacidade\n")
    
    try:
        result = await execute_approved_video("test_final.mp4")
        
        print("\n" + "="*70)
        print("RESULTADO")
        print("="*70)
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")
        
        if result.get('status') == 'ready':
            print("\n✓ SUCESSO - Video foi processado e agendado!")
        elif result.get('status') == 'error':
            print(f"\n✗ ERRO - {result.get('message')}")
        
        # Check monitor
        monitor_dir = r"C:\APPS - ANTIGRAVITY\Synapse\MONITOR\runs"
        if os.path.exists(monitor_dir):
            folders = sorted([f for f in os.listdir(monitor_dir) if "20260114" in f], reverse=True)
            if folders:
                latest = folders[0]
                print(f"\nMonitor folder: {latest}")
        
        return result
        
    except Exception as e:
        print(f"\n✗ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(test())
        exit_code = 0 if result.get('status') == 'ready' else 1
        exit(exit_code)
    finally:
        loop.close()
