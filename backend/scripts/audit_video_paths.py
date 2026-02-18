import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import scripts.script_env
scripts.script_env.setup_script_env()

from sqlalchemy import create_engine, text

# Connect to Postgres
DATABASE_URL = "postgresql://synapse:synapse_password@localhost:5432/synapse_db"
engine = create_engine(DATABASE_URL)

print("=== AUDITORIA DE VIDEO_PATHS ===\n")

with engine.connect() as conn:
    # Get all pending schedule items
    result = conn.execute(text("""
        SELECT id, profile_slug, video_path, scheduled_time 
        FROM schedule 
        WHERE status = 'pending' AND video_path IS NOT NULL
        ORDER BY id
    """))
    
    items = result.fetchall()
    
    mismatches = []
    
    for item in items:
        item_id, profile_slug, video_path, scheduled_time = item
        
        # Extract profile from video_path
        if video_path and 'ptiktok_profile_' in video_path:
            # Extract profile ID from path
            path_parts = video_path.split('ptiktok_profile_')
            if len(path_parts) > 1:
                video_profile = 'tiktok_profile_' + path_parts[1].split('_')[0]
                
                if video_profile != profile_slug:
                    mismatches.append({
                        'id': item_id,
                        'profile_slug': profile_slug,
                        'video_profile': video_profile,
                        'video_path': video_path,
                        'scheduled_time': scheduled_time
                    })
                    print(f"[MISMATCH] Item {item_id}:")
                    print(f"   DB Profile: {profile_slug}")
                    print(f"   Path Profile: {video_profile}")
                    print(f"   Video Path: {video_path}")
                    print(f"   Scheduled: {scheduled_time}\n")
    
    if not mismatches:
        print("[OK] Todos os video_paths estao corretos!")
    else:
        print(f"\n[TOTAL] {len(mismatches)} MISMATCHES ENCONTRADOS")
        print("\nResumo:")
        for m in mismatches:
            print(f"  - Item {m['id']}: {m['profile_slug']} usando video de {m['video_profile']}")
