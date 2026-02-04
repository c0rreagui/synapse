import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from core.session_manager import update_profile_metadata, import_session
from core.database import SessionLocal, DB_PATH
from core.models import Profile

def run_mock():
    print(f"Using DB Path: {DB_PATH}")
    db = SessionLocal()
    try:
        # Find the profile we used for testing
        p = db.query(Profile).filter(Profile.label == "Visual Error Test").first()
        
        if not p:
            print("Profile 'Visual Error Test' not found. searching for any profile...")
            p = db.query(Profile).first()
            
        if not p:
            print("No profiles found. Creating one...")
            pid = import_session("Visual Error Test", "[]", username="mock_tester")
            p = db.query(Profile).filter(Profile.slug == pid).first()
            
        print(f"Targeting Profile: {p.label} ({p.slug})")
        
        # Inject Mock Screenshot URL
        mock_url = "https://ui-avatars.com/api/?name=Error+Screenshot&background=ff0000&color=fff&size=512" 
        
        success = update_profile_metadata(p.slug, {
            "last_error_screenshot": mock_url
        })
        
        if success:
            print(f"SUCCESS: Injected mock screenshot URL into {p.slug}")
            # Verify persistence
            db.refresh(p)
            print(f"Verification - Metadata in DB: {p.last_seo_audit}")
        else:
            print("FAILED to update metadata.")
            
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_mock()
