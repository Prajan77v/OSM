import os

with open("surveillance.py", "r", encoding="utf-8") as f:
    content = f.read()

# Locate the start of the duplicate block
duplicate_start_marker = '                _text(img, "LOITER DETECTOR: ONLINE", tg_x, tg_y + 80, 0.24, C_TEXT)'
duplicate_end_marker = '# ── CENTER-BOTTOM INFO ROW ─────────────────────────────────────────────────────'

start_idx = content.find(duplicate_start_marker)
end_idx = content.find(duplicate_end_marker)

if start_idx != -1 and end_idx != -1:
    print(f"Found markers! Start index: {start_idx}, End index: {end_idx}")
    new_content = content[:start_idx] + "    return info_area_y\n\n" + content[end_idx:]
    with open("surveillance.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Cleaned up successfully!")
else:
    print("Markers not found!")
    if start_idx == -1:
        print("Start marker not found.")
    if end_idx == -1:
        print("End marker not found.")
