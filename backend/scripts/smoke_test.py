"""
Synapse Smoke Test — Verificação de Saúde em < 30s
====================================================

Verifica os pontos críticos do sistema.
Uso: python scripts/smoke_test.py [--host HOST] [--port PORT]

Retorna exit code 0 se tudo OK, 1 se houver falhas.
"""

import sys
import time
import json
import argparse

try:
    import httpx
except ImportError:
    print("❌ httpx nao instalado. Rode: pip install httpx")
    sys.exit(1)


def check(client: httpx.Client, name: str, method: str, path: str, expect_key: str = None) -> bool:
    """Faz uma requisição e verifica se retorna 200 + chave esperada."""
    url = f"{client.base_url}{path}"
    try:
        if method == "GET":
            r = client.get(path)
        elif method == "POST":
            r = client.post(path)
        else:
            r = client.get(path)

        if r.status_code == 200:
            data = r.json()
            if expect_key and expect_key not in data:
                print(f"  ⚠️  {name}: 200 OK mas chave '{expect_key}' ausente")
                return False
            print(f"  ✅  {name}: OK ({r.elapsed.total_seconds():.2f}s)")
            return True
        else:
            print(f"  ❌  {name}: HTTP {r.status_code}")
            return False
    except httpx.ConnectError:
        print(f"  ❌  {name}: Conexão recusada")
        return False
    except Exception as e:
        print(f"  ❌  {name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Synapse Smoke Test")
    parser.add_argument("--host", default="localhost", help="Host do backend (default: localhost)")
    parser.add_argument("--port", default="8000", help="Porta do backend (default: 8000)")
    args = parser.parse_args()

    base = f"http://{args.host}:{args.port}"
    print(f"\n🔬 Synapse Smoke Test — {base}")
    print("=" * 50)

    start = time.time()
    results = []

    with httpx.Client(base_url=base, timeout=10.0) as client:
        # 1. Health
        results.append(check(client, "Health Endpoint", "GET", "/health", "status"))

        # 2. Profiles
        results.append(check(client, "Lista de Perfis", "GET", "/api/v1/profiles/list"))

        # 3. Scheduler Items
        results.append(check(client, "Scheduler Items", "GET", "/api/v1/scheduler/items"))

        # 4. Telemetry Vitals
        results.append(check(client, "Telemetry Vitals", "GET", "/api/v1/telemetry/vitals", "cpu_percent"))

        # 5. Factory Pending
        results.append(check(client, "Factory Pending", "GET", "/api/v1/factory/pending"))

        # 6. Oracle Status
        results.append(check(client, "Oracle Status", "GET", "/api/v1/oracle/status", "status"))

    elapsed = time.time() - start
    passed = sum(results)
    total = len(results)
    failed = total - passed

    print("=" * 50)
    print(f"📊 Resultado: {passed}/{total} checks passaram ({elapsed:.1f}s)")

    if failed:
        print(f"❌ {failed} check(s) falharam!")
        sys.exit(1)
    else:
        print("✅ Sistema saudável!")
        sys.exit(0)


if __name__ == "__main__":
    main()
