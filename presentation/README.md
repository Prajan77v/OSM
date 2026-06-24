# 🛰️ OMS — OBJECT MONITORING SYSTEM

### ⚡ AI-Powered Smart Surveillance & Real-Time Monitoring Platform

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-00f0ff?style=for-the-badge&logo=python&logoColor=050814)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-ff007f?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![YOLO](https://img.shields.io/badge/YOLO-v8-ffaa00?style=for-the-badge&logo=ultralytics&logoColor=050814)](https://github.com/ultralytics/ultralytics)
[![PyQt6](https://img.shields.io/badge/PyQt6-GUI-00ff66?style=for-the-badge&logo=qt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![System Status](https://img.shields.io/badge/SYSTEM_STATUS-ONLINE%20%2F%20SCANNING-00ff66?style=for-the-badge&labelColor=050814)](https://github.com/yourprofile/oms)
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

**OMS (Object Monitoring System)** is a next-generation, AI-driven surveillance and real-time monitoring console. By integrating advanced deep learning models and high-frequency computer vision pipelines directly with live camera feeds, OMS elevates standard, passive CCTV hardware into an active, intelligent monitoring dashboard.

Whether analyzing RTSP streams, IP cameras, or standard USB webcams, OMS detects subjects, tracks spatial movement, identifies known personnel, logs security events, and presents a responsive HUD-style PyQt6 desktop controller interface.

---

## 👁️ SYSTEM PREVIEW // OVERVIEW

In traditional security environments, human operators are forced to sit through hours of stagnant footage, suffering from cognitive fatigue and missing key security indicators. 

**OMS bridges this gap** by injecting automation and machine intelligence straight into the loop. It continuously watches the scene, identifies target classes, registers known/unknown face profiles, maps movement trajectories, and maintains a structured, queryable event log.

---

## ⚠️ THE SURVEILLANCE GAP // PROBLEM STATEMENT

Standard video surveillance setups suffer from critical vulnerabilities that place property and security at risk:

* **The Fatigue Bottleneck:** Guards monitoring multiple feeds miss up to 95% of security incidents after just 20 minutes of continuous viewing.
* **Passive Post-Event Review:** Traditional systems serve only as digital tape recorders, helping you review *how* a break-in occurred, but doing nothing to *prevent* it in real time.
* **Stream Overload:** Managing, viewing, and making sense of dozens of cameras simultaneously is beyond human capacity.
* **Absence of Scene Context:** Traditional CCTV cameras cannot differentiate between a blowing branch, a stray dog, or a trespasser moving through a restricted zone.

**OMS turns surveillance from a passive archive tool into a proactive, intelligent agent.**

---

## 🚀 CORE CAPABILITIES // KEY FEATURES

OMS is organized into four main functional matrices:

### 📹 Live Feed Ingestion
* **Multi-Source Pipeline:** Seamlessly hook into standard USB Webcams, Local Video Directories, or Network CCTV feeds via RTSP / IP streams.
* **Concurrent Decoders:** High-performance, multithreaded frame capturing via OpenCV to maintain 24/7 stream consistency.

### 🧠 Vision Intelligence
* **Real-Time Classification:** YOLO-driven object detection classifying humans, luggage, tools, vehicles, and custom classes.
* **Face Verification:** Integrated deep face model mapping facial crops to a 128-dimensional vector database for instant identification of authorized personnel.
* **Dynamic Centroid Tracker:** Assigns persistent IDs to individuals, tracking motion vectors across frame successions to eliminate duplicate counts.

### 📊 Event Registry
* **Automated Log Entries:** Generates instant records detailing class labels, timestamps, confidence parameters, and tracking IDs.
* **Query-Ready Schema:** Organized logs structured for rapid filtering, export, or audit-trail verification.

### 🖥️ Operator Command Console
* **HUD PyQt6 UI:** A high-speed, hardware-accelerated desktop dashboard rendering real-time bounding boxes and operational tables.
* **Overlay Overrides:** Toggle camera bounding boxes, tracking trails, and face scan parameters on the fly.

---

## ⚡ PIPELINE FLOW // HOW OMS WORKS

The life of a video frame inside the OMS engine moves through the following stages:

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
[ Event Logging ] ────────► Commits Timestamped Alert Metadata to Disk Registry
       │
       ▼
[ Live UI Dashboard ] ────► Updates PyQt6 Screen Buffer and Active Log Grid
```

---

## 🏗️ ARCHITECTURAL SCHEMATIC // SYSTEM ARCHITECTURE

OMS uses a clean, decoupled layer architecture to separate UI threads, heavy AI inference tasks, and system logs:

1. **Input Interface Layer:** Decodes video sources into raw numpy frame matrices.
2. **Preprocessing Pipeline Layer:** Sanitizes and resizes frames to match YOLO neural input shapes without aspect distortion.
3. **Core Deep Learning Layer:** Executes parallel inference threads. Passes bounding frames to YOLO and facial crops to embedding models.
4. **Context Tracking Layer:** Evaluates frame-to-frame coordinate distances to persist tracking IDs.
5. **Database Registry Layer:** Handshakes log threads to dump metadata into CSV or database records without blocking frames.
6. **Presentation HUD Layer:** A PyQt6-based dashboard rendering the visual bounding box overlays and updating log lists.

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
| **Python** | System core, processing logic, and library gluing |
| **OpenCV** | Direct video ingestion, RTSP decoding, and drawing overlays |
| **YOLO Engine** | Deep learning model architecture for object detection |
| **PyQt6** | Desktop GUI layout, hardware rendering, and state buttons |
| **NumPy** | High-performance matrix operations on video frame buffers |
| **Face Recognition** | Facial crop embedding generation and similarity math |

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

## ⚙️ INITIALIZATION // INSTALLATION

### 1. Clone the Registry
```bash
git clone https://github.com/yourprofile/oms.git
cd oms
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

### 4. Fetch AI Models
Download the YOLO weights and FaceNet model files, placing them inside the `models/` directory:
```bash
# Example command or setup script
python core/download_models.py
```

---

## 📊 OPERATION GUIDE // USAGE

Launch the monitoring console:
```bash
python app/main.py
```

### Operational Steps:
1. **Choose Feed Source:** Select `Webcam`, `IP Camera (RTSP URL)`, or a `Local Video file` from the UI source dropdown.
2. **Start Scanner:** Click **INITIALIZE SYSTEM**. The live camera feed will load with bounding box overlays.
3. **Face Registration:** Navigate to the database config menu to register names and photos for face recognition.
4. **Read Logs:** The operational log grid on the right updates instantly as new subjects enter or leave the camera scene.
5. **System Export:** Event histories can be exported to CSV files inside the `logs/` directory for analytical reports.

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

## 🔮 UPCOMING TRANSMISSIONS // FUTURE ROADMAP

- [ ] **Anomaly Detection Layer:** Automatically trigger warning overlays for loitering, falls, or physical violence.
- [ ] **Instant Security Alerts:** Connect Telegram bot integrations to forward snapshots of intruders directly to mobile devices.
- [ ] **Multi-Stream Node Layout:** Scale the GUI layout to monitor 4 distinct camera RTSP streams simultaneously.
- [ ] **Cloud Logs Syncer:** Export SQLite surveillance database records directly to remote Web panels.
- [ ] **Hardware Acceleration:** Complete integration of TensorRT/ONNX Runtime for faster edge device processing.

---

## 📡 SYSTEM TERMINAL // CONCLUSION

OMS demonstrates how lightweight modern deep learning models can be bundled into standard computer hardware to build active, intelligent home or facility security applications. 

Explore the source code, play around with the modules, and help us improve the monitoring engine!

* **Maintained by:** [Student Name]
* **Project Status:** Active/Operational
* **Contributions:** PRs are welcome. Please read contribution guidelines before submitting edits.
* **License:** This project is licensed under the MIT License.
