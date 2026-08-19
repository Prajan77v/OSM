"""
OMS Sentinel - Ultra-Fast Instant Windows Installer (OMS_Installer.exe)
Extracts the pre-compiled standalone engine & web dashboard in seconds,
creates desktop/start-menu shortcuts, and launches the web interface.
"""
import os
import sys
import shutil
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

BG_COLOR = "#0A0C10"
CARD_BG = "#131720"
GOLD_ACCENT = "#D4AF37"
TEXT_COLOR = "#FFFFFF"
TEXT_MUTED = "#8E9AA8"

class FastOMSInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title("OMS Sentinel — System Setup Wizard")
        self.root.geometry("560x400")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TProgressbar", thickness=10, troughcolor=CARD_BG, background=GOLD_ACCENT)

        # Default install path: C:\OMS_Sentinel or C:\Program Files\OMS_Sentinel
        default_dir = Path("C:/OMS_Sentinel")
        self.install_dir = tk.StringVar(value=str(default_dir))
        self.create_desktop = tk.BooleanVar(value=True)
        self.launch_after = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg=CARD_BG, height=65)
        hdr.pack(fill=tk.X, side=tk.TOP)
        hdr.pack_propagate(False)

        tk.Label(
            hdr,
            text="⚡ OMS SENTINEL v9.0 — DEPLOYMENT WIZARD",
            font=("Segoe UI", 11, "bold"),
            fg=GOLD_ACCENT,
            bg=CARD_BG
        ).pack(side=tk.LEFT, padx=20, pady=18)

        # Body
        body = tk.Frame(self.root, bg=BG_COLOR)
        body.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)

        tk.Label(
            body,
            text="Install the military-grade AI surveillance supercomputer and local Next.js matrix.\nPre-configured for 15+ camera channels with zero cloud dependencies.",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=BG_COLOR,
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(0, 12))

        # Folder frame
        ff = tk.LabelFrame(
            body,
            text=" INSTALLATION DESTINATION ",
            font=("Segoe UI", 8, "bold"),
            fg=GOLD_ACCENT,
            bg=BG_COLOR,
            bd=1
        )
        ff.pack(fill=tk.X, pady=8)

        self.entry = tk.Entry(
            ff,
            textvariable=self.install_dir,
            font=("Consolas", 9),
            fg=TEXT_COLOR,
            bg=CARD_BG,
            bd=0,
            highlightthickness=1,
            highlightbackground="#2A303C",
            insertbackground=GOLD_ACCENT
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)

        tk.Button(
            ff,
            text="BROWSE...",
            font=("Segoe UI", 8, "bold"),
            fg=GOLD_ACCENT,
            bg=CARD_BG,
            bd=1,
            relief=tk.SOLID,
            command=self._browse
        ).pack(side=tk.RIGHT, padx=10, pady=10)

        # Checkboxes
        tk.Checkbutton(
            body,
            text="Create Desktop Protocol Shortcut",
            variable=self.create_desktop,
            font=("Segoe UI", 9),
            fg=TEXT_COLOR,
            bg=BG_COLOR,
            selectcolor=CARD_BG
        ).pack(anchor=tk.W, pady=4)

        tk.Checkbutton(
            body,
            text="Launch OMS Dashboard (http://localhost:8000) upon completion",
            variable=self.launch_after,
            font=("Segoe UI", 9),
            fg=TEXT_COLOR,
            bg=BG_COLOR,
            selectcolor=CARD_BG
        ).pack(anchor=tk.W, pady=2)

        # Progress
        self.prog_bar = ttk.Progressbar(body, orient="horizontal", mode="determinate")
        self.status_lbl = tk.Label(
            body,
            text="Ready to install.",
            font=("Segoe UI", 8),
            fg=TEXT_MUTED,
            bg=BG_COLOR
        )

        # Footer
        footer = tk.Frame(self.root, bg=BG_COLOR, height=50)
        footer.pack(fill=tk.X, side=tk.BOTTOM, padx=25, pady=(0, 15))

        tk.Button(
            footer,
            text="CANCEL",
            font=("Segoe UI", 8, "bold"),
            fg="#FF4A4A",
            bg=BG_COLOR,
            bd=1,
            command=self.root.quit
        ).pack(side=tk.LEFT)

        self.btn_install = tk.Button(
            footer,
            text="INSTALL NOW ➔",
            font=("Segoe UI", 9, "bold"),
            fg="#000000",
            bg=GOLD_ACCENT,
            bd=0,
            padx=18,
            pady=4,
            command=self._start
        )
        self.btn_install.pack(side=tk.RIGHT)

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self.install_dir.get())
        if d:
            self.install_dir.set(d)

    def _set_status(self, text, pct):
        def _u():
            self.status_lbl.config(text=text)
            self.prog_bar['value'] = pct
        self.root.after(0, _u)

    def _start(self):
        self.btn_install.config(state=tk.DISABLED)
        self.entry.config(state=tk.DISABLED)
        self.prog_bar.pack(fill=tk.X, pady=8)
        self.status_lbl.pack(anchor=tk.W, pady=2)
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            target = Path(self.install_dir.get()).resolve()
            target.mkdir(parents=True, exist_ok=True)
            desktop = Path(os.environ.get("USERPROFILE", "C:/Users/Default")) / "Desktop"

            # Terminate any running instance
            try:
                subprocess.run(["powershell", "-Command", f"Get-Process | Where-Object Path -like '*{target}*' | Stop-Process -Force"], capture_output=True)
            except Exception:
                pass

            self._set_status("Extracting AI engine and dependencies...", 20)

            # Locate bundle or source root
            base_dir = Path(getattr(sys, '_MEIPASS', Path(__file__).parent.resolve()))

            # Files and directories to copy
            items_to_copy = [
                "main.py", "web_server.py", "web_integration.py", "config.yaml",
                "identity_engine.py", "haae_engine.py", "face_engine.py",
                "db_engine.py", "auth_engine.py", "analytics_engine.py",
                "cloud_sync.py", "cloud_api.py", "requirements.txt",
                "hikvision_connection_guide.txt", "rtsp_10_cameras.txt",
                "yolov8n.pt", "yolov8s.pt", "start_oms_ai.bat", "start_oms_portable.bat"
            ]
            dirs_to_copy = ["models", "faces", "frontend", "logs"]

            total_items = len(items_to_copy) + len(dirs_to_copy)
            done = 0

            for it in items_to_copy:
                src = base_dir / it
                if not src.exists():
                    src = Path(__file__).parent / it
                if src.exists():
                    shutil.copy2(src, target / it)
                done += 1
                self._set_status(f"Deploying {it}...", int(20 + (done / total_items) * 50))

            for d in dirs_to_copy:
                src_d = base_dir / d
                if not src_d.exists():
                    src_d = Path(__file__).parent / d
                if src_d.exists():
                    dst_d = target / d
                    if dst_d.exists():
                        shutil.rmtree(dst_d, ignore_errors=True)
                    shutil.copytree(src_d, dst_d)
                done += 1
                self._set_status(f"Syncing {d}/ folder...", int(20 + (done / total_items) * 50))

            # Create standard launcher start_oms.bat
            self._set_status("Configuring system protocol launchers...", 80)
            bat_file = target / "start_oms.bat"
            with open(bat_file, "w", encoding="utf-8") as f:
                f.write('@echo off\ncd /d "%~dp0"\necho Starting OMS Sentinel...\nstart /b "" http://localhost:8000\npython main.py\npause\n')

            # Create Desktop Shortcut
            if self.create_desktop.get():
                self._set_status("Registering Desktop protocol shortcut...", 90)
                ps = (
                    f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{desktop}/OMS Sentinel.lnk'); "
                    f"$s.TargetPath = '{bat_file}'; "
                    f"$s.WorkingDirectory = '{target}'; "
                    f"$s.IconLocation = 'shell32.dll,220'; "
                    f"$s.Save()"
                )
                subprocess.run(["powershell", "-Command", ps], capture_output=True)

            self._set_status("Installation complete!", 100)

            def _done():
                if self.launch_after.get():
                    subprocess.Popen(["cmd.exe", "/c", str(bat_file)], cwd=str(target), creationflags=subprocess.CREATE_NEW_CONSOLE)
                messagebox.showinfo(
                    "OMS Sentinel Deployed",
                    f"OMS Sentinel successfully installed to:\n{target}\n\n"
                    f"Desktop shortcut created!\nWeb dashboard: http://localhost:8000"
                )
                self.root.destroy()

            self.root.after(0, _done)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Installation Error", f"Installation failed:\n{e}"))
            self.root.after(0, lambda: self.btn_install.config(state=tk.NORMAL))

if __name__ == "__main__":
    root = tk.Tk()
    app = FastOMSInstaller(root)
    root.mainloop()
