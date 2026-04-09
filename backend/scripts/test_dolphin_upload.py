"""
Dolphin Upload Test Script
--------------------------
Tests the full Dolphin upload flow for dosealta_tv.

Run inside the backend container (with a video approved):
    docker exec -it synapse-backend python /app/scripts/test_dolphin_upload.py

Or with a specific slug:
    docker exec -it synapse-backend python /app/scripts/test_dolphin_upload.py dosealta_tv
"""
import os
import sys
import asyncio

sys.path.insert(0, "/app")
os.environ.setdefault("USE_DOLPHIN_UPLOADS", "true")

TARGET_SLUG = sys.argv[1] if len(sys.argv) > 1 else "dosealta_tv"


async def test_click_only():
    """Test only the click mechanism — no upload, no cookies. Quick sanity check."""
    print("\n[TEST] Phase 1: Testing _dolphin_click_start() only...")
    from core.database import SessionLocal
    from core.models import Profile
    from core.remote_session import _dolphin_click_start, _ensure_xvfb, _ensure_dolphin, _patch_dolphin_chrome

    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.slug == TARGET_SLUG).first()
        if not profile:
            print(f"  ❌ Profile '{TARGET_SLUG}' not found in DB")
            return False
        dolphin_name = getattr(profile, "dolphin_profile_name", None)
        if not dolphin_name:
            print(f"  ❌ dolphin_profile_name not set for '{TARGET_SLUG}'")
            print(f"     Set it first: curl -X PUT http://localhost:8000/api/v1/profiles/{TARGET_SLUG}/dolphin-name -H 'Content-Type: application/json' -d '{{\"dolphin_profile_name\": \"NAME\"}}'")
            return False
        print(f"  Profile found: slug={profile.slug!r} dolphin_name={dolphin_name!r}")
    finally:
        db.close()

    print("  Starting Xvfb + Dolphin...")
    await _ensure_xvfb()
    _ensure_dolphin()
    _patch_dolphin_chrome()
    print("  Infrastructure ready.")

    print(f"  Clicking START for '{dolphin_name}'...")
    try:
        await _dolphin_click_start(dolphin_name)
        print("  ✅ Click succeeded!")
        return True
    except Exception as e:
        print(f"  ❌ Click failed: {e}")
        return False


async def test_full_launch():
    """Test the full launch_browser_via_dolphin() including CDP connection."""
    print("\n[TEST] Phase 2: Testing launch_browser_via_dolphin()...")
    from core.remote_session import launch_browser_via_dolphin

    try:
        pw, browser, context, page = await launch_browser_via_dolphin(TARGET_SLUG)
        print(f"  ✅ CDP connected! page URL: {page.url!r}")

        # Navigate to TikTok Studio upload page as smoke test
        print("  Navigating to TikTok Studio upload...")
        await page.goto("https://www.tiktok.com/tiktokstudio/upload",
                        wait_until="domcontentloaded", timeout=30000)
        print(f"  ✅ Navigated to: {page.url!r}")

        # Take screenshot as proof
        os.makedirs("/app/downloads", exist_ok=True)
        await page.screenshot(path=f"/app/downloads/dolphin_upload_test_{TARGET_SLUG}.png")
        print(f"  📸 Screenshot: /app/downloads/dolphin_upload_test_{TARGET_SLUG}.png")

        await browser.close()
        await pw.stop()
        return True
    except Exception as e:
        print(f"  ❌ Launch failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def find_approved_video():
    """Find a video in the approval queue for TARGET_SLUG."""
    print(f"\n[TEST] Looking for approved video for '{TARGET_SLUG}'...")
    try:
        from core.database import SessionLocal
        from core.models import Profile

        db = SessionLocal()
        try:
            profile = db.query(Profile).filter(Profile.slug == TARGET_SLUG).first()
            if not profile:
                print(f"  Profile '{TARGET_SLUG}' not found")
                return None
            profile_id = profile.id
        finally:
            db.close()

        import httpx
        # Query the scheduler/queue API for approved videos
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"http://localhost:8000/api/v1/scheduler/queue",
            )
            if resp.status_code == 200:
                queue = resp.json()
                approved = [
                    v for v in queue
                    if v.get("status") == "approved"
                    and (v.get("profile_slug") == TARGET_SLUG or v.get("profile_id") == profile_id)
                ]
                if approved:
                    print(f"  ✅ Found {len(approved)} approved video(s):")
                    for v in approved:
                        print(f"     id={v.get('id')} title={v.get('title', '?')!r}")
                    return approved[0]
                else:
                    print(f"  ℹ️  No approved videos for '{TARGET_SLUG}' in queue")
                    return None
    except Exception as e:
        print(f"  ⚠️  Could not check queue: {e}")
        return None


async def main():
    print("=" * 60)
    print(f"Dolphin Upload Test — Profile: {TARGET_SLUG}")
    print("=" * 60)

    # Phase 1: Click test
    click_ok = await test_click_only()
    if not click_ok:
        print("\n⛔ Aborting — fix the click issue first.")
        return

    import asyncio
    await asyncio.sleep(3)  # Wait for Chrome to fully start

    # Phase 2: Full launch test
    launch_ok = await test_full_launch()
    if not launch_ok:
        print("\n⛔ Launch failed — check logs above.")
        return

    # Phase 3: Check for approved video
    video = await find_approved_video()
    if not video:
        print("\nℹ️  No approved video to upload. To test upload:")
        print("   1. Approve a video in the UI for dosealta_tv")
        print("   2. Re-run this script")
        return

    print(f"\n[TEST] Phase 3: Testing actual upload for video id={video.get('id')}...")
    print("  (This will trigger the full uploader_monitored.py flow)")
    try:
        async with __import__("httpx").AsyncClient(timeout=300) as client:
            resp = await client.post(
                f"http://localhost:8000/api/v1/scheduler/execute/{video.get('id')}",
            )
            print(f"  Response: {resp.status_code} — {resp.text[:200]}")
    except Exception as e:
        print(f"  ❌ Upload trigger failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
