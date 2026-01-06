import json
import requests
import os
import sys

# Carrega cookies do arquivo
SESSION_FILE = r"c:\APPS - ANTIGRAVITY\Synapse\backend\data\sessions\tiktok_profile_01.json"

def load_cookies(path):
    with open(path, 'r') as f:
        data = json.load(f)
        # O formato pode variar (Playwright state vs EditThisCookie)
        # O arquivo atual parece ser Playwright state ({cookies: [...], origins: []})
        if 'cookies' in data:
            cookies = {}
            for c in data['cookies']:
                cookies[c['name']] = c['value']
            return cookies
    return None

def check_profile():
    print(f"📂 Lendo sessão: {SESSION_FILE}")
    cookies = load_cookies(SESSION_FILE)
    
    if not cookies:
        print("❌ Cookies não encontrados")
        return

    print("🍪 Cookies carregados. Tentando API do TikTok...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.tiktok.com/",
    }

    # Tenta Endpoint de Info da Conta (Passport)
    try:
        url = "https://www.tiktok.com/passport/web/account/info/?aid=1459&app_language=pt-BR&app_name=tiktok_web"
        response = requests.get(url, cookies=cookies, headers=headers, timeout=10)
        
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # print(json.dumps(data, indent=2)) 
            
            user_data = data.get("data", {})
            if user_data:
                nickname = user_data.get("username", "") # Às vezes é screen_name
                unique_id = user_data.get("screen_name", "") # @handler
                avatar = user_data.get("avatar_url", "")
                
                print("\n✅ SUCESSO! Dados extraídos:")
                print(f"Nome: {nickname}")
                print(f"User (@): {unique_id}")
                print(f"Avatar: {avatar}")
            else:
                print("⚠️ JSON retornado mas sem dados de usuário (pode ter expirado/bloqueado).")
                print(data)
        else:
            print("❌ Falha na requisição.")
            
    except Exception as e:
        print(f"💥 Erro: {e}")

if __name__ == "__main__":
    check_profile()
