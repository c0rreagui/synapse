import json
import os
from datetime import datetime

def check_cookie_validity(profile_name):
    """Checks if cookies in a session file are likely still valid"""
    session_path = os.path.join(
        r"C:\APPS - ANTIGRAVITY\Synapse\backend\data\sessions",
        f"{profile_name}.json"
    )
    
    print(f"\n{'='*70}")
    print(f"ANALISANDO: {profile_name}")
    print(f"{'='*70}")
    
    if not os.path.exists(session_path):
        print(f"ERRO: Arquivo nao encontrado: {session_path}")
        return False
    
    # File metadata
    file_size = os.path.getsize(session_path)
    file_mtime = os.path.getmtime(session_path)
    last_modified = datetime.fromtimestamp(file_mtime)
    
    print(f"\n1. ARQUIVO:")
    print(f"   Caminho: {session_path}")
    print(f"   Tamanho: {file_size} bytes")
    print(f"   Ultima modificacao: {last_modified}")
    days_old = (datetime.now() - last_modified).days
    print(f"   Idade: {days_old} dias")
    
    # Load and analyze cookies
    with open(session_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cookies = data.get('cookies', [])
    print(f"\n2. COOKIES ENCONTRADOS: {len(cookies)}")
    
    # Check important session cookies
    important_cookies = ['sessionid', 'sid_tt', 'sid_guard']
    found_important = {}
    
    now_timestamp = datetime.now().timestamp()
    any_expired = False
    
    for cookie in cookies:
        name = cookie.get('name')
        expires = cookie.get('expires', -1)
        
        if name in important_cookies:
            found_important[name] = cookie
            
            if expires == -1:
                status = "Session (sem expiracao)"
            else:
                exp_date = datetime.fromtimestamp(expires)
                if expires < now_timestamp:
                    status = f"EXPIRADO em {exp_date}"
                    any_expired = True
                else:
                    days_remaining = (exp_date - datetime.now()).days
                    status = f"Valido ate {exp_date} ({days_remaining} dias)"
            
            print(f"   - {name}: {status}")
    
    # Meta info
    if 'synapse_meta' in data:
        meta = data['synapse_meta']
        print(f"\n3. INFORMACOES DA CONTA:")
        print(f"   Username: {meta.get('username', 'N/A')}")
        print(f"   Display: {meta.get('display_name', 'N/A')}")
        
        if 'last_checked' in meta:
            last_check = datetime.fromtimestamp(meta['last_checked'])
            print(f"   Ultima verificacao: {last_check}")
    
    # Verdict
    print(f"\n4. VEREDICTO:")
    if any_expired:
        print(f"   STATUS: COOKIES EXPIRADOS")
        print(f"   ACAO: Renovacao necessaria")
        is_valid = False
    elif days_old > 7:
        print(f"   STATUS: COOKIES ANTIGOS (mais de 7 dias)")
        print(f"   ACAO: Renovacao recomendada")
        is_valid = False
    else:
        print(f"   STATUS: COOKIES PARECEM VALIDOS")
        print(f"   ACAO: Pode tentar usar, mas teste primeiro")
        is_valid = True
    
    return is_valid

# Main
print("\n" + "#"*70)
print("#  ANALISE DE COOKIES - PERFIS 1 E 2")
print("#"*70)

results = {}
results["tiktok_profile_01"] = check_cookie_validity("tiktok_profile_01")
results["tiktok_profile_02"] = check_cookie_validity("tiktok_profile_02")

# Summary
print("\n" + "="*70)
print("RESUMO")
print("="*70)
for profile, is_valid in results.items():
    icon = "?" if is_valid else "X"
    status = "Provavelmente OK" if is_valid else "REQUER RENOVACAO"
    print(f"  [{icon}] {profile}: {status}")

print("\n" + "="*70)
if all(results.values()):
    print("CONCLUSAO: Cookies parecem OK, mas teste necessario")
else:
    print("CONCLUSAO: RENOVACAO DE COOKIES NECESSARIA")
    print("\nProximo passo: Rodar script de renovacao manualmente")
print("="*70)
