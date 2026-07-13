import re

with open('web_server.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find what handlers are registered in _control_handlers
handler_registrations = re.findall(r'_control_handlers\[[\'"](.*?)[\'"]\]', content)
with open('registered_handlers.txt', 'w', encoding='utf-8') as out:
    for h in sorted(set(handler_registrations)):
        out.write(f'{h}\n')
print('Done')
