import os
import subprocess
import sys
from pathlib import Path

def ensure_pyinstaller():
    try:
        import PyInstaller
        print("[+] PyInstaller is installed.")
    except ImportError:
        print("[!] PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[+] PyInstaller installed successfully.")

def run_build():
    print("==================================================")
    print("  OMS_Sentinel Standalone Build Script (PyInstaller)  ")
    print("==================================================")
    ensure_pyinstaller()

    # Define paths
    workspace = Path(__file__).parent.resolve()
    main_script = workspace / "main.py"
    
    # We will build using PyInstaller CLI directly via subprocess
    # so we don't need to manually construct the complex .spec file.
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name", "OMS_Sentinel",
        "--add-data", f"frontend/out{os.pathsep}frontend/out",
        "--add-data", f"models{os.pathsep}models",
    ]
    
    # Add optional top-level files if they exist
    for f in ["alarm.wav", "yolov8n.pt", "yolov8s.pt"]:
        p = workspace / f
        if p.exists():
            cmd.extend(["--add-data", f"{f}{os.pathsep}."])
            
    cmd.append(str(main_script))
    
    print("\n[+] Running PyInstaller with command:")
    print(" ".join(cmd))
    
    subprocess.check_call(cmd, cwd=str(workspace))
    
    print("\n==================================================")
    print("  Build Complete!                               ")
    print("  Executable is located in: dist/OMS_Sentinel   ")
    print("==================================================")

if __name__ == "__main__":
    run_build()
