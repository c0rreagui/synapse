from app.main import app
import traceback

try:
    schema = app.openapi()
    print("OpenAPI schema generated successfully")
except Exception as e:
    print("Exception generating OpenAPI:")
    traceback.print_exc()
