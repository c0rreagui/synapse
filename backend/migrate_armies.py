import sys
import os

# Adiciona o diretório backend ao PYTHONPATH para importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MigrateArmy")

def run_migration():
    logger.info("Iniciando verificação da tabela 'armies'...")

    with engine.connect() as conn:
        # Verificar o dialect (postgresql ou sqlite)
        dialect = engine.dialect.name
        logger.info(f"Conectado ao banco usando dialeto: {dialect}")

        if dialect == "sqlite":
            # Para SQLite
            try:
                # Verifica se a coluna updated_at existe
                result = conn.execute(text("PRAGMA table_info(armies)")).fetchall()
                columns = [row[1] for row in result]
                
                if "created_at" not in columns:
                    conn.execute(text("ALTER TABLE armies ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                    logger.info("Coluna 'created_at' adicionada com sucesso no SQLite.")
                else:
                    logger.info("Coluna 'created_at' já existe no SQLite.")

                if "updated_at" not in columns:
                    conn.execute(text("ALTER TABLE armies ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                    logger.info("Coluna 'updated_at' adicionada com sucesso no SQLite.")
                else:
                    logger.info("Coluna 'updated_at' já existe no SQLite.")
                
                conn.commit()
            except Exception as e:
                logger.error(f"Erro ao tentar adicionar colunas no SQLite: {e}")
                
        elif dialect == "postgresql":
            # Para PostgreSQL
            try:
                # Adicionar created_at
                conn.execute(text("ALTER TABLE armies ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()"))
                logger.info("Coluna 'created_at' adicionada/verificada com sucesso no PostgreSQL.")
                
                # Adicionar updated_at
                conn.execute(text("ALTER TABLE armies ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()"))
                logger.info("Coluna 'updated_at' adicionada/verificada com sucesso no PostgreSQL.")
                
                conn.commit()
            except Exception as e:
                logger.error(f"Erro ao criar/atualizar colunas no PostgreSQL: {e}")
        else:
            logger.error(f"Dialeto {dialect} não suportado para esta migração automática.")

if __name__ == "__main__":
    run_migration()
