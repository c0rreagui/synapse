import requests
import sys

API_URL = "http://localhost:8000/api/v1/profiles/list"

def test_profiles_endpoint():
    print(f"🔌 Conectando ao endpoint: {API_URL} ...")
    try:
        response = requests.get(API_URL)
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ SUCESSO! Dados recebidos:")
            print("-" * 40)
            for item in data:
                print(f"🆔 ID:    {item.get('id')}")
                print(f"🏷️ Label: {item.get('label')}")
                print("-" * 40)
            
            if not data:
                print("⚠ Alerta: Lista retornou vazia (mas conexão funcionou).")
            else:
                print(f"📊 Total de perfis encontrados: {len(data)}")
        else:
            print(f"❌ ERRO: Servidor retornou código {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ ERRO: Não foi possível conectar ao servidor (localhost:8000).")
        print("💡 DICA: Verifique se o 'python tools/ignite.py' está rodando.")

if __name__ == "__main__":
    test_profiles_endpoint()
