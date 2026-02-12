import sys
import os
import json
import glob
from datetime import datetime

# Adjust path to find core modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from core.models import ScheduleItem
from core.config import DATA_DIR, BASE_DIR, SESSIONS_DIR

DIRS = {
    "approved": os.path.join(DATA_DIR, "approved"),
    "processing": os.path.join(BASE_DIR, "processing"),
    "done": os.path.join(BASE_DIR, "done"),
    "errors": os.path.join(BASE_DIR, "errors"),
    "pending": os.path.join(DATA_DIR, "pending")
}

def check_session_health():
    print("\n--- SESSION HEALTH ---")
    session_files = glob.glob(os.path.join(SESSIONS_DIR, "*.json"))
    for s_file in session_files:
        name = os.path.basename(s_file)
        try:
            with open(s_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            cookies = data.get("cookies", []) if isinstance(data, dict) else data
            
            # Simple expiry check
            expired_count = 0
            total_cookies = len(cookies)
            now = datetime.now().timestamp()
            
            for c in cookies:
                if c.get('expires', 0) > 0 and c.get('expires', 0) < now:
                    expired_count += 1
            
            status = "[OK]"
            if expired_count > 0:
                status = "[WARN]"
            if total_cookies == 0:
                status = "[EMPTY]"
                
            print(f"{name}: {status} ({total_cookies} cookies, {expired_count} expired)")
            
        except Exception as e:
            print(f"{name}: [ERROR] Invalid JSON - {e}")

def scan_codebase_paths():
    print("\n--- CODEBASE PATH AUDIT ---")
    # Simple grep equivalent
    root_dir = os.path.dirname(os.path.abspath(__file__))
    suspicious_patterns = ["/app/data", "/tmp", "\\app\\data", "C:\\tmp"]
    
    for root, dirs, files in os.walk(root_dir):
        if "venv" in root or "__pycache__" in root or ".git" in root:
            continue
            
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            for pattern in suspicious_patterns:
                                if pattern in line:
                                    print(f"[WARN] Found '{pattern}' in {os.path.relpath(path, root_dir)}:{i+1}")
                except Exception as e:
                    print(f"[ERR] Could not read {file}: {e}")

def deep_audit():
    print(f"=== DEEP SYSTEM AUDIT {datetime.now()} ===")
    
    # 1. Build File Index & Check Orphans
    print("\n--- FILE & METADATA INTEGRITY ---")
    all_files_on_disk = set()
    file_map = {} # filename -> path
    
    for name, path in DIRS.items():
        if os.path.exists(path):
            files = os.listdir(path)
            for f in files:
                full_path = os.path.join(path, f)
                if os.path.isfile(full_path):
                    all_files_on_disk.add(full_path)
                    file_map[f] = full_path

    # 2. Database Check
    db = SessionLocal()
    items = db.query(ScheduleItem).all()
    print(f"Total DB Items: {len(items)}")
    
    known_db_files = set()
    
    for item in items:
        if not item.video_path:
            print(f"[{item.id}] [WARN] No video_path set")
            continue
            
        # Normalize path
        norm_path = os.path.normpath(item.video_path)
        known_db_files.add(norm_path)
        
        # Check Existence
        if not os.path.exists(norm_path):
             print(f"[{item.id}] [FAIL] Missing file: {item.video_path}")
        else:
             # Check Metadata Sidecar
             if norm_path.endswith(".mp4"):
                 json_path = norm_path + ".json"
                 if not os.path.exists(json_path):
                      print(f"[{item.id}] [WARN] Missing sidecar JSON: {json_path}")

    # 3. Find Orphans (Files on disk NOT in DB)
    print("\n--- ORPHANED FILES ---")
    orphans = 0
    for fpath in all_files_on_disk:
        if fpath.endswith(".mp4"):
            norm_fpath = os.path.normpath(fpath)
            if norm_fpath not in known_db_files:
                print(f"[ORPHAN] Found video not in DB: {fpath}")
                orphans += 1
    
    if orphans == 0:
        print("No orphaned video files found.")

    # 4. Session Health
    check_session_health()
    
    # 5. Codebase Paths
    scan_codebase_paths()
    
    print("\n=== AUDIT COMPLETE ===")

if __name__ == "__main__":
    deep_audit()
