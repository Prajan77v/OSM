import os
from pathlib import Path

root_dir = Path("C:/Users/Prajan/.gemini/antigravity/scratch/smart_surveillance")
matches = []

for root, dirs, files in os.walk(root_dir):
    for file in files:
        if file == "app.log":
            matches.append(Path(root) / file)

print("Found app.log files:")
for m in matches:
    print(f"Path: {m}, Size: {m.stat().st_size} bytes, Modified: {m.stat().st_mtime}")
