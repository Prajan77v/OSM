"""
OMS Sentinel v9.0 - One-Click Build Script
Builds the Next.js frontend, then bundles everything into a single .exe with PyInstaller.

Usage:
    py build_exe.py

Output:
    dist/OMS_Sentinel.exe  -- standalone executable (no Python required on target machine)
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Force UTF-8 output on Windows consoles so print() never crashes on special chars
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT  = Path(__file__).parent.resolve()
DIST  = ROOT / "dist"
BUILD = ROOT / "build"


def run(cmd, cwd=None, check=True):
    """Run a shell command and stream output."""
    print("\n>>> " + " ".join(str(c) for c in cmd))
    result = subprocess.run(cmd, cwd=str(cwd or ROOT), check=check, env=os.environ, shell=(os.name == 'nt'))
    return result


def ensure_dep(pkg):
    try:
        __import__(pkg.replace("-", "_"))
    except ImportError:
        print("[+] Installing " + pkg + "...")
        run([sys.executable, "-m", "pip", "install", pkg, "--break-system-packages"])


# ---------------------------------------------------------------------------
# STEP 0  -- Make sure build tools are installed
# ---------------------------------------------------------------------------
print("\n" + "=" * 62)
print("  OMS Sentinel v9.0 -- Standalone Executable Build")
print("=" * 62)

ensure_dep("pyinstaller")

# ---------------------------------------------------------------------------
# STEP 1  -- Build the Next.js frontend  (generates frontend/out/)
# ---------------------------------------------------------------------------
print("\n[STEP 1] Building Next.js frontend ...")
frontend_dir = ROOT / "frontend"
frontend_out = frontend_dir / "out"


def _find_exe(name):
    """Search PATH then known Windows install locations for an executable."""
    found = shutil.which(name)
    if found:
        return found
    candidates = [
        Path("C:/Program Files/nodejs") / name,
        Path("C:/Program Files (x86)/nodejs") / name,
        Path(os.environ.get("APPDATA", "")) / "npm" / name,
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/nodejs" / name,
    ]
    for p in candidates:
        if p.with_suffix(".cmd").exists():
            return str(p.with_suffix(".cmd"))
        if p.with_suffix(".exe").exists():
            return str(p.with_suffix(".exe"))
        if p.exists():
            return str(p)
    return name  # fallback -- let subprocess raise a clear error


npm_cmd  = _find_exe("npm")
node_exe = _find_exe("node")

# Verify node is reachable
try:
    ver = subprocess.check_output([node_exe, "--version"], text=True).strip()
    print("  Node.js : " + ver + "  (" + node_exe + ")")
except Exception:
    print("\n[ERROR] Node.js not found.")
    print("  Install from https://nodejs.org/ and re-run.")
    sys.exit(1)

# CRITICAL: inject nodejs dir into PATH so npm.cmd can call node internally
nodejs_dir = str(Path(node_exe).parent)
if nodejs_dir.lower() not in os.environ.get("PATH", "").lower():
    os.environ["PATH"] = nodejs_dir + os.pathsep + os.environ.get("PATH", "")
    print("  Injected into PATH: " + nodejs_dir)

# Install node_modules if missing
if not (frontend_dir / "node_modules").exists():
    print("  Installing node_modules ...")
    run([npm_cmd, "install"], cwd=frontend_dir)

# Build static export  (Next.js -> frontend/out/)
if frontend_out.exists():
    print("  [INFO] frontend/out/ already exists. Skipping Next.js build. Delete frontend/out/ to force rebuild.")
else:
    run([npm_cmd, "run", "build"], cwd=frontend_dir)

if not frontend_out.exists():
    print("\n[ERROR] Next.js build failed -- 'frontend/out' not found.")
    sys.exit(1)

print("  [OK] Frontend built/verified -> " + str(frontend_out))

# ---------------------------------------------------------------------------
# STEP 2  -- Install Python dependencies
# ---------------------------------------------------------------------------
print("\n[STEP 2] Installing Python dependencies ...")
run([sys.executable, "-m", "pip", "install", "-r", "requirements_build.txt", "--quiet", "--break-system-packages"])

# ---------------------------------------------------------------------------
# STEP 3  -- Clean previous build artefacts
# ---------------------------------------------------------------------------
print("\n[STEP 3] Cleaning previous build ...")
for d in [DIST, BUILD]:
    if d.exists():
        try:
            shutil.rmtree(d)
            print("  Removed " + str(d))
        except Exception as e:
            print(f"  shutil.rmtree failed on {d}: {e}")
            print("  Trying system force remove...")
            try:
                if os.name == 'nt':
                    subprocess.run(["cmd.exe", "/c", f"rd /s /q \"{d}\""], check=False)
                else:
                    shutil.rmtree(d, ignore_errors=True)
                if not d.exists():
                    print("  Successfully removed " + str(d) + " via system command.")
                else:
                    print("  [WARNING] Could not fully remove " + str(d) + ". Proceeding anyway.")
            except Exception as ex:
                print(f"  [WARNING] Force remove failed: {ex}. Proceeding anyway.")


# ---------------------------------------------------------------------------
# STEP 4  -- Run PyInstaller using the .spec file
# ---------------------------------------------------------------------------
print("\n[STEP 4] Running PyInstaller ...")
spec_file = ROOT / "OMS_Sentinel.spec"
run([
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    str(spec_file),
])

# ---------------------------------------------------------------------------
# STEP 5 -- Copy faces and objects directories to dist/ (to maintain sync with executable)
# ---------------------------------------------------------------------------
print("\n[STEP 5] Copying faces/ folder to dist/ ...")
faces_src = ROOT / "faces"
faces_dst = DIST / "faces"
if faces_src.exists():
    if faces_dst.exists():
        shutil.rmtree(faces_dst)
    shutil.copytree(faces_src, faces_dst)
    print("  [OK] Copied faces/ to " + str(faces_dst))
else:
    print("  [WARNING] 'faces/' folder not found in project root.")

print("\n[STEP 5b] Copying objects/ folder to dist/ ...")
objects_src = ROOT / "objects"
objects_dst = DIST / "objects"
if objects_src.exists():
    if objects_dst.exists():
        shutil.rmtree(objects_dst)
    shutil.copytree(objects_src, objects_dst)
    print("  [OK] Copied objects/ to " + str(objects_dst))
else:
    print("  [WARNING] 'objects/' folder not found in project root.")

print("\n[STEP 5c] Copying models/ folder to dist/ ...")
models_src = ROOT / "models"
models_dst = DIST / "models"
if models_src.exists():
    if models_dst.exists():
        shutil.rmtree(models_dst)
    shutil.copytree(models_src, models_dst)
    print("  [OK] Copied models/ to " + str(models_dst))

print("\n[STEP 5d] Copying yolov8s.pt weight to dist/ ...")
yolo_src = ROOT / "yolov8s.pt"
yolo_dst = DIST / "yolov8s.pt"
if yolo_src.exists():
    shutil.copy2(yolo_src, yolo_dst)
    print("  [OK] Copied yolov8s.pt to " + str(yolo_dst))

# ---------------------------------------------------------------------------
# STEP 6 -- Generate Portable ZIP and Standalone Installer
# ---------------------------------------------------------------------------
print("\n[STEP 6] Packaging Portable ZIP and Standalone Installer ...")

import zipfile
portable_zip_path = DIST / "OMS_Sentinel_Portable.zip"
print(f"  Creating portable archive: {portable_zip_path.name}...")
try:
    with zipfile.ZipFile(portable_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(DIST / "OMS_Sentinel.exe", "OMS_Sentinel.exe")
        if (DIST / "yolov8s.pt").exists():
            zipf.write(DIST / "yolov8s.pt", "yolov8s.pt")
        if (ROOT / "config.yaml").exists():
            zipf.write(ROOT / "config.yaml", "config.yaml")
        if (ROOT / ".env.example").exists():
            zipf.write(ROOT / ".env.example", ".env.example")
        faces_folder = ROOT / "faces"
        if faces_folder.exists():
            for file_path in faces_folder.rglob('*'):
                if file_path.is_file():
                    zipf.write(file_path, file_path.relative_to(ROOT))
        objects_folder = ROOT / "objects"
        if objects_folder.exists():
            for file_path in objects_folder.rglob('*'):
                if file_path.is_file():
                    zipf.write(file_path, file_path.relative_to(ROOT))
        models_folder = DIST / "models"
        if models_folder.exists():
            for file_path in models_folder.rglob('*'):
                if file_path.is_file():
                    zipf.write(file_path, file_path.relative_to(DIST))
    print("  [OK] Portable ZIP created.")
except Exception as e:
    print(f"  [WARNING] Failed to create portable ZIP: {e}")

print("  Compiling Installer GUI Wizard...")
try:
    run([
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--noconsole",
        "--name=OMS_Sentinel_Installer",
        "--add-data=main.py;.",
        "--add-data=haae_engine.py;.",
        "--add-data=web_server.py;.",
        "--add-data=web_integration.py;.",
        "--add-data=requirements.txt;.",
        "--add-data=faces;faces",
        "--add-data=objects;objects",
        "--add-data=models;models",
        "--add-data=yolov8s.pt;.",
        "--add-data=config.yaml;.",
        "--add-data=frontend/out;frontend/out",
        "create_installer.py"
    ])
    print("  [OK] Standalone Installer compiled.")
except Exception as e:
    print(f"  [ERROR] Failed to compile Standalone Installer: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# DONE
# ---------------------------------------------------------------------------
exe_path = DIST / "OMS_Sentinel.exe"
installer_path = DIST / "OMS_Sentinel_Installer.exe"
if exe_path.exists():
    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print("\n" + "=" * 62)
    print("  BUILD SUCCESSFUL!")
    print("  Executable        : " + str(exe_path))
    print("  Portable ZIP      : " + str(portable_zip_path))
    if installer_path.exists():
        print("  Windows Installer : " + str(installer_path))
    print("  Size              : " + f"{size_mb:.1f}" + " MB")
    print("=" * 62)
    print("\nHOW TO DEPLOY:")
    print("  1. Run  dist/OMS_Sentinel_Installer.exe  to install via GUI wizard.")
    print("  2. Or extract  dist/OMS_Sentinel_Portable.zip  for portable deployment.")
else:
    print("\n[ERROR] Build failed -- dist/OMS_Sentinel.exe not found.")
    sys.exit(1)
