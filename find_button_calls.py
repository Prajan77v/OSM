import re

with open('frontend/src/app/page.tsx', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find all button onClick handlers and action calls
button_clicks = re.findall(r'onClick=\{[^}]*?`\$\{API\}([^`]+)`', content, re.DOTALL)
button_clicks += re.findall(r'fetch\([^)]*`\$\{API\}([^`]+)`', content, re.DOTALL)

with open('button_actions.txt', 'w', encoding='utf-8') as out:
    for call in sorted(set(button_clicks)):
        out.write(f'{call.strip()}\n')
print('Done')
