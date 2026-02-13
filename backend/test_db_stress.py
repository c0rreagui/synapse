import threading
import time
import random
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from core.models import Profile
from core.database_utils import with_db_retries
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("stress_test")

@with_db_retries(max_retries=10, base_delay=0.1)
def stress_update(thread_id):
    db = SessionLocal()
    try:
        # Simulate work
        time.sleep(random.uniform(0.01, 0.05))
        
        # Write operation
        # We update the FIRST profile found
        profile = db.query(Profile).first()
        if profile:
            # Update a timestamp to force a write
            profile.updated_at = datetime.now()
            db.commit()
            logger.info(f"Thread {thread_id} success")
            return True
        else:
            logger.warning(f"Thread {thread_id} - No profile found")
            return False
            
    except Exception as e:
        logger.error(f"Thread {thread_id} failed finally: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

def run_stress_test():
    print("Starting Stress Test with 20 concurrent threads...")
    threads = []
    start_time = time.time()
    
    for i in range(20): # 20 concurrent threads
        t = threading.Thread(target=stress_update, args=(i,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    end_time = time.time()
    print(f"Stress Test Complete in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    run_stress_test()
