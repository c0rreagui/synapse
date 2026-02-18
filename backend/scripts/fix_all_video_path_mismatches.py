import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import scripts.script_env
scripts.script_env.setup_script_env()

from sqlalchemy import create_engine, text

# Connect to Postgres
DATABASE_URL = "postgresql://synapse:synapse_password@localhost:5432/synapse_db"
engine = create_engine(DATABASE_URL)

# Profile 2 videos available (from docker ls)
available_videos_profile_2 = [
    "/app/data/pending/ptiktok_profile_1770307556827_1463ab54.mp4",
    "/app/data/pending/ptiktok_profile_1770307556827_2818295e.mp4",
    "/app/data/pending/ptiktok_profile_1770307556827_b52f9ed1.mp4",
]

# Mismatched items for Profile 2 (from audit)
mismatched_items = [2, 10, 12, 14, 16, 22, 24, 26, 28, 34, 36, 38, 40, 42, 44, 46, 48, 50, 54, 56, 58, 60, 62, 64, 66, 68, 70, 72, 74, 76, 78, 80, 82, 84, 86]

print(f"=== CORRIGINDO {len(mismatched_items)} MISMATCHES ===\n")
print(f"Videos disponiveis para Profile 2: {len(available_videos_profile_2)}")

if len(available_videos_profile_2) < len(mismatched_items):
    print(f"\n[AVISO] Apenas {len(available_videos_profile_2)} videos disponiveis para {len(mismatched_items)} items!")
    print("Vou usar os mesmos videos em loop para cobrir todos os items.\n")

with engine.connect() as conn:
    updated = 0
    
    for idx, item_id in enumerate(mismatched_items):
        # Cycle through available videos
        video_path = available_videos_profile_2[idx % len(available_videos_profile_2)]
        
        conn.execute(text("""
            UPDATE schedule 
            SET video_path = :video_path
            WHERE id = :item_id
        """), {"video_path": video_path, "item_id": item_id})
        
        updated += 1
        print(f"[OK] Item {item_id}: {video_path}")
    
    conn.commit()
    
    print(f"\n[CONCLUIDO] {updated} items atualizados com sucesso!")
