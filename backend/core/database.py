from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Create engine for SQLite
# We use check_same_thread=False because FastAPI runs in multiple threads but SQLite 
# connection is usually thread-bound. For simple apps this is fine.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# BASE_DIR is .../backend
DB_PATH = os.path.join(BASE_DIR, "synapse.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine
# [SYN-FIX] Enable WAL Mode for Concurrency
# SQLite standard mode locks the whole file for writing, causing "disk I/O error" or "db locked"
# when API and Scheduler try to write simultaneously. WAL allows concurrent readers and writers.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    pool_pre_ping=True
)

from sqlalchemy import event
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

from contextlib import contextmanager

@contextmanager
def safe_session():
    """
    Context manager for safe DB operations.
    Ensures session is always closed.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_db():
    """FastAPI Dependency."""
    with safe_session() as db:
        yield db
