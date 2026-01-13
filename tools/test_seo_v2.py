import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(name, method, url, payload=None):
    print(f"Testing {name}...", end=" ")
    try:
        if method == "POST":
            res = requests.post(url, json=payload)
        else:
            res = requests.get(url)
        
        if res.status_code == 200:
            print("âœ… OK")
            return res.json()
        else:
            print(f"âŒ FAIL ({res.status_code})")
            print(res.text)
            return None
    except Exception as e:
        print(f"âŒ ERROR: {e}")
        return None

def main():
    print("--- SEO V2 API TEST ---")
    
    # 1. Test Audit (using tiktok_profile_01)
    audit = test_endpoint("My Audit", "POST", f"{BASE_URL}/oracle/seo/audit/tiktok_profile_01")
    if audit:
        print(f"   Score: {audit.get('total_score')}")
        print(f"   Vision: {audit.get('vision_score')}")

    # 2. Test Spy
    spy = test_endpoint("Competitor Spy", "POST", f"{BASE_URL}/oracle/seo/spy", {"competitor_handle": "@test_rival"})
    if spy:
        print(f"   Weakness: {spy.get('analysis', {}).get('weakness_exposed')}")

    # 3. Test Fix Bio
    bio = test_endpoint("Fix Bio", "POST", f"{BASE_URL}/oracle/seo/fix-bio", {"current_bio": "Just a test bio", "niche": "Testing"})
    if bio:
        print(f"   Options: {len(bio.get('options', []))}")

    # 4. Test Hashtags
    tags = test_endpoint("Hashtags", "POST", f"{BASE_URL}/oracle/seo/hashtags", {"niche": "Tech", "topic": "AI"})
    if tags:
        print(f"   Broad: {tags.get('broad')}")

if __name__ == "__main__":
    main()
