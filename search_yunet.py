with open("main.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

with open("yunet_search.txt", "w", encoding="utf-8") as out:
    for idx, line in enumerate(lines):
        if "_yunet_detector" in line or "FaceDetectorYN" in line:
            out.write(f"Line {idx+1}: {line.strip()}\n")
print("Search complete. Results written to yunet_search.txt")
