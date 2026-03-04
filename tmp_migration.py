from app.api.endpoints.clipper import TwitchTarget
from core.database import engine, Base

print("Rebuilding Schema...")
Base.metadata.create_all(bind=engine)
print("Migration Complete.")
