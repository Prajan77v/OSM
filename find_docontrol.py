with open('frontend/src/app/page.tsx', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# Find doControl definition
with open('docontrol_def.txt', 'w', encoding='utf-8') as out:
    for idx, line in enumerate(lines):
        if 'doControl' in line or 'const doControl' in line:
            out.write(f'Line {idx+1}: {line.strip()}\n')
print("Done")
