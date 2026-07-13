import re

with open('frontend/src/app/page.tsx', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find all fetch calls in the frontend
fetch_calls = re.findall(r'fetch\([^)]*`\$\{API\}([^`"\']+)', content)
fetch_calls += re.findall(r'fetch\([^)]*"[^"]*(/api/[^"]+)"', content)
fetch_calls += re.findall(r'fetch\([^)]*\'[^\']*(/api/[^\']+)\'', content)

with open('frontend_fetches.txt', 'w', encoding='utf-8') as out:
    for call in sorted(set(fetch_calls)):
        out.write(f'{call}\n')
print('Done')
