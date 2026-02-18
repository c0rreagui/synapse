import sys
import os

# [HARDENING] Unified Environment Loader
import script_env
script_env.setup_script_env()

from sqlalchemy.orm import Session
from core.database import SessionLocal
from core.models import Profile

def check_status():
    db = SessionLocal()
    try:
        profiles = db.query(Profile).all()
        print(f"Found {len(profiles)} profiles.")
        for p in profiles:
            print(f"Slug: {p.slug} | Label: {p.label} | Active: {p.active}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_status()
