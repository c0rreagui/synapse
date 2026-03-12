from fastapi.testclient import TestClient
from app.main import app
import traceback

client = TestClient(app)

try:
    response = client.get("/api/clipper/pipeline")
    print("Status:", response.status_code)
    print("Body:", response.text)
except Exception as e:
    print("Exception occurred!")
    traceback.print_exc()

try:
    response = client.get("/openapi.json")
    print("Status openapi:", response.status_code)
except Exception as e:
    print("Exception occurred getting openapi!")
    traceback.print_exc()
