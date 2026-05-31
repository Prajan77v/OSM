import os
import cv2
import sys
from pathlib import Path
from collections import Counter
import logging

logging.basicConfig(level=logging.INFO)
import surveillance

def log_print(msg):
    print(msg, flush=True)

log_print("\n=== DIAGNOSTICS ===")
log_print(f"YUNET_AVAILABLE: {surveillance.YUNET_AVAILABLE}")

# Test encoding Prajan.jpg
p = Path(surveillance.Config.KNOWN_FACES_DIR) / "Prajan.jpg"
if p.exists():
    img = cv2.imread(str(p))
    if img is not None:
        enc = surveillance._yunet_encode(img)
        log_print(f"Prajan.jpg shape: {img.shape}")
        log_print(f"YuNet encoding success: {enc is not None}")
        if enc is not None:
            log_print(f"Encoding size: {enc.shape}")
    else:
        log_print("Failed to read Prajan.jpg")
else:
    log_print("Prajan.jpg does not exist in known faces dir!")

surveillance.preload_known()
log_print("=== YUNET CACHE ===")
log_print(str(list(surveillance._yunet_enc_cache.keys())))
log_print("=== FACES DB ===")
for pid, data in surveillance.faces_db.items():
    log_print(f"{pid} {data.get('name')} known: {data.get('known')}")
