import asyncio
from datetime import datetime, timedelta
from core import session_manager
from core.oracle.seo_engine import seo_engine
# from core.oracle.deep_analytics import deep_analytics # (If we want auto-analytics)

class OracleAutomator:
    """
    Suite de Automação do Oracle V2.
    Gerencia a execução autônoma de tarefas de inteligência.
    """
    
    def __init__(self):
        self.is_running = False
        self.tasks = []

    async def start_loop(self):
        """Inicia o loop de verificação de tarefas automáticas."""
        self.is_running = True
        print("🤖 Oracle Automation: Engine Started")
        while self.is_running:
            try:
                await self.check_and_run_tasks()
            except Exception as e:
                import traceback
                print(f"⚠️ Oracle Automation Error: {e}")
                traceback.print_exc()
            
            # Verifica a cada 30 minutos (1800s)
            await asyncio.sleep(1800)

    async def check_and_run_tasks(self):
        """Verifica perfis que precisam de auditoria ou spy."""
        sessions = session_manager.list_available_sessions()
        
        for session in sessions:
            profile_id = session.get("id")
            metadata = session_manager.get_profile_metadata(profile_id)
            
            # --- TAREFA 1: Auto Audit (Semanal) ---
            last_audit_iso = metadata.get("last_audit_date")
            should_run_audit = False
            
            if not last_audit_iso:
                should_run_audit = True
            else:
                try:
                    last_audit = datetime.fromisoformat(last_audit_iso)
                    if datetime.now() - last_audit > timedelta(days=7):
                        should_run_audit = True
                except ValueError:
                    logger.warning(f"⚠️ Invalid date format for profile {profile_id}: {last_audit_iso}. Forcing audit.")
                    should_run_audit = True
            
            if should_run_audit:
                print(f"🤖 Auto-Oracle: Executing Scheduled Audit for {profile_id}")
                # Executa em thread separada para não bloquear
                await asyncio.to_thread(seo_engine.audit_profile, metadata)
                session_manager.update_profile_metadata(profile_id, {
                    "last_audit_date": datetime.now().isoformat()
                })

            # --- TAREFA 2: Competitor Watch (Diário) ---
            # Implementação futura se tiver lista de competidores no metadata
            competitors = metadata.get("monitored_competitors", [])
            for comp in competitors:
                # Lógica similar...
                pass

    def stop(self):
        self.is_running = False

oracle_automator = OracleAutomator()
