with open("surveillance.py.bak", "r", encoding="utf-8") as f:
    content = f.read()

import re
matches = list(re.finditer(r"def\s+\w*(?:crop|aspect)\w*\b", content, re.IGNORECASE))
print(f"Total matching functions: {len(matches)}")
for m in matches:
    print(m.group(0))
