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
    result = subprocess.run(cmd, cwd=str(cwd or ROOT), check=check, env=os.environ)
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
run([npm_cmd, "run", "build"], cwd=frontend_dir)

if not frontend_out.exists():
    print("\n[ERROR] Next.js build failed -- 'frontend/out' not found.")
    sys.exit(1)

print("  [OK] Frontend built -> " + str(frontend_out))

# ---------------------------------------------------------------------------
# STEP 2  -- Install Python dependencies
# ---------------------------------------------------------------------------
print("\n[STEP 2] Installing Python dependencies ...")
run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet", "--break-system-packages"])

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
# STEP 5 -- Copy faces directory to dist/ (to maintain sync with executable)
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

# ---------------------------------------------------------------------------
# DONE
# ---------------------------------------------------------------------------
exe_path = DIST / "OMS_Sentinel.exe"
if exe_path.exists():
    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print("\n" + "=" * 62)
    print("  BUILD SUCCESSFUL!")
    print("  Executable : " + str(exe_path))
    print("  Size       : " + f"{size_mb:.1f}" + " MB")
    print("=" * 62)
    print("\nHOW TO DEPLOY:")
    print("  1. Copy  dist/OMS_Sentinel.exe  to any Windows PC.")
    print("  2. Place your  config.yaml  and  .env  beside the exe.")
    print("  3. Double-click OMS_Sentinel.exe  (no Python / Node needed).")
    print("  4. Web dashboard opens automatically at http://localhost:8000")
else:
    print("\n[ERROR] Build failed -- dist/OMS_Sentinel.exe not found.")
    sys.exit(1)
