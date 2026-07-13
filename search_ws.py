with open('web_server.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

with open('ws_search.txt', 'w', encoding='utf-8') as out:
    for idx, line in enumerate(lines):
        if any(w in line for w in ['save_config', 'save_settings', 'detect_new', 'detect_people', 'detect_objects', 'particle', 'mesh', 'match_threshold', 'profile', 'hwProfile', 'confThresh']):
            out.write(f'Line {idx+1}: {line.rstrip()}\n')
print('Done')
