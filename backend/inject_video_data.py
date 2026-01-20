from core import session_manager

profile_id = "tiktok_profile_02" # Opinião Viral (usually)
# Or find by username
sessions = session_manager.list_available_sessions()
for s in sessions:
    if "opiniao" in s.get("label", "").lower() or "viral" in s.get("label", "").lower():
        profile_id = s.get("id")
        break

print(f"Injecting videos for {profile_id}")

video_data = [
    {
        "cover": "https://p16-sign-va.tiktokcdn.com/tos-maliva-p-0068/7d3c5289050d4264a5d3d45c61988880_1690000000~tplv-tiktok-play.jpeg?x-expires=1738206000&x-signature=X", # Mock URL, might fail download but will trigger logic
        "desc": "Video Teste 1",
        "stats": {"playCount": 1000}
    }
]

# Use a real image URL if possible to avoid 403 in the backend Vision check
# But for now, let's assume the fallback works or mock valid URL?
# Actually, I'll use a placeholder image service.
video_data[0]["cover"] = "https://via.placeholder.com/150"

session_manager.update_profile_metadata(profile_id, {
    "recent_videos": video_data,
    "last_seo_audit": {} # Reset audit
})

print("✅ Injected video data")
