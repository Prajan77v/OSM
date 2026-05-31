# Object Sentinel Matrix (OSM) v9.0

A next-generation, ultra-premium AI smart surveillance system and command center. Built with Python and Next.js, OSM features real-time video processing, deep-learning facial recognition, behavior analytics, and a high-performance Next.js web dashboard, all wrapped in a cinematic Black & Gold luxury UI design.

---

## 🌟 What We Have Built
Throughout the development of this project, we have completely transformed a standard camera feed into an elite AI command center:
* **Premium Cinematic UI**: Re-engineered the OpenCV visual feed to feature glassmorphism, neon glows, animated crosshairs, and a true 1920x1080 UI-free fullscreen camera preview mode.
* **Deep Learning Face Recognition (No dlib required!)**: Implemented a state-of-the-art fallback engine using OpenCV's YuNet and SFace models, eliminating the notorious Windows `dlib` C++ compilation nightmare.
* **Intelligent Threat Engine**: Built a dynamic threat evaluation system (Green, Yellow, Orange, Red) that tracks object abandonment, running, pacing, and loitering.
* **Full-Stack Integration**: Developed a sleek Next.js frontend that hooks seamlessly into the Python FastAPI backend to monitor telemetry, view events, and trigger commands remotely.
* **Repository Restructuring**: Completely organized the codebase, designated `main.py` as the undisputed entry point, and purged all unwanted AI-generated scratch files for a professional GitHub presentation.

---

## 🚀 What It Can Do
* **Real-Time Object Detection**: Uses ultralytics YOLOv8 for high-speed, high-confidence tracking of people and objects.
* **Behavior Anomalies**: Autonomously flags suspicious behavior like pacing back and forth, sprinting, or abandoning objects (like backpacks).
* **Automated Evidence Capture**: Automatically isolates and saves high-quality cropped photos of intruders to the `faces/captured/` evidence locker.
* **Voice Annunciator**: Speaks critical alerts aloud (e.g., "Intruder detected", "Identity confirmed").
* **Immersive Fullscreen Mode**: Hides all data panels to give you a pure, unobstructed 1920x1080 view of your active camera.
* **Telegram Integration**: Can dispatch instant mobile alerts with photo evidence of security breaches.

---

## 🎮 How To Use (Keyboard Commands)
When the main OpenCV dashboard is running, use these keys to control the Matrix:

| Key | Action |
|:---:|:---|
| **`Z`** | **Toggle Cinematic Fullscreen**: Hides the UI and expands the focused camera to 1920x1080. |
| **`S` / `Tab`** | **Cycle Cameras**: Switches the active/focused camera feed. |
| **`R`** | **Register Face**: Looks at the active camera to capture and save your face as an authorized Operator. |
| **`Space`** | **Manual Alarm**: Instantly elevates the threat level to RED and triggers sirens. |
| **`C`** | **Export Logs**: Dumps all recent events to a CSV file. |
| **`Q`** | **Shutdown**: Safely terminates the AI, saves databases, and exits. |

---

## 🛠 Installation (Windows Only)

**Prerequisites:**
* Python 3.10 or 3.11
* Node.js (v18+)

**Step 1: Clone the Repository**
```powershell
git clone https://github.com/Prajan77v/OSM.git
cd OSM
```

**Step 2: Install Python Dependencies**
*Note: You do NOT need Visual Studio C++ build tools because we integrated YuNet as a dlib bypass!*
```powershell
pip install -r requirements.txt
```

**Step 3: Setup the Next.js Frontend**
```powershell
cd frontend
npm install
cd ..
```

**Step 4: Launch the Command Center**
You need two terminals.

*Terminal 1 (The AI Core):*
```powershell
# Inside the root OSM folder
python main.py
```

*Terminal 2 (The Web Dashboard):*
```powershell
# Inside the frontend folder
npm run dev
```
Once both are running, your local OpenCV window will pop up, and you can view the web UI at `http://localhost:3000`.

---

## 🧗‍♂️ Problems Undergone & Solved
Building a system of this complexity required solving several major technical hurdles:

1. **The `dlib` Windows Compilation Nightmare**: 
   * *Problem*: Installing `face_recognition` requires compiling `dlib`, which consistently fails on Windows machines without massive GBs of Visual Studio C++ tools installed.
   * *Solution*: Engineered a custom deep-learning fallback engine utilizing OpenCV's `YuNet` and `SFace` ONNX models. The system dynamically downloads these models and perfectly executes facial recognition using pure OpenCV.
2. **Cluttered UI in Fullscreen**: 
   * *Problem*: Expanding the window to fullscreen originally just stretched the side-panels and headers, creating an ugly layout. 
   * *Solution*: Re-wrote the rendering loop so that pressing `Z` suspends the UI canvas, forcing the focused camera to seamlessly take over the entire 1920x1080 viewport.
3. **Accidental Git Initialization in System Folders**: 
   * *Problem*: Git was accidentally initialized in the `AppData` VS Code directory, causing fatal identity errors.
   * *Solution*: Destroyed the bad git instance, re-initialized it cleanly inside the project workspace, and forcefully scrubbed 20+ temporary scratch files before pushing to GitHub.
4. **"Zone" Clutter**: 
   * *Problem*: The UI was bloated with bounding boxes for "Restricted Zones".
   * *Solution*: Systematically scrubbed all zone-rendering logic from the Python backend and Next.js frontend, returning the system to a clean, luxury "Black & Gold" aesthetic.
