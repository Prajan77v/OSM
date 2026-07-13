import re

with open('web_server.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find all actions handled under /api/control/{action}
action_handlers = re.findall(r'"([a-z_]+)".*?:.*?(?:lambda|def|await)', content)
# Simpler: find case/elif blocks for action handling
if_actions = re.findall(r'action\s*==\s*["\']([a-z_]+)["\']', content)
elif_actions = re.findall(r'elif\s+action\s*==\s*["\']([a-z_]+)["\']', content)
all_actions = sorted(set(if_actions + elif_actions))

with open('control_actions.txt', 'w', encoding='utf-8') as out:
    for a in all_actions:
        out.write(f'{a}\n')
print('Done')
