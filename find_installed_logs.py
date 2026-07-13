import os
from pathlib import Path

# Search directories
search_dirs = [
    Path("C:/Program Files"),
    Path("C:/Program Files (x86)"),
    Path(os.environ.get("APPDATA", "C:/")),
    Path(os.environ.get("LOCALAPPDATA", "C:/")),
]

found = []
for sd in search_dirs:
    if not sd.exists(): continue
    print(f"Searching {sd}...")
    try:
        # Just scan top levels or search for "OMS"
        for root, dirs, files in os.walk(sd):
            # Prune directories to speed up
            dirs[:] = [d for d in dirs if any(w in d.lower() for w in ["oms", "sentinel", "smart", "surveillance", "prajan"])]
            for file in files:
                if file == "app.log" or file == "yolo_import_error.txt":
                    found.append(Path(root) / file)
    except Exception as e:
        print(f"Error searching {sd}: {e}")

print("\nFound logs:")
for f in found:
    try:
        print(f"{f} (Size: {f.stat().st_size}, Modified: {f.stat().st_mtime})")
    except Exception:
        print(f)
