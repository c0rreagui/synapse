
import os
import json
import glob
import sys

# Define target paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")
PROFILES_FILE = os.path.join(DATA_DIR, "profiles.json")

def fix_session_files():
    print("=== FIXING SESSION FILES METADATA ===")
    
    # 1. Load profiles.json (Manual Source of Truth)
    profiles_data = {}
    if os.path.exists(PROFILES_FILE):
        try:
            with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
                profiles_data = json.load(f)
            print(f"Loaded {len(profiles_data)} profiles from profiles.json")
        except Exception as e:
            print(f"Error reading profiles.json: {e}")
    
    # 2. Scan Session Files
    json_files = glob.glob(os.path.join(SESSIONS_DIR, "*.json"))
    for file_path in json_files:
        filename = os.path.basename(file_path)
        slug = os.path.splitext(filename)[0]
        
        print(f"\nProcessing {slug}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Normalize structure
            if isinstance(data, list):
                print("  - Converting legacy list format to dict")
                data = {"cookies": data}
            
            # Get existing meta
            meta = data.get("synapse_meta", {})
            
            # Determine correct label
            current_label = meta.get("display_name")
            new_label = current_label
            
            # Check profiles.json for override
            if slug in profiles_data:
                p_info = profiles_data[slug]
                possible_label = p_info.get("label")
                if possible_label and possible_label != "Restored Session" and possible_label != slug:
                     new_label = possible_label
                elif not current_label and possible_label:
                     new_label = possible_label
            
            # Check DB (via quick query if possible, or just hardcode based on known slugs)
            if slug == "tiktok_profile_1770135259969":
                new_label = "Vibe Cortes"  # Hardcode desired name
            elif slug == "tiktok_profile_1770307556827":
                new_label = "Opinião Viral"
            
            if new_label != current_label:
                print(f"  - Updating label: '{current_label}' -> '{new_label}'")
                meta["display_name"] = new_label
                meta["username"] = meta.get("username") or slug # Ensure username is set
                
                # Check avatar
                if slug in profiles_data and profiles_data[slug].get("avatar_url"):
                    meta["avatar_url"] = profiles_data[slug]["avatar_url"]
                
                data["synapse_meta"] = meta
                
                # Save
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                print("  - Saved.")
            else:
                print("  - No changes needed.")
                
        except Exception as e:
            print(f"  - Error processing file: {e}")

if __name__ == "__main__":
    fix_session_files()
