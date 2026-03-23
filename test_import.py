import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
try:
    from core.session_manager import save_session
    print("SUCCESS: save_session imported")
except ImportError as e:
    print(f"IMPORT ERROR: {e}")
except Exception as e:
    print(f"OTHER ERROR: {e}")
