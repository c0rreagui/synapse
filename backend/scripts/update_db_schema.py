from core.database import engine
from core.models import Base

def update_schema():
    print("... Updating Database Schema...")
    Base.metadata.create_all(bind=engine)
    print("OK: Schema Updated! (New tables created if missing)")

if __name__ == "__main__":
    update_schema()
