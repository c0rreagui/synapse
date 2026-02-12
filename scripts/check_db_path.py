
import sys
import os

# Set working directory to project root for consistency if needed, 
# but we want to know what happens in the subprocess.
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.database import DB_PATH

print(f"Current Working Directory: {os.getcwd()}")
print(f"Effective DB Path: {os.path.abspath(DB_PATH)}")
