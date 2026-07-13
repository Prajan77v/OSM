with open('frontend/src/app/page.tsx', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# Find the detection view section
with open('detection_section.txt', 'w', encoding='utf-8') as out:
    for idx, line in enumerate(lines):
        # Write lines around "detection" view checks
        if 'activeView' in line and 'detection' in line:
            out.write(f'Line {idx+1}: {line.rstrip()}\n')

print("Done - found detection view lines")
