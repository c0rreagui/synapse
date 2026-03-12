"""
Migration: Adiciona coluna 'auto_approve' a tabela 'twitch_targets'.
=======================================================================

Bug Fix para SYN-XXX: 'TwitchTarget' object has no attribute 'auto_approve'
O worker.py referenciava target.auto_approve mas a coluna nunca existiu no modelo.
Isso causava crash em 100% dos jobs do pipeline, impedindo videos de chegar na aprovacao.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.database import engine
from sqlalchemy import text, inspect

def migrate():
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns("twitch_targets")]

    if "auto_approve" in columns:
        print("[MIGRATION] Coluna 'auto_approve' já existe em 'twitch_targets'. Nada a fazer.")
        return

    dialect = engine.dialect.name  # "postgresql" ou "sqlite"
    
    with engine.begin() as conn:
        if dialect == "postgresql":
            conn.execute(text(
                "ALTER TABLE twitch_targets ADD COLUMN auto_approve BOOLEAN DEFAULT FALSE"
            ))
        else:
            # SQLite
            conn.execute(text(
                "ALTER TABLE twitch_targets ADD COLUMN auto_approve BOOLEAN DEFAULT 0"
            ))
    
    print("[MIGRATION] ✅ Coluna 'auto_approve' adicionada com sucesso a 'twitch_targets'.")

    # Verificacao pos-migration
    inspector2 = inspect(engine)
    columns2 = [col["name"] for col in inspector2.get_columns("twitch_targets")]
    assert "auto_approve" in columns2, "FALHA: Coluna não encontrada após migration!"
    print("[MIGRATION] ✅ Verificação pós-migration OK.")

if __name__ == "__main__":
    migrate()
