import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Set env to force Postgres
os.environ["POSTGRES_SERVER"] = "localhost"
os.environ["POSTGRES_USER"] = "synapse"
os.environ["POSTGRES_PASSWORD"] = "synapse_password"
os.environ["POSTGRES_DB"] = "synapse_db"

from core import session_manager

# Test get_profile_metadata
result = session_manager.get_profile_metadata('tiktok_profile_1770307556827')
print(f"Metadata result: {result}")
print(f"Active status: {result.get('active')}")
