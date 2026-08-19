"""
OMS Sentinel - Portable Package Builder
Builds the standalone executable and creates dist/OMS_Sentinel_Portable.zip.
"""
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
DIST = ROOT / "dist"
BUILD = ROOT / "build"

print("=" * 65)
print("  OMS SENTINEL - PACKAGING PORTABLE RELEASE BUNDLE")
print("=" * 65)

# Step 1: Ensure frontend static export is ready
frontend_out = ROOT / "frontend" / "out"
if not frontend_out.exists():
    print("[1/4] Building Next.js static frontend...")
    subprocess.run(["npm", "run", "build"], cwd=str(ROOT / "frontend"), shell=True, check=True)
else:
    print("[1/4] Frontend build verified -> frontend/out/")

# Step 2: Run PyInstaller
print("\n[2/4] Compiling standalone OMS_Sentinel.exe via PyInstaller...")
spec_file = ROOT / "OMS_Sentinel.spec"
res = subprocess.run([
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    str(spec_file)
], cwd=str(ROOT))

exe_path = DIST / "OMS_Sentinel.exe"
if not exe_path.exists():
    print(f"\n[ERROR] PyInstaller failed to produce {exe_path}")
    sys.exit(1)

print(f"[OK] Standalone Executable built: {exe_path} ({exe_path.stat().st_size / (1024*1024):.1f} MB)")

# Step 3: Copy assets into dist/
print("\n[3/4] Copying required assets to dist/ ...")
for item in ["yolov8n.pt", "yolov8s.pt", "alarm.wav", "config.yaml", ".env.example", "start_oms_ai.bat", "start_oms_cloud.bat"]:
    src = ROOT / item
    if src.exists():
        shutil.copy2(src, DIST / item)
        print(f"  + Copied {item}")

for folder in ["faces", "objects", "models"]:
    src = ROOT / folder
    dst = DIST / folder
    if src.exists():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"  + Copied {folder}/ folder")

# Step 4: Create Portable ZIP
print("\n[4/4] Generating dist/OMS_Sentinel_Portable.zip ...")
zip_path = DIST / "OMS_Sentinel_Portable.zip"
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    zipf.write(exe_path, "OMS_Sentinel.exe")
    for item in ["yolov8n.pt", "yolov8s.pt", "alarm.wav", "config.yaml", ".env.example", "start_oms_ai.bat", "start_oms_cloud.bat"]:
        f_path = DIST / item
        if f_path.exists():
            zipf.write(f_path, item)
    
    for folder in ["faces", "objects", "models"]:
        f_dir = DIST / folder
        if f_dir.exists():
            for p in f_dir.rglob('*'):
                if p.is_file():
                    zipf.write(p, p.relative_to(DIST))

size_mb = zip_path.stat().st_size / (1024 * 1024)
print("\n" + "=" * 65)
print("  PORTABLE BUNDLE CREATED SUCCESSFULLY!")
print(f"  ZIP Path : {zip_path}")
print(f"  ZIP Size : {size_mb:.1f} MB")
print("=" * 65)
