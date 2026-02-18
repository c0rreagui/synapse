
path = r"d:\APPS - ANTIGRAVITY\Synapse\backend\core\scheduler.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

found = False
for i, line in enumerate(lines):
    if "Zombie" in line:
        print(f"Line {i+1}: {repr(line)}")
        found = True

if not found:
    print("Zero Zombies found in file.")
