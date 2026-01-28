import os
import glob

def find_non_ascii(directory):
    print(f"Scanning {directory}...")
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            if not line.isascii():
                                print(f"{path}:{i+1}: {line.strip()}")
                except Exception as e:
                    print(f"Skipping {path}: {e}")

if __name__ == "__main__":
    find_non_ascii("backend/core")
    find_non_ascii("backend/scripts")
