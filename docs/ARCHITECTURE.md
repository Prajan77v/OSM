# 🏛️ OMS Sentinel — System Architecture Specification

This document details the engineering architecture, concurrency designs, and data pipelines of the Object Monitoring System (OMS).

---

## 🏗️ Concurrency Architecture & Thread Isolation

OMS isolates camera acquisition and GUI rendering from deep learning workloads using dedicated thread pools and double-buffer queues. This maintains a steady 30 FPS webcam render rate regardless of heavy AI model compute times.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        MAIN THREAD (Tkinter / GUI)                     │
└────────────────────────────────────▲───────────────────────────────────┘
                                     │
                 Queue (Latest processed frame + detections)
                                     │
┌────────────────────────────────────┴───────────────────────────────────┐
│                      CAMERA THREAD (OpenCV loop)                       │
├─────────────────┬───────────────────────────────────┬──────────────────┤
│  YOLOv8 (CPU)   │    face_pool (ThreadPoolExecutor)  │  haae_pool (TPE) │
│  Object Track   │    DeepFace/SFace Recognition     │  Expression AI   │
└─────────────────┴───────────────────────────────────┴──────────────────┘
```

### Thread Descriptions
1. **Main UI Thread**: Spawns GUI controls, manages the FastAPI server process via a background sub-thread, and flushes frame displays.
2. **Camera Thread (per camera)**: Sequentially captures raw BGR frames, runs object detection models, updates kinematic trackers, and executes the HAAE updates.
3. **`face_pool` Thread Executor**: A dedicated pool (max workers = 4) that takes aligned face crops asynchronously, computes feature vectors using SFace, and queries the database.
4. **`haae_pool` Thread Executor**: A dedicated worker pool (max workers = 2) for running facial expression analytics. Offloads tensorflow/deepface models to prevent recognition delays.

---

## 📊 Core Data Schemas

### 1. Person Metadata (`faces_db.json`)
Located in `logs/faces_db.json`. Tracks registered personnel templates.
```json
{
  "P1": {
    "name": "Prajan",
    "added_at": "2026-06-21 10:49:50",
    "known": true,
    "photo_path": "faces/known/P1.jpg"
  }
}
```

### 2. Events Database (`events.db`)
SQLite database managing alert logs.
* **Schema**:
  - `id`: INTEGER PRIMARY KEY
  - `timestamp`: TEXT (e.g. `2026-06-21 10:52:48`)
  - `event_type`: TEXT (`PERSON_ENTERED`, `PERSON_LEFT`, `ZONE_INTRUSION`, `BEHAVIOR`, `RUNNING`)
  - `camera_name`: TEXT
  - `subject_name`: TEXT
  - `detail`: TEXT

---

## 🛰️ Kinematic Scoring Formulas

The **HAAE Module** calculates real-time activity metrics using bounding-box centroid dynamics:

### 1. Velocity Component (\(V_{score}\))
Given centroid coordinates \(C_t = (x_t, y_t)\) and timestamps \(T_t\), the velocity over a 3-frame window is:
\[\text{Speed} = \frac{1}{N}\sum_{i=t-N}^{t-1} \frac{\sqrt{(x_{i+1}-x_i)^2 + (y_{i+1}-y_i)^2}}{T_{i+1} - T_i}\]
This is normalized against the running speed threshold:
\[V_{score} = \min\left(1.0, \frac{\text{Speed}}{V_{threshold}}\right)\]

### 2. Direction Change Rate (\(D_{score}\))
Pacing is detected by tracking changes in the sign of the motion vector angle. If the sign of the direction vector flips, a direction change timestamp is recorded.
\[D_{score} = \min\left(1.0, \frac{\text{Flips in last 15 seconds}}{10}\right)\]

### 3. Integrated Activity Score
The continuous activity score merges velocity, pacing, and stationary duration:
\[\text{Score} = (V_{score} \times 0.40) + (D_{score} \times 0.30) + (\text{Stillness} \times 0.30)\]
This score is mapped to categories:
* \(\text{Score} \ge 0.75 \land V_{score} \ge 1.0 \implies\) `RUNNING`
* \(0.35 \le \text{Score} < 0.75 \implies\) `ACTIVE`
* \(\text{Score} < 0.35 \implies\) `IDLE`
