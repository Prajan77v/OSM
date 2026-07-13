import re

with open('web_server.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# Look for the /api/control/{action} handler - find main dispatch block
with open('control_dispatch.txt', 'w', encoding='utf-8') as out:
    in_section = False
    for idx, line in enumerate(lines):
        if '/api/control' in line or 'action_executed' in line or 'nav_' in line or 'toggle_' in line or 'shutdown' in line.lower() or 'restart' in line.lower():
            out.write(f'Line {idx+1}: {line.rstrip()}\n')
print('Done')
