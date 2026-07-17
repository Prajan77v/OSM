import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Prajan\OMS_Sentinel\main.py', 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f, 1):
        if 3460 <= i <= 3540:
            sys.stdout.write(f"{i}: {line}")
