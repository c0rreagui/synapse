"""
Dolphin{anty} Setup Script
--------------------------
Run inside the backend container:
    docker exec -it synapse-backend python /app/scripts/dolphin_setup.py

Does:
1. Runs the dolphin_profile_name migration
2. Lists all Dolphin profiles and their cookie state
3. Connects to Dolphin Electron UI and takes a screenshot for DOM inspection
4. Tries to auto-detect which Dolphin profile has TikTok cookies for dosealta_tv
5. Saves inspection artifacts to /app/downloads/
"""
import os
import sys
import glob
import json
import asyncio
import socket

sys.path.insert(0, "/app")

# ── 1. Run migration ──────────────────────────────────────────────────────────
def run_migration():
    import psycopg2
    conn_str = (
        f"host={os.getenv('POSTGRES_SERVER','db')} "
        f"dbname={os.getenv('POSTGRES_DB','synapse')} "
        f"user={os.getenv('POSTGRES_USER','postgres')} "
        f"password={os.getenv('POSTGRES_PASSWORD','')}"
    )
    try:
        conn = psycopg2.connect(conn_str)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS dolphin_profile_name VARCHAR;")
        conn.close()
        print("[MIGRATION] ✅ dolphin_profile_name column added (or already exists)")
    except Exception as e:
        print(f"[MIGRATION] ❌ Error: {e}")


# ── 2. List Dolphin profiles from filesystem ──────────────────────────────────
def list_dolphin_profiles():
    dolphin_dir = "/root/.config/dolphin_anty/browser_profiles"
    print(f"\n[PROFILES] Scanning {dolphin_dir}")
    results = []
    for prefs_path in glob.glob(f"{dolphin_dir}/**/Preferences", recursive=True):
        profile_id = os.path.basename(os.path.dirname(os.path.dirname(prefs_path)))
        cookies_db = os.path.join(os.path.dirname(prefs_path), "Cookies")
        has_cookies = os.path.exists(cookies_db)
        has_tiktok = False
        if has_cookies:
            try:
                import sqlite3, shutil, tempfile
                tmp = tempfile.mktemp(suffix=".db")
                shutil.copy2(cookies_db, tmp)
                conn = sqlite3.connect(f"file:{tmp}?mode=ro&immutable=1", uri=True)
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM cookies WHERE host_key LIKE '%tiktok.com%'")
                count = cur.fetchone()[0]
                conn.close()
                os.unlink(tmp)
                has_tiktok = count > 0
            except Exception as e:
                print(f"  [WARN] Could not read cookies for {profile_id}: {e}")
        results.append({
            "id": profile_id,
            "prefs": prefs_path,
            "has_cookies": has_cookies,
            "has_tiktok_cookies": has_tiktok,
        })
        marker = "🍪 TikTok cookies" if has_tiktok else ("📁 cookies DB" if has_cookies else "⬜ no cookies")
        print(f"  Profile dir: {profile_id}  {marker}")
    return results


# ── 3. Electron DOM inspection ────────────────────────────────────────────────
async def inspect_dolphin_ui():
    ELECTRON_PORT = 9222
    os.makedirs("/app/downloads", exist_ok=True)

    # Check if port is open
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    if s.connect_ex(("127.0.0.1", ELECTRON_PORT)) != 0:
        s.close()
        print(f"\n[ELECTRON] Port {ELECTRON_PORT} not responding — Dolphin not running or missing --remote-debugging-port flag.")
        print("  → Start a VNC session first (factory or profile), then re-run this script.")
        return None
    s.close()

    print(f"\n[ELECTRON] Port {ELECTRON_PORT} open. Connecting via CDP...")

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("[ELECTRON] playwright not available")
        return None

    results = {}
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(f"http://localhost:{ELECTRON_PORT}")
        print(f"  Contexts: {len(browser.contexts)}")
        for i, ctx in enumerate(browser.contexts):
            print(f"  Context {i}: {len(ctx.pages)} pages")
            for j, page in enumerate(ctx.pages):
                url = page.url or ""
                title = ""
                try:
                    title = await page.title()
                except Exception:
                    pass
                print(f"    Page {j}: url={url!r}  title={title!r}")

                # Skip devtools and extensions
                if "devtools" in url or "chrome-extension" in url or url in ("", "about:blank"):
                    continue

                # This is likely the Dolphin UI
                try:
                    await page.screenshot(
                        path=f"/app/downloads/dolphin_ui_{i}_{j}.png",
                        full_page=True
                    )
                    print(f"    → Screenshot: /app/downloads/dolphin_ui_{i}_{j}.png")
                except Exception as e:
                    print(f"    → Screenshot failed: {e}")

                try:
                    html = await page.evaluate("document.body.outerHTML")
                    out_path = f"/app/downloads/dolphin_html_{i}_{j}.txt"
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(html[:30000])
                    print(f"    → HTML (30k chars): {out_path}")
                    results["html"] = html
                    results["page_url"] = url
                    results["page_title"] = title
                except Exception as e:
                    print(f"    → HTML dump failed: {e}")

                # Try to find profile names in the DOM
                try:
                    profile_texts = await page.evaluate("""
                        () => {
                            const els = document.querySelectorAll('[class*="profile"], [class*="Profile"], [class*="browser"], [data-testid]');
                            return Array.from(els).slice(0, 20).map(el => ({
                                tag: el.tagName,
                                cls: el.className,
                                text: el.innerText?.substring(0, 100),
                                testid: el.dataset?.testid,
                            }));
                        }
                    """)
                    out_path = "/app/downloads/dolphin_profile_elements.json"
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump(profile_texts, f, indent=2, ensure_ascii=False)
                    print(f"    → Profile elements: {out_path}")
                    results["profile_elements"] = profile_texts
                except Exception as e:
                    print(f"    → Profile elements failed: {e}")

        await browser.close()
    return results


