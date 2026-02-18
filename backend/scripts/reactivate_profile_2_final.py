import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import scripts.script_env
scripts.script_env.setup_script_env()

from sqlalchemy import create_engine, text

# Connect to Postgres
DATABASE_URL = "postgresql://synapse:synapse_password@localhost:5432/synapse_db"
engine = create_engine(DATABASE_URL)

print("=== REATIVANDO PROFILES ===\n")

with engine.connect() as conn:
    # Reactivate Profile 2
    conn.execute(text("""
        UPDATE profiles 
        SET active = true
        WHERE slug = 'tiktok_profile_1770307556827'
    """))
    
    conn.commit()
    
    # Verify
    result = conn.execute(text("SELECT id, slug, label, active FROM profiles ORDER BY id"))
    profiles = result.fetchall()
    
    print("Profiles apos reativacao:")
    for p in profiles:
        status = "ATIVO" if p[3] else "INATIVO"
        print(f"  ID {p[0]}: {p[2]} ({p[1]}) - {status}")
    
    print("\n[OK] Profile 2 reativado com sucesso!")
