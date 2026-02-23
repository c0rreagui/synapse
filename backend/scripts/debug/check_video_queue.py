from core.database import engine
from sqlalchemy import inspect, text

i = inspect(engine)
tables = i.get_table_names()
print("Tabelas no banco:")
print([t for t in sorted(tables)])
print()
if "video_queue" in tables:
    print("OK: tabela video_queue EXISTS no Postgres!")
    cols = [c["name"] for c in i.get_columns("video_queue")]
    print(f"Colunas: {cols}")
else:
    print("ERRO: tabela video_queue NAO EXISTE!")
