# Object Sentinel Matrix (OSM) — v9.0

[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11-gold?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Next.js Version](https://img.shields.io/badge/Next.js-16%2B-gold?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Modern--API-gold?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-gold?style=for-the-badge)](https://opensource.org/licenses/MIT)

**Object Sentinel Matrix (OSM)** is an enterprise-grade AI-powered smart surveillance system and interactive command center. By combining Python’s computer vision capability with a high-performance Next.js dashboard, OSM delivers real-time video telemetry, deep learning facial recognition, and behavioral anomaly detection wrapped in a stunning, cinematic luxury **Black & Gold** interface.

---

## 📸 System Overview

*(Add screenshots of your premium OpenCV layout and Next.js Web Dashboard here to showcase the Black & Gold UI)*

---

## 🌟 Key Features

* **High-Performance Vision Engine**: Utilizes Ultralytics **YOLOv8** for real-time tracking of personnel and object telemetry.
* **No-Compile Facial Recognition**: Features a state-of-the-art fallback recognition pipeline powered by OpenCV's **YuNet** and **SFace** ONNX engines, bypassing complex C++ compilation setups on Windows/macOS.
* **Dynamic Node Orchestration**: Add, remove, rename, and monitor camera streams dynamically from the web interface without stopping the surveillance core.
* **Behavior Anomaly Detection**: Autonomously flags loitering, running/sprinting, and abandoned objects using relative velocity and temporal calculations.
* **Async Logging & Storage**: Employs an event-driven, non-blocking dirty-flag architecture to flush database states and save frame capture logs without impacting high-FPS camera rendering.
* **Security Integrations**: Instant snapshot captures saved directly to the `/faces/captured/` evidence directory with options for Telegram alert broadcasts.

---

## 📂 Repository Structure

```directory
OSM/
├── main.py                     # AI core execution engine & OpenCV rendering loop
├── web_server.py               # FastAPI backend exposing camera control & log telemetry APIs
├── dev_server.py               # Local server coordination script
├── config.yaml                 # System configurations & camera settings
├── requirements.txt            # Python dependencies list
├── frontend/                   # Next.js web application
│   ├── src/
│   │   └── app/
│   │       ├── page.tsx        # Command center web dashboard UI
│   │       └── globals.css     # CSS style variables & layout configurations
│   └── package.json
└── faces/
    ├── baselines/              # Reference face photos for registered personnel
    └── captured/               # Auto-isolated security breach snapshot evidence
```

---

## 🛠️ Quick Start & Installation

### Prerequisites
* **Python**: `3.10` or `3.11`
* **Node.js**: `v18+` (npm included)

### Step-by-Step Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Prajan77v/OSM.git
   cd OSM
   ```

2. **Configure Python Core**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Frontend Dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Launch Command Center**
   Run the backend core and frontend dashboard simultaneously:

   * **Terminal 1 (AI Surveillance Core)**:
     ```bash
     python main.py
     ```
   * **Terminal 2 (Next.js Dashboard)**:
     ```bash
     cd frontend
     npm run dev
     ```

   Once initialized, open `http://localhost:3000` in your web browser.

---

## 🎮 Desktop Shortcuts & Interface Controls

When the active OpenCV window is selected, use these hotkeys to navigate the interface:

| Key | Operation | Description |
| :---: | :--- | :--- |
| **`Z`** | **Toggle Fullscreen Preview** | Instantly toggles a clean, distraction-free camera stream layout. |
| **`Tab`** | **Cycle Camera Stream** | Cycles active focus through available video devices. |
| **`R`** | **Register Face** | Registers the current frame subject as an authorized operator database baseline. |
| **`Space`** | **Trigger Alarm** | Sets the current threat level to MAXIMUM (Red alert). |
| **`C`** | **Export Logs** | Syncs system logs and outputs a clean CSV log export. |
| **`Q`** | **Graceful Shutdown** | Releases hardware feeds, saves operational databases, and exits. |

---

## 🧗‍♂️ Challenges Solved

* **Windows dlib Dependency Bypass**: Building face recognition on Windows traditionally requires compiling C++ `dlib` binaries, which demands gigabytes of Visual Studio workloads. We bypassed this entirely by engineering a dual-engine fallback using **YuNet** and **SFace** running directly via OpenCV's `dnn` module.
* **Dynamic Camera Hot-Swapping**: Traditional surveillance loops freeze or crash when camera devices are unplugged or added. We resolved this by building a dedicated thread cleanup guard checking `removed` states and cleaning index shifts dynamically.
* **Non-Blocking Write Queue**: Standard file writing blocks vision runtime loops. We optimized file writes through an asynchronous dirty-flag system which schedules saves off the main GUI thread.
* **Cinematic Aesthetic Refinements**: Scrubbed cluttering HUD indicators and zone outlines to guarantee a luxury UI look with high-visibility neon Gold/Black themes.ck & Gold" aesthetic.
