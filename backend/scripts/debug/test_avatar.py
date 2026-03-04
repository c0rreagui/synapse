import requests
from fake_useragent import UserAgent
import json

cookies_json = '''[
  {"domain": ".tiktok.com", "name": "sessionid", "value": "d278273e2131c1e7f108d3f91a16c1b3"},
  {"domain": ".tiktok.com", "name": "sessionid_ss", "value": "d278273e2131c1e7f108d3f91a16c1b3"},
  {"domain": ".tiktok.com", "name": "sid_tt", "value": "d278273e2131c1e7f108d3f91a16c1b3"},
  {"domain": ".tiktok.com", "name": "uid_tt", "value": "4d290c7b24eed8dec0c92c24fa6665b8132618728fe3da4f892f099fab568686"},
  {"domain": ".tiktok.com", "name": "passport_csrf_token", "value": "235e95926a8429254b92fe63ce8cca3f"},
  {"domain": ".tiktok.com", "name": "ttwid", "value": "1%7CsSOKjApc9Gb0hlQxTey7UiOWHFX5-V7OgNBIagPCqmw%7C1770134587%7C7f405d9ca50f5890c431d5202cec4c2693f31cbc66a9b7a2268a742b805ce02c"}
]'''

cookies_list = json.loads(cookies_json)

s = requests.Session()
ua = UserAgent()
headers = {
    "User-Agent": ua.random,
    "Referer": "https://www.tiktok.com/",
    "Origin": "https://www.tiktok.com"
}

for c in cookies_list:
    s.cookies.set(c["name"], c["value"], domain=c.get("domain", ".tiktok.com"))

url = "https://www.tiktok.com/passport/web/account/info/"
response = s.get(url, headers=headers, timeout=15)

print(f"Status: {response.status_code}")
data = response.json()
print(f"Passport Response: {json.dumps(data, indent=2)}")

# Now test public API
username = data.get("data", {}).get("username")
if username:
    print(f"\n--- Testing Public API for @{username} ---")
    public_url = f"https://www.tiktok.com/api/user/detail/?uniqueId={username}&secUid="
    pub_response = s.get(public_url, headers=headers, timeout=10)
    print(f"Public Status: {pub_response.status_code}")
    print(f"Public Raw (first 500 chars): {pub_response.text[:500]}")
    if pub_response.status_code == 200 and pub_response.text.strip().startswith("{"):
        pub_data = pub_response.json()
        user_info = pub_data.get("userInfo", {}).get("user", {})
        print(f"Public Avatar Large: {user_info.get('avatarLarger')}")
        print(f"Public Avatar Medium: {user_info.get('avatarMedium')}")
    else:
        print(f"Public Error or HTML returned")
