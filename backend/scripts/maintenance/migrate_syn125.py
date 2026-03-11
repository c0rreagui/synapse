"""
Migração SYN-125: Cria a tabela twitch_known_streamers
=======================================================

Uso:
    cd backend/
    python scripts/maintenance/migrate_syn125.py

Este script usa Base.metadata.create_all() para criar APENAS
as tabelas que ainda não existem no banco, sem afetar as existentes.
"""

import os
import sys

# Adiciona backend/ ao sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.database import engine, Base

# Importa TODOS os modelos para que o Base.metadata conheça as tabelas
from core.clipper.models import TwitchKnownStreamer  # noqa: F401
from core.clipper.models import TwitchTarget, ClipJob  # noqa: F401


def migrate():
    print("=" * 60)
    print("SYN-125: Migrando banco de dados")
    print(f"Engine: {engine.url}")
    print("=" * 60)

    print("\n[1/2] Verificando tabelas existentes...")
    from sqlalchemy import inspect
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print(f"  Tabelas existentes: {existing_tables}")

    target_table = "twitch_known_streamers"
    if target_table in existing_tables:
        print(f"\n✅ Tabela '{target_table}' já existe. Nada a fazer.")
        return

    print(f"\n[2/2] Criando tabela '{target_table}'...")
    Base.metadata.create_all(bind=engine)

    # Verificação pós-migração
    inspector = inspect(engine)
    if target_table in inspector.get_table_names():
        print(f"\n✅ Migração concluída com sucesso! Tabela '{target_table}' criada.")
    else:
        print(f"\n❌ ERRO: Tabela '{target_table}' não foi criada. Verifique os logs.")
        sys.exit(1)


if __name__ == "__main__":
    migrate()
