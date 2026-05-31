with open("surveillance.py", "r", encoding="utf-8") as f:
    content = f.read()

import re
funcs = ["_panel", "_text"]
for func in funcs:
    matches = list(re.finditer(rf"def\s+{func}\b", content))
    for m in matches:
        line_no = content[:m.start()].count("\n") + 1
        line = content[m.start():].splitlines()[0]
        print(f"Line {line_no}: {line}")
