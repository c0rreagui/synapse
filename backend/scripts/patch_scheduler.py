
import os

path = r"d:\APPS - ANTIGRAVITY\Synapse\backend\core\scheduler.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

target = 'zombie.error_message = "Zombie Recovery: Pipeline stuck for >1h"'
replacement = 'zombie.error_message = "ZOMBIE HOST DETECTED: Pipeline stuck for >1h"'

if target not in content:
    print(f"Error: Target string not found in {path}")
else:
    new_content = content.replace(target, replacement)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Successfully patched scheduler.py")
