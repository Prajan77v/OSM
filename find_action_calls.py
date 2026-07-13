import re

with open('frontend/src/app/page.tsx', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# Look for all places where action is used in control endpoint
with open('action_calls.txt', 'w', encoding='utf-8') as out:
    for idx, line in enumerate(lines):
        if '/api/control/' in line and '${action}' not in line:
            out.write(f'Line {idx+1}: {line.strip()}\n')
        # Also find where action variable is set
        if 'setAction' in line or '"alarm"' in line.lower() or '"shutdown"' in line.lower() or '"export"' in line.lower() or '"alarm"' in line:
            out.write(f'Line {idx+1}: {line.strip()}\n')
        # Find control action button definitions
        if '/api/control/alarm' in line or '/api/control/shutdown' in line or '/api/control/export' in line or '/api/control/refresh' in line or '/api/control/reset' in line or '/api/control/hud' in line or '/api/control/telegram' in line:
            out.write(f'Line {idx+1}: {line.strip()}\n')
print("Done")
