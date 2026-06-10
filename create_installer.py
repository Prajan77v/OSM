"""
OMS Sentinel - GUI Installer Wizard
Packs the compiled Sentinel files and registers Desktop/Start Menu shortcuts.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

# Dark tech palette matching OMS dashboard
BG_COLOR = "#0D0F12"
CARD_BG = "#161A22"
GOLD_ACCENT = "#D4AF37"
TEXT_COLOR = "#FFFFFF"
TEXT_MUTED = "#8E9AA8"

class OMSInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title("OMS Sentinel Installation Matrix")
        self.root.geometry("550x380")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)

        # Set style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TProgressbar", thickness=8, troughcolor=BG_COLOR, background=GOLD_ACCENT)

        # Setup variables
        self.install_dir = tk.StringVar(value=str(Path.home() / "OMS_Sentinel"))
        self.create_desktop_shortcut = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        # Header banner
        header = tk.Frame(self.root, bg=CARD_BG, height=60)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text="OMS SENTINEL v9.0 INSTALLER",
            font=("Orbitron", 12, "bold"),
            fg=GOLD_ACCENT,
            bg=CARD_BG
        )
        title.pack(side=tk.LEFT, padx=20, pady=15)

        # Body area
        body = tk.Frame(self.root, bg=BG_COLOR)
        body.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        desc = tk.Label(
            body,
            text="This wizard will install the stand-alone OMS Sentinel Surveillance engine and the Next.js visual dashboard matrix on your system.",
            font=("Inter", 9),
            fg=TEXT_MUTED,
            bg=BG_COLOR,
            wraplength=480,
            justify=tk.LEFT
        )
        desc.pack(anchor=tk.W, pady=(0, 15))

        # Target Folder Frame
        folder_frame = tk.LabelFrame(
            body,
            text=" TARGET DEPLOYMENT DIRECTORY ",
            font=("Orbitron", 8, "bold"),
            fg=GOLD_ACCENT,
            bg=BG_COLOR,
            bd=1,
            relief=tk.FLAT
        )
        folder_frame.pack(fill=tk.X, pady=10)

        self.entry = tk.Entry(
            folder_frame,
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

        browse_btn = tk.Button(
            folder_frame,
            text="BROWSE...",
            font=("Orbitron", 8, "bold"),
            fg=GOLD_ACCENT,
            bg=BG_COLOR,
            activeforeground=TEXT_COLOR,
            activebackground=GOLD_ACCENT,
            bd=1,
            highlightthickness=0,
            relief=tk.SOLID,
            command=self.browse_dir
        )
        browse_btn.pack(side=tk.RIGHT, padx=10, pady=10)

        # Shortcuts frame
        self.shortcut_check = tk.Checkbutton(
            body,
            text="Create Desktop Shortcut Protocol",
            variable=self.create_desktop_shortcut,
            font=("Inter", 9),
            fg=TEXT_COLOR,
            bg=BG_COLOR,
            activeforeground=TEXT_COLOR,
            activebackground=BG_COLOR,
            selectcolor=BG_COLOR
        )
        self.shortcut_check.pack(anchor=tk.W, pady=10)

        # Progress elements (initially hidden)
        self.prog_bar = ttk.Progressbar(body, orient="horizontal", mode="determinate")
        self.status_lbl = tk.Label(
            body,
            text="Awaiting user confirmation...",
            font=("Consolas", 8),
            fg=TEXT_MUTED,
            bg=BG_COLOR
        )

        # Footer Actions
        footer = tk.Frame(self.root, bg=BG_COLOR, height=50)
        footer.pack(fill=tk.X, side=tk.BOTTOM, padx=25, pady=(0, 15))

        self.cancel_btn = tk.Button(
            footer,
            text="CANCEL",
            font=("Orbitron", 8, "bold"),
            fg="#FF4A4A",
            bg=BG_COLOR,
            activeforeground=TEXT_COLOR,
            activebackground="#FF4A4A",
            bd=1,
            relief=tk.SOLID,
            command=self.root.quit
        )
        self.cancel_btn.pack(side=tk.LEFT)

        self.install_btn = tk.Button(
            footer,
            text="EXECUTE DEPLOYMENT",
            font=("Orbitron", 8, "bold"),
            fg=BG_COLOR,
            bg=GOLD_ACCENT,
            activeforeground=TEXT_COLOR,
            activebackground=BG_COLOR,
            bd=0,
            padx=15,
            command=self.start_install
        )
        self.install_btn.pack(side=tk.RIGHT)

    def browse_dir(self):
        dir_selected = filedialog.askdirectory(initialdir=self.install_dir.get())
        if dir_selected:
            self.install_dir.set(dir_selected)

    def update_progress(self, text, value):
        def _update():
            self.status_lbl.config(text=text)
            self.prog_bar['value'] = value
        self.root.after(0, _update)

    def start_install(self):
        # Disable buttons
        self.install_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.DISABLED)
        self.entry.config(state=tk.DISABLED)
        self.shortcut_check.config(state=tk.DISABLED)

        # Show progress
        self.prog_bar.pack(fill=tk.X, pady=5)
        self.status_lbl.pack(anchor=tk.W, pady=2)
        self.root.update()

        import threading

        def _thread_target():
            try:
                self.run_install()
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Deployment Error", f"OMS Installation aborted due to exception:\n{e}"))
                self.root.after(0, lambda: self.install_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.cancel_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.entry.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.shortcut_check.config(state=tk.NORMAL))

        threading.Thread(target=_thread_target, daemon=True).start()

    def run_install(self):
        target = Path(self.install_dir.get()).resolve()
        target.mkdir(parents=True, exist_ok=True)
        desktop = Path(os.environ["USERPROFILE"]) / "Desktop"

        # Terminate any active processes running out of the target folder to release file locks
        try:
            ps_cmd = f"Get-Process | Where-Object Path -like '*{target}*' | Stop-Process -Force"
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
        except Exception:
            pass

        # Locate files in bundle
        base_path = Path(getattr(sys, '_MEIPASS', Path(__file__).parent.resolve()))
        main_src = base_path / "main.py"
        ws_src = base_path / "web_server.py"
        wi_src = base_path / "web_integration.py"
        req_src = base_path / "requirements.txt"
        cfg_src = base_path / "config.yaml"
        faces_src = base_path / "faces"
        frontend_src = base_path / "frontend" / "out"

        # Fallback to local files if run directly in dev env
        if not main_src.exists():
            main_src = Path(__file__).parent / "main.py"
            ws_src = Path(__file__).parent / "web_server.py"
            wi_src = Path(__file__).parent / "web_integration.py"
            req_src = Path(__file__).parent / "requirements.txt"
            cfg_src = Path(__file__).parent / "config.yaml"
            faces_src = Path(__file__).parent / "faces"
            frontend_src = Path(__file__).parent / "frontend" / "out"

        if not main_src.exists():
            raise FileNotFoundError("Source engine code 'main.py' not found in bundle.")

        # Copy source files
        self.update_progress("Extracting source files...", 15)
        shutil.copy2(main_src, target / "main.py")
        shutil.copy2(ws_src, target / "web_server.py")
        shutil.copy2(wi_src, target / "web_integration.py")
        shutil.copy2(req_src, target / "requirements.txt")
        if cfg_src.exists():
            shutil.copy2(cfg_src, target / "config.yaml")

        # Create env example
        with open(target / ".env", "w", encoding="utf-8") as f:
            f.write("# OMS Environment Protocols\nPORT=8000\nTELEGRAM_SPAM_COOLDOWN=300\n")

        # Copy frontend pages
        self.update_progress("Extracting web dashboard pages...", 30)
        if frontend_src.exists():
            dst_frontend = target / "frontend" / "out"
            if dst_frontend.exists():
                shutil.rmtree(dst_frontend)
            shutil.copytree(frontend_src, dst_frontend)

        # Set up Python environment
        self.update_progress("Checking system Python installation...", 40)
        
        has_python = False
        try:
            # Add a short timeout to prevent hanging on Microsoft Store alias checks
            res = subprocess.run(["python", "--version"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                has_python = True
        except Exception:
            pass
            
        python_cmd = "python"
        pip_cmd = "pip"
        is_portable = False
        
        if has_python:
            self.update_progress("Creating Python virtual environment (venv)...", 50)
            venv_dir = target / "venv"
            try:
                # Add a 20-second timeout to prevent infinite hangs on broken/alias Python installations
                subprocess.run(["python", "-m", "venv", str(venv_dir)], capture_output=True, timeout=20)
                python_cmd = str(venv_dir / "Scripts" / "python.exe")
                pip_cmd = str(venv_dir / "Scripts" / "pip.exe")
                
                # Double-check that it was actually created successfully
                if not Path(python_cmd).exists() or not Path(pip_cmd).exists():
                    raise FileNotFoundError("Virtual environment binaries not created.")
            except Exception:
                # If venv creation times out or fails, fallback to portable python download
                has_python = False

        if not has_python:
            # Fallback/Download portable python
            self.update_progress("System Python failed/not found. Downloading portable Python (10MB)...", 50)
            
            py_zip = target / "python_embed.zip"
            py_dir = target / "python_env"
            py_dir.mkdir(exist_ok=True)
            is_portable = True
            
            import urllib.request
            import zipfile
            
            url = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
            try:
                urllib.request.urlretrieve(url, py_zip)
                self.update_progress("Extracting portable Python...", 55)
                with zipfile.ZipFile(py_zip, 'r') as zip_ref:
                    zip_ref.extractall(py_dir)
                py_zip.unlink()
                
                # Enable site-packages in python311._pth
                pth_file = py_dir / "python311._pth"
                if pth_file.exists():
                    with open(pth_file, "r") as f:
                        lines = f.readlines()
                    with open(pth_file, "w") as f:
                        for line in lines:
                            if "import site" in line or "#import site" in line:
                                f.write("import site\n")
                            else:
                                f.write(line)
                                
                # Download get-pip.py
                self.update_progress("Setting up package manager...", 60)
                get_pip = py_dir / "get-pip.py"
                urllib.request.urlretrieve("https://bootstrap.pypa.io/get-pip.py", get_pip)
                subprocess.run([str(py_dir / "python.exe"), str(get_pip)], capture_output=True)
                get_pip.unlink()
                
                python_cmd = str(py_dir / "python.exe")
                pip_cmd = str(py_dir / "Scripts" / "pip.exe")
            except Exception as download_err:
                raise Exception(f"System Python is missing, and automated fallback failed: {download_err}\n\nPlease install Python 3.11 from python.org and retry.")

        # Install requirements
        self.update_progress("Installing dependencies (PyTorch, YOLO, OpenCV)...", 65)
        
        # Stream pip output to installer status label in real time to reassure user
        process = subprocess.Popen(
            [pip_cmd, "install", "-r", str(target / "requirements.txt")],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if line:
                if "Installing collected packages" in line:
                    self.update_progress("pip: Unpacking & copying files (H: drive is slow, please wait 3-8m)...", 65)
                else:
                    # Truncate very long log lines to fit status label
                    display_line = line
                    if len(display_line) > 75:
                        display_line = display_line[:72] + "..."
                    self.update_progress(f"pip: {display_line}", 65)
                
        process.stdout.close()
        return_code = process.wait()
        
        if return_code != 0:
            raise Exception("Dependency installation failed. Check internet connection and retry.")

        # Copy Face registries
        self.update_progress("Syncing identity database folder...", 80)
        if faces_src.exists():
            dst_faces = target / "faces"
            if dst_faces.exists():
                shutil.rmtree(dst_faces)
            shutil.copytree(faces_src, dst_faces)

        # Write execution batch file launcher
        self.update_progress("Writing execution protocol launchers...", 85)
        
        bat_launcher = target / "OMS_Sentinel.bat"
        with open(bat_launcher, "w", encoding="utf-8") as f:
            if is_portable:
                f.write(f"@echo off\ncd /d \"%~dp0\"\nstart python_env\\python.exe main.py\n")
            else:
                f.write(f"@echo off\ncd /d \"%~dp0\"\nstart venv\\Scripts\\python.exe main.py\n")

        # Create Desktop Shortcut
        if self.create_desktop_shortcut.get():
            self.update_progress("Registering system shortcuts...", 90)
            
            ps_cmd = (
                f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{desktop}/OMS Sentinel.lnk'); "
                f"$s.TargetPath = '{bat_launcher}'; "
                f"$s.WorkingDirectory = '{target}'; "
                f"$s.Save()"
            )
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)

        # Uninstall batch registry
        self.update_progress("Creating uninstaller script...", 95)
        
        uninst_bat = target / "Uninstall_OMS.bat"
        with open(uninst_bat, "w", encoding="utf-8") as f:
            f.write(
                f"@echo off\n"
                f"echo Deleting OMS Sentinel from system...\n"
                f"del /f /q \"{desktop}\\OMS Sentinel.lnk\" >nul 2>&1\n"
                f"echo Removing folder {target}...\n"
                f"cd \\\n"
                f"start /b \"\" cmd /c \"timeout /t 2 /nobreak >nul & rmdir /s /q \\\"{target}\\\"\"\n"
                f"echo OMS fully removed.\n"
            )

        self.update_progress("Deployment matrix initialized.", 100)

        def _finish():
            messagebox.showinfo(
                "OMS Sentinel deployed",
                f"Deployment successfully completed!\n\n"
                f"Deployment location: {target}\n"
                f"Shortcuts created on operator desktop.\n\n"
                f"Launch the dashboard by double clicking the shortcut."
            )
            self.root.destroy()
        self.root.after(0, _finish)

if __name__ == "__main__":
    main_root = tk.Tk()
    app = OMSInstaller(main_root)
    main_root.mainloop()
