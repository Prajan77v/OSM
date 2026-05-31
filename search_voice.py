import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

with open("surveillance.py", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if re.search(r'voice|speak|mic|audio|speech|recogni', line, re.IGNORECASE):
            print(f"{i}: {line.strip()}")
