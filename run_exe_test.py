import subprocess
import time
import os

print("Running OMS_Sentinel.exe to capture console errors...")
try:
    p = subprocess.Popen(["dist/OMS_Sentinel.exe"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # Wait for 3 seconds to let it boot and print errors
    time.sleep(4)
    p.terminate()
    stdout, stderr = p.communicate()
    
    print("\n--- STDOUT ---")
    print(stdout[:1000])
    print("\n--- STDERR ---")
    print(stderr[:1000])
    
    with open("exe_error_capture.txt", "w", encoding="utf-8") as f:
        f.write("=== STDOUT ===\n")
        f.write(stdout)
        f.write("\n=== STDERR ===\n")
        f.write(stderr)
except Exception as e:
    print(f"Error running process: {e}")
