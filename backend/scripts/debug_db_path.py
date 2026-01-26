import sys
import os
# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.database import engine, SQLALCHEMY_DATABASE_URL, DB_PATH
from core.models import Profile
from sqlalchemy.orm import sessionmaker

def check():
    print(f"CWD: {os.getcwd()}")
    print(f"DB_PATH resolved to: {DB_PATH}")
    print(f"Engine URL: {SQLALCHEMY_DATABASE_URL}")
    print(f"File exists at DB_PATH? {os.path.exists(DB_PATH)}")
    
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        count = db.query(Profile).count()
        print(f"Profile Count in DB: {count}")
    finally:
        db.close()

if __name__ == "__main__":
    check()
