
path = r"d:\APPS - ANTIGRAVITY\Synapse\backend\core\scheduler.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

start = 537
end = 545
print(f"Printing lines {start}-{end}:")
for i in range(start, end):
    if i < len(lines):
        print(f"{i+1}: {repr(lines[i])}")
