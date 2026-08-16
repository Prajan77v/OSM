# OMS Deployment Architecture: Free Cloud + Local GPU Tier

## 1. Executive Summary

The **Object Monitoring System (OMS)** employs a hybrid edge-cloud architecture designed for maximum performance, minimal cost ($0/month), and complete offline autonomy:

- **Local AI Engine (Edge Tier)**: Runs on your Windows machine powered by the **NVIDIA GeForce RTX 4060**. Executes all computationally heavy computer vision workloads (YOLOv8 object detection, InsightFace ArcFace biometric facial recognition, ByteTrack tracking, HAAE activity analysis, and direct RTSP/webcam capture).
- **OMS Cloud API (Cloud Hub Tier)**: Deployed on **Render Free Tier** Web Service (512 MB RAM / 0.1 CPU). Acts as a lightweight proxy and live metadata store for events, telemetry, camera status, and active detections without importing heavy ML libraries (no PyTorch, no OpenCV, no CUDA).
- **OMS Dashboard (Presentation Tier)**: Built with **Next.js** and hosted on **Render Static Sites** (free, global CDN). Seamlessly communicates with either the Cloud API or Local AI server via standard REST/JSON and WebSockets.

---

## 2. High-Level Data Flow

```text
                           INTERNET / CLIENTS
                                   │
                                   ▼
                      ┌─────────────────────────┐
                      │    OMS DASHBOARD (UI)   │
                      │    Next.js Static Site  │
                      │    (Render Free CDN)    │
                      └────────────┬────────────┘
                                   │ HTTPS / WSS
                                   ▼
                      ┌─────────────────────────┐
                      │      OMS CLOUD API      │
                      │   Lightweight FastAPI   │
                      │ (Render Free Web Svc)   │
                      │   512 MB RAM / 0.1 CPU  │
                      └────────────┬────────────┘
                                   ▲
                                   │ HTTPS / WSS (OMS_API_KEY Auth)
                                   │ [Or Cloudflare Tunnel]
                                   │
                                   │ ◄─── Heartbeat (5s)
                                   │ ◄─── Live Detections / Telemetry
                                   │ ◄─── Event Logs Batch Sync
                                   │
                      ┌────────────┴────────────┐
                      │    LOCAL OMS AI ENGINE  │
                      │    Windows RTX 4060     │
                      │                         │
                      │  • YOLOv8 (CUDA)        │
                      │  • InsightFace ArcFace  │
                      │  • ByteTrack (Kalman)   │
                      │  • RTSP Video Streams   │
                      │  • Local SQLite DB      │
                      │  • Cloud Sync Hub       │
                      │  • Offline Queue Buffer │
                      └─────────────────────────┘
```

---

## 3. Tier Responsibilities

| Responsibility | Local Engine (RTX 4060) | Cloud API (Render Free) | Dashboard (Static Site) |
| :--- | :---: | :---: | :---: |
| **YOLOv8 Object Detection** | ✅ CUDA Accelerated | ❌ Disabled | ❌ |
| **InsightFace Biometrics** | ✅ CUDA Accelerated | ❌ Disabled | ❌ |
| **Direct RTSP Video Decoding** | ✅ Local LAN | ❌ Prohibited | ❌ |
| **ByteTrack Kalman Smoothing** | ✅ Real-Time | ❌ Disabled | ❌ |
| **Local Database Persistence** | ✅ SQLite / JSON | ❌ Ephemeral Buffer | ❌ |
| **Telemetry & State Ingestion** | ✅ Originator | ✅ Cloud Store | ❌ |
| **Event Broadcast via WebSockets** | ❌ (Pushes to Cloud) | ✅ Global Relay | ❌ |
| **User Interface & Visualizations** | ❌ | ❌ | ✅ HTML5 / CSS3 / React |

---

## 4. Resilience & Offline-First Guarantees

1. **Autonomous Operation**: If Render Free spins down (sleep after 15 min of inactivity) or internet connection is lost:
   - Local AI detection, tracking, face recognition, and alarm triggers continue running at full 60+ FPS on the RTX 4060.
   - New surveillance events are buffered locally in an append-only in-memory & SQLite sync queue.
2. **Exponential Backoff & Reconnection**:
   - The Local Sync Daemon polls the Cloud API with exponential backoff (5s $\rightarrow$ 10s $\rightarrow$ 30s $\rightarrow$ 60s) without spamming logs.
   - When the Cloud API wakes up, all queued events are flushed in a single batch request (`POST /api/cloud/events`).
3. **Bandwidth Optimization**:
   - Raw video is **never** streamed to Render Free. Only JSON metadata (coordinates, labels, confidence scores, telemetry) is synchronized.

---

## 5. Security & Authentication

- **API Secret Key**: All local engine sync endpoints (`/api/cloud/*`) are protected via the `X-API-Key` HTTP header configured with `OMS_API_KEY`.
- **Zero Committed Secrets**: `.env` and `config.yaml` avoid committing tokens to git repository.
- **Cloudflare Tunnel Compatibility**: For remote bidirectional control, a zero-trust Cloudflare Tunnel (`cloudflared`) can securely proxy requests to `http://localhost:8000` without exposing open ports or port forwarding.
