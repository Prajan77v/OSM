with open("surveillance.py", "r", encoding="utf-8") as f:
    content = f.read()

import re
matches = list(re.finditer(r"def _draw_hud_glass_overlay\b", content))
for m in matches:
    line_no = content[:m.start()].count("\n") + 1
    line = content[m.start():].splitlines()[0]
    print(f"Line {line_no}: {line}")
