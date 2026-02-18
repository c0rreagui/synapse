import sys
import os
import re

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import scripts.script_env
scripts.script_env.setup_script_env()

from sqlalchemy import create_engine, text
from datetime import datetime

# Connect to Postgres
DATABASE_URL = "postgresql://synapse:synapse_password@localhost:5432/synapse_db"
engine = create_engine(DATABASE_URL)

print("=" * 80)
print("AUDITORIA COMPLETA DE VIDEO PATH MISMATCHES")
print("=" * 80)
print()

with engine.connect() as conn:
    # 1. Obter todos os profiles
    profiles_result = conn.execute(text("""
        SELECT id, slug, label, active
        FROM profiles
        ORDER BY id
    """))
    profiles = profiles_result.fetchall()
    
    print(f"Total de Profiles: {len(profiles)}")
    print()
    
    total_mismatches = 0
    total_items_checked = 0
    corrections_made = []
    
    for profile in profiles:
        profile_id, profile_slug, profile_label, active = profile
        
        # 2. Buscar todos os items PENDENTES deste profile
        items_result = conn.execute(text("""
            SELECT id, profile_slug, video_path, status, scheduled_time
            FROM schedule
            WHERE profile_slug = :slug
            AND status IN ('pending', 'pending_approval', 'pending_analysis_oracle')
            ORDER BY id
        """), {"slug": profile_slug})
        
        items = items_result.fetchall()
        
        if not items:
            continue
            
        print(f"\n{'='*80}")
        print(f"Profile {profile_id}: {profile_label} ({profile_slug})")
        print(f"Status: {'ATIVO' if active else 'INATIVO'}")
        print(f"Items pendentes: {len(items)}")
        print(f"{'='*80}")
        
        profile_mismatches = []
        
        for item in items:
            item_id, item_profile_slug, video_path, status, scheduled_time = item
            total_items_checked += 1
            
            # Extrair profile do video_path
            # Padrões: ptiktok_profile_X_ ou tiktok_profile_X_
            match = re.search(r'(p?tiktok_profile_\d+)', video_path)
            
            if not match:
                print(f"  [AVISO] Item {item_id}: Não consegui extrair profile do path: {video_path}")
                continue
            
            path_profile = match.group(1)
            
            # Normalizar para comparação
            # Se video_path tem "ptiktok_profile_X", normalizar para "tiktok_profile_X"
            if path_profile.startswith('ptiktok_'):
                normalized_path_profile = path_profile[1:]  # Remove 'p' inicial
            else:
                normalized_path_profile = path_profile
            
            # Comparar
            if normalized_path_profile != item_profile_slug:
                print(f"  [MISMATCH] Item {item_id}:")
                print(f"    - DB profile_slug: {item_profile_slug}")
                print(f"    - Path profile: {path_profile} (normalized: {normalized_path_profile})")
                print(f"    - Video path: {video_path}")
                print(f"    - Status: {status}")
                print(f"    - Scheduled: {scheduled_time}")
                
                profile_mismatches.append({
                    'item_id': item_id,
                    'current_profile': item_profile_slug,
                    'path_profile': normalized_path_profile,
                    'video_path': video_path,
                    'status': status
                })
                total_mismatches += 1
        
        if profile_mismatches:
            print(f"\n  Total de mismatches neste profile: {len(profile_mismatches)}")
            corrections_made.extend(profile_mismatches)
    
    print()
    print("=" * 80)
    print("RESUMO DA AUDITORIA")
    print("=" * 80)
    print(f"Total de items verificados: {total_items_checked}")
    print(f"Total de mismatches encontrados: {total_mismatches}")
    print()
    
    if total_mismatches > 0:
        print("CORREÇÕES NECESSÁRIAS:")
        print()
        
        # Agrupar por perfil para facilitar correção
        from collections import defaultdict
        by_profile = defaultdict(list)
        
        for mismatch in corrections_made:
            target_profile = mismatch['path_profile']
            by_profile[target_profile].append(mismatch)
        
        for target_profile, items in by_profile.items():
            print(f"Profile {target_profile}: {len(items)} items precisam ser movidos")
        
        print()
        print("[?] Deseja aplicar as correções automaticamente? (y/n)")
        response = input().strip().lower()
        
        if response == 'y':
            print("\nAplicando correções...")
            
            for mismatch in corrections_made:
                item_id = mismatch['item_id']
                correct_profile = mismatch['path_profile']
                
                conn.execute(text("""
                    UPDATE schedule
                    SET profile_slug = :correct_profile
                    WHERE id = :item_id
                """), {"correct_profile": correct_profile, "item_id": item_id})
                
                print(f"  ✓ Item {item_id}: {mismatch['current_profile']} -> {correct_profile}")
            
            conn.commit()
            print(f"\n[OK] {len(corrections_made)} correções aplicadas!")
        else:
            print("\n[SKIP] Correções não aplicadas.")
    else:
        print("[OK] Nenhum mismatch encontrado! Todos os profiles estão consistentes.")
