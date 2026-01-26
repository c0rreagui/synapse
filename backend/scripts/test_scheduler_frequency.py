
import sys
import os
import json
from datetime import datetime, timedelta
import io

# Force UTF-8 for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.batch_manager import batch_manager
from core.scheduler import scheduler_service

def test_frequency_and_mix():
    print("🧪 Starting Scheduler & Auto-Mix Test...")
    
    # Mock Data
    files = [f"video_{i}.mp4" for i in range(5)]
    profiles = ["test_user"]
    start_time = datetime.now() + timedelta(minutes=10)
    
    # 1. Test "2x/Day" (Every 12h = 720 mins)
    # Also test Auto-Mix enabled
    print("\n--- TEST 1: 2x/Day (720 min) + Auto-Mix ---")
    
    # Mock trend_checker to return sounds without scraping
    # We patch it dynamically or rely on existing cache?
    # Let's assume cache exists or handle empty.
    
    batch_id = batch_manager.create_batch(
        files=files,
        profiles=profiles,
        start_time=start_time,
        interval_minutes=720, # 12 hours
        viral_music_enabled=True,
        mix_viral_sounds=True
    )
    
    batch = batch_manager._batches[batch_id]
    events = batch["events"]
    
    # Validate Frequency
    print(f"Events Created: {len(events)}")
    for i, e in enumerate(events):
        expected = start_time + timedelta(minutes=720 * i)
        diff = abs((e.scheduled_time - expected).total_seconds())
        
        status = "✅" if diff < 5 else "❌"
        print(f"[{i}] Time: {e.scheduled_time.strftime('%H:%M:%S')} | Expected: {expected.strftime('%H:%M:%S')} | {status}")
        
    # Validate Auto-Mix
    sounds = [e.metadata.get("sound_title") for e in events]
    print(f"\nSounds Assigned: {sounds}")
    unique_sounds = len(set([s for s in sounds if s]))
    
    if unique_sounds > 1:
        print(f"✅ Auto-Mix Working (Unique Sounds: {unique_sounds})")
    else:
        print("⚠️ Auto-Mix Warning: Sounds are identical (Cache might be empty)")
        
    # 2. Test "Every 4h" (240 mins)
    print("\n--- TEST 2: Every 4h (240 min) ---")
    batch_id_2 = batch_manager.create_batch(
        files=files[:3],
        profiles=profiles,
        start_time=start_time,
        interval_minutes=240
    )
    events_2 = batch_manager._batches[batch_id_2]["events"]
    
    for i, e in enumerate(events_2):
        expected = start_time + timedelta(minutes=240 * i)
        diff = abs((e.scheduled_time - expected).total_seconds())
        status = "✅" if diff < 5 else "❌"
        print(f"[{i}] Time: {e.scheduled_time.strftime('%H:%M:%S')} | Expected: {expected.strftime('%H:%M:%S')} | {status}")

if __name__ == "__main__":
    test_frequency_and_mix()
