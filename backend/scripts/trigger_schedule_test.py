import requests
import os
import shutil
from datetime import datetime, timedelta

def main():
    print("🕒 Starting Schedule Test Trigger...")

    # 1. Calculate Date: Tomorrow at 10:00 AM
    tomorrow = datetime.now() + timedelta(days=1)
    schedule_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    # Ensure format matches what API expects (string) - Ingestion endpoint handles it. 
    # The prompt asked for "ISO format compatible with API". 
    # If the API expects what the frontend sends, it likely takes "YYYY-MM-DDTHH:MM" or similar.
    # Frontend usually sends `datetime-local` value which is `YYYY-MM-DDTHH:MM`.
    schedule_time_str = schedule_time[:16] # Cut off seconds/ms for safety if needed, or keep full ISO.
    
    print(f"📅 Target Schedule Time: {schedule_time_str}")

    # 2. Locate Video
    # Assuming we run this from backend folder or root. Let's find absolute paths.
    # Current file is in backend/tools/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir)
    
    # Try to find existing dummy
    possible_video = os.path.join(backend_dir, "dummy_video.mp4")
    target_video_path = os.path.join(current_dir, "teste_agendamento.mp4")

    if os.path.exists(possible_video):
        print(f"✅ Found dummy video at: {possible_video}")
        shutil.copy(possible_video, target_video_path)
    else:
        print("⚠️ Dummy video not found, creating a new one...")
        with open(target_video_path, "wb") as f:
            f.write(b"FAKE_VIDEO_CONTENT_FOR_TESTING_SCHEDULE")

    # 3. Disparar API
    url = "http://127.0.0.1:8000/api/v1/ingest/upload"
    payload = {
        "profile_id": "p1",
        "schedule_time": schedule_time_str,
        "viral_music_enabled": True
    }
    
    files = {
        "file": ("teste_agendamento.mp4", open(target_video_path, "rb"), "video/mp4")
    }

    print(f"🚀 Making POST request to: {url}")
    print(f"📦 Payload: {payload}")
    
    try:
        response = requests.post(url, data=payload, files=files)
        
        print("\n" + "="*40)
        print(f"📡 API Status Code: {response.status_code}")
        try:
            print(f"📄 Response JSON: {response.json()}")
        except:
            print(f"📄 Response Text: {response.text}")
        print("="*40 + "\n")

        if response.status_code == 200:
            print(f"🚀 Disparo de teste enviado! Agendado para: {schedule_time_str}")
        else:
            print("❌ Falha no envio.")
            
    except Exception as e:
        print(f"❌ Erro na conexao: {e}")
    finally:
        # Cleanup
        if os.path.exists(target_video_path):
            try:
                os.remove(target_video_path)
                print("🧹 Test file cleaned up.")
            except:
                pass

if __name__ == "__main__":
    main()
