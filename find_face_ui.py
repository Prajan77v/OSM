with open('frontend/src/app/page.tsx', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

with open('face_detection_ui.txt', 'w', encoding='utf-8') as out:
    for idx, line in enumerate(lines):
        if any(w in line for w in ['yunet', 'face_recog', 'YUNET', 'faceRecog', 'face recognition', 'Face Recognition', 'FACE_RECOG', 'YUNET_AVAILABLE', 'face_engine']):
            out.write(f'Line {idx+1}: {line.rstrip()}\n')
print('Done')
