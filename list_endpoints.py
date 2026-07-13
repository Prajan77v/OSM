import re

with open('web_server.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

endpoints = re.findall(r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', content)
with open('api_endpoints.txt', 'w', encoding='utf-8') as out:
    for method, path in sorted(set(endpoints), key=lambda x: x[1]):
        out.write(f'{method.upper():6} {path}\n')
print('Done')
