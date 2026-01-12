import requests
import json

url = "http://localhost:8000/api/v1/oracle/reply"
payload = {
    "comment": "Esse vídeo é fake! Não acredito.",
    "tone": "Hater Neutralizer",
    "context": "Vídeo sobre IA generativa"
}
headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Reply:")
        print(response.json())
    else:
        print("Error Response:")
        print(response.text)
except Exception as e:
    print(f"Request failed: {e}")