# ── 4. Auto-set dolphin_profile_name if single TikTok profile found ───────────
def try_auto_configure(profiles_with_tiktok: list, target_slug: str = "dosealta_tv"):
    if not profiles_with_tiktok:
        print(f"\n[AUTO-CONFIG] No TikTok profiles found in Dolphin filesystem.")
        return

    if len(profiles_with_tiktok) == 1:
        profile = profiles_with_tiktok[0]
        print(f"\n[AUTO-CONFIG] Single TikTok profile found: {profile['id']}")
        print(f"  We cannot read the display name from the filesystem alone.")
        print(f"  → After inspecting the Dolphin UI screenshot, run:")
        print(f"    curl -X PUT http://localhost:8000/api/v1/profiles/{target_slug}/dolphin-name \\")
        print(f"         -H 'Content-Type: application/json' \\")
        print(f"         -d '{{\"dolphin_profile_name\": \"NAME_AS_SHOWN_IN_DOLPHIN\"}}'")
    else:
        print(f"\n[AUTO-CONFIG] Multiple TikTok profiles found:")
        for p in profiles_with_tiktok:
            print(f"  - {p['id']}")
        print(f"  → Check the screenshot to identify which belongs to '{target_slug}'")
        print(f"  → Then run the curl command above with the correct name.")


# ── 5. Check current DB state ─────────────────────────────────────────────────
def check_db_state(target_slug: str = "dosealta_tv"):
    try:
        import psycopg2
        conn_str = (
            f"host={os.getenv('POSTGRES_SERVER','db')} "
            f"dbname={os.getenv('POSTGRES_DB','synapse')} "
            f"user={os.getenv('POSTGRES_USER','postgres')} "
            f"password={os.getenv('POSTGRES_PASSWORD','')}"
        )
        conn = psycopg2.connect(conn_str)
        cur = conn.cursor()
        cur.execute(
            "SELECT slug, label, username, dolphin_profile_name FROM profiles WHERE slug = %s OR username ILIKE %s",
            (target_slug, f"%dose%")
        )
        rows = cur.fetchall()
        conn.close()
        print(f"\n[DB] Profiles matching '{target_slug}':")
        for row in rows:
            slug, label, username, dolphin_name = row
            status = f"✅ dolphin_profile_name='{dolphin_name}'" if dolphin_name else "❌ dolphin_profile_name NOT SET"
            print(f"  slug={slug!r}  label={label!r}  username={username!r}  {status}")
        return rows
    except Exception as e:
        print(f"[DB] Error: {e}")
        return []


# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    print("=" * 60)
    print("Dolphin{anty} Setup & Inspection Script")
    print("=" * 60)

    run_migration()
    profiles = list_dolphin_profiles()
    tiktok_profiles = [p for p in profiles if p["has_tiktok_cookies"]]
    db_rows = check_db_state()
    await inspect_dolphin_ui()
    try_auto_configure(tiktok_profiles)

    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("1. Open /app/downloads/dolphin_ui_*.png in the VNC file picker to see the Dolphin UI")
    print("2. Find the profile name for dosealta_tv in the screenshot")
    print("3. Set it via:")
    print("   curl -X PUT http://localhost:8000/api/v1/profiles/dosealta_tv/dolphin-name \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"dolphin_profile_name\": \"NOME_AQUI\"}'")
    print("4. Then test: USE_DOLPHIN_UPLOADS=true python scripts/test_dolphin_upload.py")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
