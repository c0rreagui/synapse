
import json
import os

SESSION_PATH = r"d:\APPS - ANTIGRAVITY\Synapse\backend\data\sessions\tiktok_profile_1770307556827.json"

def fix_cookies():
    try:
        if not os.path.exists(SESSION_PATH):
            print(f"File not found: {SESSION_PATH}")
            return

        with open(SESSION_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        cookies = data.get("cookies", []) if isinstance(data, dict) else data
        
        fixed_count = 0
        for cookie in cookies:
            ss = cookie.get("sameSite")
            original = ss
            
            # Fix Logic
            if ss is None:
                cookie["sameSite"] = "Lax"  # Default safe
                fixed_count += 1
            elif isinstance(ss, str):
                ss_lower = ss.lower()
                if ss_lower == "no_restriction":
                    cookie["sameSite"] = "None"
                    fixed_count += 1
                elif ss_lower == "lax":
                    cookie["sameSite"] = "Lax"
                    if ss != "Lax": fixed_count += 1
                elif ss_lower == "strict":
                    cookie["sameSite"] = "Strict"
                    if ss != "Strict": fixed_count += 1
                elif ss_lower == "none":
                    cookie["sameSite"] = "None"
                    if ss != "None": fixed_count += 1
            
            # Also remove 'expirationDate' if it exists and map to 'expires' if needed by some browsers, 
            # but Playwright usually accepts expirationDate or expires. 
            # The error complained about sameSite, so focus on that.

        # Wrap back if needed
        if isinstance(data, dict):
             data["cookies"] = cookies
        else:
             data = {"cookies": cookies, "origins": []}

        with open(SESSION_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print(f"Fixed {fixed_count} cookies in {SESSION_PATH}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_cookies()
