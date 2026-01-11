import requests
import sys

API_URL = "http://localhost:8000/api/v1"

def list_pending():
    print("Listing pending...")
    res = requests.get(f"{API_URL}/queue/pending")
    if res.status_code == 200:
        videos = res.json()
        print(f"Found {len(videos)} videos")
        for v in videos:
            print(f" - {v['id']} ({v['filename']})")
        return videos
    else:
        print(f"Failed to list: {res.status_code} {res.text}")
        return []

def delete_video(video_id):
    print(f"Deleting {video_id}...")
    res = requests.delete(f"{API_URL}/queue/{video_id}")
    if res.status_code == 200:
        print("Success!")
    else:
        print(f"Failed: {res.status_code} {res.text}")

if __name__ == "__main__":
    videos = list_pending()
    if videos:
        target = videos[0]['id']
        delete_video(target)
        list_pending()
    else:
        print("No videos to delete.")
