import sys
import os
sys.path.append('/app')

from core.oracle.client import oracle_client

print("--- Testing Oracle Client ---")
print(f"Provider: {oracle_client.provider}")

try:
    print("Attempting to generate content...")
    response = oracle_client.generate_content("Say 'Groq is working'")
    print(f"Response: {response.text}")
    print("--- SUCCESS ---")
except Exception as e:
    print(f"--- FAILED ---")
    print(e)
    import traceback
    traceback.print_exc()
