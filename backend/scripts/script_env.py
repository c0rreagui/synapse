import sys
import os
import dotenv

def setup_script_env():
    """
    Sets up the environment for running backend scripts from the Host machine.
    - Loads .env file
    - Adds backend to sys.path
    - Forces POSTGRES_SERVER to 'localhost' if not running in Docker
    """
    # 1. Add Backend to Path
    current_dir = os.path.dirname(os.path.abspath(__file__)) # backend/scripts
    backend_dir = os.path.dirname(current_dir) # backend
    if backend_dir not in sys.path:
        sys.path.append(backend_dir)
        print(f"[SCRIPT_ENV] Added {backend_dir} to sys.path")

    # 2. Load .env
    env_path = os.path.join(backend_dir, ".env")
    if os.path.exists(env_path):
        dotenv.load_dotenv(env_path)
        print(f"[SCRIPT_ENV] Loaded .env from {env_path}")
    else:
        print(f"[SCRIPT_ENV] Warning: .env not found at {env_path}")

    # 3. Detect Docker vs Host
    # In docker, usually hostname is random string or set explicitly.
    # A simple check: if POSTGRES_SERVER is 'db' (default in docker-compose) 
    # BUT we are running main (which implies manual execution often), we might check connectivity.
    # Simpler: If running a script, we usually want localhost unless explicitly told otherwise.
    
    server = os.getenv("POSTGRES_SERVER")
    
    # If server is 'db' (from .env), but we can't resolve 'db', we are likely on Host.
    # We'll just force localhost for convenience if we are executing a script interactively.
    
    # Heuristic: If we are in this function, we are likely running a script manually.
    # If the env says "db" OR is missing, we override to "localhost".
    if server == "db" or not server:
        print(f"[SCRIPT_ENV] Detected POSTGRES_SERVER='{server}'. Forcing 'localhost' for script execution on Host.")
        os.environ["POSTGRES_SERVER"] = "localhost"
    
    # Ensure other credentials exist
    if not os.getenv("POSTGRES_USER"):
        print("[SCRIPT_ENV] POSTGRES_USER not set. Defaulting to 'synapse'.")
        os.environ["POSTGRES_USER"] = "synapse"
        
    if not os.getenv("POSTGRES_PASSWORD"):
        print("[SCRIPT_ENV] POSTGRES_PASSWORD not set. Defaulting to 'synapse_password'.")
        os.environ["POSTGRES_PASSWORD"] = "synapse_password"
        
    if not os.getenv("POSTGRES_DB"):
        print("[SCRIPT_ENV] POSTGRES_DB not set. Defaulting to 'synapse_db'.")
        os.environ["POSTGRES_DB"] = "synapse_db"

    print(f"[SCRIPT_ENV] Database Target: {os.environ.get('POSTGRES_SERVER')}/{os.environ.get('POSTGRES_DB')}")
