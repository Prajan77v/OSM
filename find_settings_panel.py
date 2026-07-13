with open('frontend/src/app/page.tsx', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# Find "settings" nav condition
with open('settings_panel.txt', 'w', encoding='utf-8') as out:
    for idx, line in enumerate(lines):
        if 'settings' in line.lower() and 'activeNav' in line:
            start = max(0, idx-2)
            # Print that line and next 200 lines
            for j in range(start, min(len(lines), idx+200)):
                out.write(f'Line {j+1}: {lines[j].rstrip()}\n')
            out.write('\n---\n')
print("Done")
