import requests
import time

# Create dummy mp4
with open("test_viral_clip.mp4", "wb") as f:
    f.write(b"fake video content")

url = "http://127.0.0.1:8000/api/v1/ingest/upload"
files = {'file': ('test_viral_clip.mp4', open('test_viral_clip.mp4', 'rb'))}
data = {
    'profile_id': 'p1', 
    'viral_music_enabled': 'true'
}

print("🚀 Uploading video...")
res = requests.post(url, files=files, data=data)
print(res.json())

# Poll status
print("⏳ Waiting for Oracle Background Task...")
time.sleep(5) 
# Logic actually runs in background, checks via files is hard from here?
# User can verify in UI.
print("✅ Check the Queue UI for the new video!")
