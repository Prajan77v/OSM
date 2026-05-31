import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

with open("surveillance.py", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if re.search(r'\b(cuda|CUDA)\b', line):
            print(f"{i}: {line.strip()}")
