import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.session_manager import list_available_sessions

sessions = list_available_sessions()
print('\nPerfis disponiveis:')
print('=' * 60)
for s in sessions:
    print(f"ID: {s.get('id')}")
    print(f"Username: @{s.get('username')}")
    print(f"Active: {s.get('active')}")
    print('-' * 60)

print(f'\nTotal: {len(sessions)} perfis')
