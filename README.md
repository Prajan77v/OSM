# 🛰️ OMS — OBJECT MONITORING SYSTEM v9.0

### ⚡ Next-Gen AI-Powered Smart Surveillance & Real-Time Monitoring Platform

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-00f0ff?style=for-the-badge&logo=python&logoColor=050814)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-ff007f?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![YOLO](https://img.shields.io/badge/YOLO-v8-ffaa00?style=for-the-badge&logo=ultralytics&logoColor=050814)](https://github.com/ultralytics/ultralytics)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-Frontend-black?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![License](https://img.shields.io/badge/LICENSE-MIT-94a3b8?style=for-the-badge)](https://choosealicense.com/licenses/mit/)

</div>

---

```
========================================================================
[OMS SYSTEM TERMINAL BOOTUP]
>> INITIALIZING DUAL RECOGNITION ENGINES... OK
>> LINKING FASTAPI BACKEND PORTS... OK
>> LOADED FRONTEND WEB MATRIX... Next.js EXPORT ACTIVE
>> SECURITY PROTOCOLS... OPERATIONAL
========================================================================
```

**OMS (Object Monitoring System)** is an AI-powered smart surveillance and monitoring platform. By running advanced computer vision models directly on live camera feeds, OMS turns standard, passive security cameras into active, intelligent monitoring stations.

---

## 👁️ OMS AT A GLANCE // WHAT IS OMS?

OMS is a next-generation desktop & web surveillance application that connects to standard video cameras (like webcams or CCTV streams) and uses AI to continuously watch the feed. 

Instead of requiring a human operator to constantly stare at a screen, OMS automatically identifies who and what is in the video, tracks movements, registers names, anomalies, and logs important events in real time.

---

## 🚀 CORE CAPABILITIES // WHAT OMS CAN DO

OMS is designed with simple, powerful features to automate surveillance:

* **📹 Live Camera Monitoring**
  Inject and monitor video feeds in real time from USB webcams, pre-recorded video files, or network IP cameras (using RTSP streams).
* **🔍 Multi-Engine Facial & Object Recognition**
  * **ArcFace / SFace Biometric Recognition**: 512-dim neural embeddings for sub-second person identification with multi-pose continuous learning.
  * **Object Identification (MobileNetV2 / ResNet50)**: Feature extraction for physical items (keyboards, laptops, backpacks, mugs) to track them by custom names.
* **🧠 Unified Profile Merging & Auto-Deduplication Engine**
  * **Zero Duplicate Guarantee**: Never creates duplicate entries for the same subject. If a new face matches an existing profile ($\text{similarity} \ge 0.38$) or is renamed to an existing name (case-insensitive), it is **instantly unified into a single profile**.
  * **Embedding & History Aggregation**: Merges multi-angle facial embeddings, consolidates cumulative visit counts, and preserves primary reference photos.
  * **Live Stream Track Re-Routing**: Dynamically updates all active camera inference loops, ByteTrack track-to-PID maps, and HUD identity badges without requiring a restart.
  * **Startup & On-Save Dedup Scans**: Continuous automated deduplication cleans and synchronizes the memory database across JSON and SQLite stores.
* **🎯 Continuous Object Tracking & Competitive NMS**
  * **Competitive Cross-Class NMS**: Resolves overlapping candidate detections on physical items (e.g., competing phone vs remote detections on a hand) by keeping the highest-confidence valid object while maintaining person interaction.
  * **Noise Gating ($\ge 42\%$) & Hit Filtering**: Eliminates low-confidence background clutter and 1-frame flickering glitches.
  * **Spatial Memory & Kalman Smoothing**: Maintains stable track trajectories with a 3.5s recovery buffer and smooth HUD bounding box interpolation.
* **📦 Advanced Face & Object Enrollment Matrix**
  * **Guided Capture**: Capture multi-view object perspectives with orientation helpers (`front`, `back`, `left`, `right`, `top`, `bottom`, `left_45`, `right_45`).
  * **Center-Crop Fallback**: Auto-crops the center 50% of the frame during guided captures if the custom object is not natively detected by YOLO's default classes.
  * **Direct Image Upload**: Drag-and-drop or select object photos from your browser, name them, and register them instantly using base64 JSON APIs.
* **🔍 High-Resolution Biometric Lightbox Preview**
  * Click on any face avatar (Active Portrait, Inspector, or Memory Database) to open an enlarged modal view with scanline animations, visit logs, confidence percentages, and instant profile management.
* **📍 Movement & Anomaly Tracking**
  Follow the movement of people and objects across consecutive video frames, assigning a unique tracking ID to each subject and checking for abnormal behaviors (pacing, running, abandoned objects).
* **🖥️ Cinematic Web Dashboard**
  A premium dark-themed Next.js operator dashboard featuring real-time stream overlays, active track cards, telemetry metrics, and event log tables.

---

## ⚙️ INITIALIZATION // INSTALLATION

### Standalone Installer (Recommended)
Compile the standalone GUI installer on Windows:
```bash
python build_exe.py
```
This produces:
* **Windows Installer Wizard**: `dist/OMS_Sentinel_Installer.exe`
* **Portable ZIP Bundle**: `dist/OMS_Sentinel_Portable.zip`

### Developer Setup
1. **Configure Environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
2. **Install Python Packages:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Build Frontend Dashboard:**
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```
4. **Launch Application:**
   ```bash
   python main.py
   # Or run: .\start_oms_ai.bat
   ```

---

## ☁️ FREE CLOUD DEPLOYMENT // RENDER FREE + RTX 4060

OMS features a hybrid edge-cloud architecture that lets you host the dashboard and cloud metadata relay on **Render Free ($0/mo)** while running all heavy computer vision workloads locally on your **NVIDIA RTX 4060**:

* **Backend Cloud API (Render Web Service)**: `pip install -r requirements-cloud.txt` $\rightarrow$ `uvicorn cloud_api:app --host 0.0.0.0 --port $PORT`
* **Frontend Dashboard (Render Static Site)**: Root `frontend`, `npm install && npm run build`, Publish `out`
* **Local RTX 4060 Engine**: `.\start_oms_ai.bat` with `OMS_CLOUD_API_URL` configured in `.env`

For complete step-by-step instructions, see [`docs/DEPLOY_RENDER_FREE.md`](docs/DEPLOY_RENDER_FREE.md) and [`docs/DEPLOYMENT_ARCHITECTURE.md`](docs/DEPLOYMENT_ARCHITECTURE.md).

---

* **Maintained by:** Prajan77v
* **Project Status:** Active/Operational
* **License:** MIT License
