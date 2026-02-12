
import os
import sys

# The path from the DB response for item 25
path = r"D:\APPS - ANTIGRAVITY\Synapse\backend\data\pending\ptiktok_profile_1770135259969_7f7db1eb.mp4"

print(f"Checking path: {path}")
print(f"Exists: {os.path.exists(path)}")
print(f"Is File: {os.path.isfile(path)}")

# Also verify permissions
try:
    with open(path, 'rb') as f:
        print("Can read file: True")
except Exception as e:
    print(f"Can read file: False ({e})")

# Check DATA_DIR resolving
try:
    from core.config import DATA_DIR
    print(f"DATA_DIR from config: {DATA_DIR}")
    pending = os.path.join(DATA_DIR, "pending")
    print(f"Pending dir exists: {os.path.exists(pending)}")
    
    filename = os.path.basename(path)
    candidate = os.path.join(pending, filename)
    print(f"Candidate path: {candidate}")
    print(f"Candidate exists: {os.path.exists(candidate)}")
except ImportError:
    print("Could not import core.config (might need to set pythonpath)")
except Exception as e:
    print(f"Config check failed: {e}")
