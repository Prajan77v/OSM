import re

with open('surveillance.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all ◆ characters and their surrounding context
diamond = '\u25c6'
count = content.count(diamond)
print(f'Found {count} diamond chars')

# Replace all diamonds in the content with >>>
# The ticker is passed to _text() which uses PIL, so plain ASCII is fine
content = content.replace(diamond, '>>>')

# Also fix any remaining strftime that had diamonds (now replaced)
# The remaining issue is the strftime call - let's build ticker without strftime
# Find the footer function and fix the strftime concatenation
old_strf = '+ datetime.now().strftime("%Y-%m-%d %H:%M:%S  >>>  ")'
new_strf = '+ datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "  >>>  "'

if old_strf in content:
    content = content.replace(old_strf, new_strf)
    print('Fixed strftime concatenation')
else:
    print('strftime concatenation already fixed or not found')

with open('surveillance.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done - all diamond chars replaced with >>>')
