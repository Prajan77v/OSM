with open("surveillance.py", "r", encoding="utf-8") as f:
    content = f.read()

import re
matches = list(re.finditer(r"\b_panel\b", content))
print(f"Total calls to _panel: {len(matches)}")
for m in matches:
    line_no = content[:m.start()].count("\n") + 1
    line = content[m.start():].splitlines()[0]
    print(f"  Line {line_no}: {line}")
