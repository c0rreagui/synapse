import requests
import json

url = "http://localhost:8000/api/v1/oracle/rewrite_caption"
payload = {
    "draft": "Check out this new AI tool that edits video automatically",
    "tone": "Viral/Clickbait"
}
headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
    else:
        print("Error Response:")
        print(response.text)
except Exception as e:
    print(f"Request failed: {e}")
