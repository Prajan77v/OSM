# 🛰️ OMS — OBJECT MONITORING SYSTEM

### ⚡ AI-Powered Smart Surveillance & Real-Time Monitoring Platform

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-00f0ff?style=for-the-badge&logo=python&logoColor=050814)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-ff007f?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![YOLO](https://img.shields.io/badge/YOLO-v8-ffaa00?style=for-the-badge&logo=ultralytics&logoColor=050814)](https://github.com/ultralytics/ultralytics)
[![PyQt6](https://img.shields.io/badge/PyQt6-GUI-00ff66?style=for-the-badge&logo=qt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![System Status](https://img.shields.io/badge/SYSTEM_STATUS-ONLINE%20%2F%20SCANNING-00ff66?style=for-the-badge&labelColor=050814)](https://github.com/Prajan77v/OSM)
[![License](https://img.shields.io/badge/LICENSE-MIT-94a3b8?style=for-the-badge)](https://choosealicense.com/licenses/mit/)

</div>

---

```
========================================================================
[OMS SYSTEM TERMINAL BOOTUP]
>> INITIALIZING AI ENGINE... OK
>> LINKING CAMERA FEED PORTS... OK
>> LOADING OBJECT DETECTION DATASET... YOLOv8 ACTIVE
>> SECURITY PROTOCOLS... OPERATIONAL
========================================================================
```

**OMS (Object Monitoring System)** is an AI-powered smart surveillance and monitoring platform. By running advanced computer vision models directly on live camera feeds, OMS turns standard, passive security cameras into active, intelligent monitoring stations.

---

## 👁️ OMS AT A GLANCE // WHAT IS OMS?

In simple terms, OMS is a desktop software application that connects to standard video cameras (like webcams or CCTV streams) and uses AI to continuously watch the feed. 

Instead of requiring a human operator to constantly stare at a screen, OMS automatically identifies who and what is in the video, tracks movements, registers names, and logs important events in real time.

---

## 🚀 CORE CAPABILITIES // WHAT OMS CAN DO

OMS is designed with simple, powerful features to automate surveillance:

* **📹 Live Camera Monitoring**
  Inject and monitor video feeds in real time from USB webcams, pre-recorded video files, or network IP cameras (using RTSP streams).
* **🔍 Object & Person Detection**
  Automatically detect and classify people and objects (such as backpacks, luggage, or tools) in the video frames using the YOLO model.
* **🆔 Face Recognition**
  Identify registered faces (such as employees, students, or family members) in the stream and match them against a database.
* **📍 Movement Tracking**
  Follow the movement of people and objects across consecutive video frames, assigning a unique tracking ID to each subject to prevent double-counting.
* **📊 Event Logging**
  Save important detections, timestamps, tracking IDs, and classifications automatically to a local log database for later review.
* **🖥️ Live Dashboard Display**
  View the live camera stream with active bounding boxes, tracking trails, and log tables on a clean, interactive operator dashboard.

---

## 🎮 USING OMS IN PRACTICE // HOW IT IS USED

Operating OMS is simple and does not require technical expertise:

1. **Launch the App:** Open a terminal and start the application console:
   ```bash
   python app/main.py
   ```
2. **Select Feed Source:** Use the source dropdown menu on the dashboard to select your camera stream (e.g., standard `Webcam`, or input a network `RTSP URL`).
3. **Initialize Surveillance:** Click the **INITIALIZE SYSTEM** button. The dashboard will load the live camera feed and start overlaying AI bounding boxes in real time.
4. **Register Face Templates:** Navigate to the database configuration tab to register names and photos for face recognition matching.
5. **Read Live Logs:** Detections, labels, and timestamps will automatically populate the active event grid on the dashboard for real-time tracking.

---

## 🛰️ TARGET DEPLOYMENTS // WHERE OMS CAN BE APPLIED

* **🏫 Colleges & Campuses:** Automated perimeter surveillance and entrance logs.
* **🏢 Offices & Workspaces:** Track employee attendance and restricted area entries.
* **🔬 Computer Labs:** Monitor access logging of high-value equipment racks.
* **🛒 Retail & Shops:** Track customer entry patterns and count visits.
* **🔒 Restricted Zones:** Trigger alerts when unauthorized personnel enter specified coordinates.
* **🏡 Home Surveillance:** Secure entrance monitoring with detailed activity records.

---

## 📸 COMMAND CONTROL // SHOWCASE & DEMOS

<div align="center">

### OMS Dashboard UI Console
*Desktop dashboard built with PyQt6 displaying video stream overlays, active track cards, and live log tables.*
![OMS Dashboard UI](assets/dashboard_preview.png)

<br>

### Real-Time Detections Gallery
*YOLOv8 boundaries identifying person classifications, bags, and tools simultaneously.*
![Detections Showcase](assets/yolo_detection.gif)
![Face Verification Scan](assets/facerec_scanner.png)

</div>

---

## ⚡ PIPELINE FLOW // HOW OMS WORKS

Here is how a video frame moves through the system from capture to output:

```
[ Camera Feed ] ──────────► Ingests Raw Streams (Webcam, CCTV, RTSP)
       │
       ▼
[ Frame Capture ] ────────► Decodes and Buffers Video Packets (OpenCV)
       │
       ▼
[ Preprocessing ] ────────► Normalizes Frame Layout, Scales, and Color Space
       │
       ▼
[ Object Detection ] ─────► YOLO Inference Maps Boundaries and Classes
       │
       ▼
[ Face Rec / Track ] ─────► Extracts Embedding Vector & Associates Tracking ID
       │
       ▼
[ Event Logging ] ────────► Commits Alert Metadata to Disk Database
       │
       ▼
[ Live UI Dashboard ] ────► Updates PyQt6 Screen Buffer and Active Log Grid
```

---

## 🏗️ ARCHITECTURAL SCHEMATIC // SYSTEM ARCHITECTURE

OMS is structured into separate layers to ensure clean performance and fast processing:

1. **Input Interface Layer:** Decodes video sources into raw frame matrices.
2. **Preprocessing Layer:** Sanitizes and resizes frames to match model input sizes.
3. **Core Deep Learning Layer:** Runs parallel inference threads for YOLO detection and facial embeddings.
4. **Context Tracking Layer:** Tracks coordinate movements across frames to persist tracking IDs.
5. **Database Registry Layer:** Asynchronously logs alert updates to files.
6. **Presentation Layer:** A PyQt6-based dashboard rendering the visual bounding box overlays and logs.

---

## 🧩 MODULE BREAKDOWN // FUNCTIONAL SCHEMATIC

```
 OMS PLATFORM
 ├── Camera Input Module    ── Ingests feeds, scales resolution, drops dead frames.
 ├── Detection Module       ── Runs YOLO model, extracts boundary boxes & conf.
 ├── Face Rec Module        ── Isolates faces, runs embedding comparisons.
 ├── Tracking Module        ── Persists IDs across frame coordinates over time.
 ├── Event Logger Module    ── Asynchronously commits event tables to disk.
 └── PyQt6 Dashboard UI     ── Manages screen layouts, overlay switches, lists.
```

---

## 💻 TECH STACK // POWERING THE SYSTEM

| Technology | Purpose / Application |
| :--- | :--- |
| **Python** | Core programming language |
| **OpenCV** | Video frame capture, scaling, and overlay drawing |
| **YOLO Engine** | Deep learning model for multi-object detection |
| **PyQt6** | Desktop GUI layout, buttons, and dashboard frame rendering |
| **NumPy** | High-performance matrix calculations on frame buffers |
| **Face Recognition** | Facial crop embedding generation and similarity math |

---

## ⚙️ INITIALIZATION // INSTALLATION

### 1. Clone the Registry
```bash
git clone https://github.com/Prajan77v/OSM.git
cd osm
```

### 2. Configure Virtual Environment
```bash
# Create environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS / Linux
source venv/bin/activate
```

### 3. Load Dependencies
```bash
pip install -r requirements.txt
```

### 5. Launch the Application
```bash
python app/main.py
```

---

## 📁 SYSTEM LAYOUT // PROJECT STRUCTURE

Below is the repository directory tree for the Object Monitoring System:

```
oms/
├── app/
│   ├── __init__.py
│   └── main.py                     # App bootstrap and main thread loop
├── core/
│   ├── __init__.py
│   ├── camera.py                   # Camera stream thread pool manager
│   ├── engine.py                   # Master processing loop orchestrator
│   └── logger.py                   # Event writer thread (CSV/SQLite)
├── detection/
│   ├── __init__.py
│   ├── yolo_detector.py            # YOLO model interface and boundaries extractor
│   └── classes.txt                 # Target label classes configuration
├── recognition/
│   ├── __init__.py
│   ├── face_rec.py                 # Embedding generator and database matcher
│   └── database/                   # Storage of registered personnel faces
├── tracking/
│   ├── __init__.py
│   └── tracker.py                  # Centroid-based tracking algorithm
├── ui/
│   ├── __init__.py
│   ├── dashboard.py                # PyQt6 window layouts and controllers
│   ├── resources/                  # UI icons, stylesheets, and assets
│   └── stylesheet.qss              # Custom cyberpunk dark-mode styles
├── models/
│   ├── yolov8n.pt                  # YOLO model weight assets (auto-downloaded)
│   └── facenet.onnx                # Face embedding model file
├── logs/
│   └── event_logs.csv              # Output log files for surveillance telemetry
├── requirements.txt                # System dependency configuration
└── README.md                       # Documentation index
```

---

## 🔮 UPCOMING TRANSMISSIONS // FUTURE ROADMAP

* **Behavior Anomaly Flags:** Automatically trigger warning overlays for loitering, falls, or physical violence.
* **Instant Security Alerts:** Connect Telegram bot integrations to forward snapshots of intruders directly to mobile devices.
* **Multi-Stream Node Layout:** Scale the GUI layout to monitor 4 distinct camera RTSP streams simultaneously.
* **Cloud Logs Syncer:** Export SQLite surveillance database records directly to remote Web panels.
* **Hardware Acceleration:** Complete integration of TensorRT/ONNX Runtime for faster edge device processing.

---

## 📡 SYSTEM TERMINAL // CONCLUSION

OMS demonstrates how lightweight modern deep learning models can be bundled into standard computer hardware to build active, intelligent home or facility security applications. 

Explore the source code, play around with the modules, and help us improve the monitoring engine!

* **Maintained by:** Prajan77v
* **Project Status:** Active/Operational
* **Contributions:** PRs are welcome. Please read contribution guidelines before submitting edits.
* **License:** This project is licensed under the MIT License.
