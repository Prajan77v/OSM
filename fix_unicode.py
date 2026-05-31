import re, sys

with open('surveillance.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check all unicode special chars that can fail on Windows locale codec
# These are the ones that fail: ◆ (\u25c6), and anything in strftime() calls
problematic = []
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'strftime' in line:
        for c in line:
            if ord(c) > 127:
                problematic.append((i+1, repr(c), line.strip()[:80]))
                break

print(f'Lines with non-ASCII in strftime: {len(problematic)}')
for ln, ch, txt in problematic:
    print(f'  Line {ln}: char={ch} -> {txt}')

# Fix all occurrences: replace diamond in footer ticker
# diamond char: \u25c6
diamond = '\u25c6'
n = content.count(diamond)
print(f'\nTotal diamond chars: {n}')

# Replace all diamonds with ASCII " // "
content = content.replace(diamond, ' // ')

# Now the strftime issue: rebuild the footer ticker concat differently
# Old pattern: ... + datetime.now().strftime("%Y-%m-%d %H:%M:%S  //  ")
# New: replace to not have special chars in strftime at all
old = 'datetime.now().strftime("%Y-%m-%d %H:%M:%S  //  ")'
new = 'datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "  //  "'
if old in content:
    content = content.replace(old, new)
    print('Fixed strftime concatenation')

with open('surveillance.py', 'w', encoding='utf-8') as f:
    f.write(content)

# Verify
with open('surveillance.py', 'r', encoding='utf-8') as f:
    final = f.read()

remaining = sum(1 for c in final if ord(c) > 127 and 'strftime' in final[max(0, final.index(c)-200):final.index(c)+200])
print(f'Remaining non-ASCII near strftime: {remaining}')

# Quick syntax check
import ast
try:
    ast.parse(final)
    print('SYNTAX OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR line {e.lineno}: {e.msg}')
