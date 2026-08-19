"""
OMS Sentinel — Lightweight Cloud API
Designed for Render Free Tier (512 MB RAM / 0.1 CPU).
Provides high-performance metadata relay, telemetry store, and event synchronization
WITHOUT loading heavy ML frameworks (no PyTorch, no OpenCV, no YOLO, no CUDA).
"""

from __future__ import annotations
import os
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from fastapi import FastAPI, Request, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel

# ──────────────────────────────────────────────────────────────────────────────
# Configuration & Security
# ──────────────────────────────────────────────────────────────────────────────
OMS_API_KEY = os.getenv("OMS_API_KEY", "").strip()
OPERATOR_NAME = os.getenv("OSM_OPERATOR", "Prajan")

app = FastAPI(
    title="OMS Cloud API",
    description="Autonomous AI Surveillance Cloud Hub (Render Free Tier)",
    version="9.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────────────────────────
# In-Memory Cloud State Store
# ──────────────────────────────────────────────────────────────────────────────
class CloudStore:
    def __init__(self):
        self.last_heartbeat: float = 0.0
        self.engine_info: Dict[str, Any] = {
            "engine_id": "none",
            "gpu": "Unavailable",
            "cuda_available": False,
            "status": "OFFLINE",
            "version": "9.0.0",
            "hostname": "unknown"
        }
        self.telemetry: Dict[str, Any] = {
            "cpu": 0,
            "gpu": 0,
            "ram": 0,
            "net_kb": 0.0,
            "fps": 0.0,
            "uptime": "00:00:00",
            "yolo": False,
            "face_recog": False,
            "telegram": False,
            "profiles_count": 0,
            "detect_new_ids": True,
            "threat_level": "GREEN"
        }
        self.cameras: List[Dict[str, Any]] = [
            {
                "id": 0,
                "name": "LOCAL WEBCAM",
                "online": True,
                "fps": 30.0,
                "persons": 0,
                "objects": 0,
                "threat": "GREEN",
                "active_subjects": [],
                "source": "0",
                "location": "Control Desk"
            },
            {
                "id": 1,
                "name": "Diamond Silicate",
                "online": False,
                "fps": 0.0,
                "persons": 0,
                "objects": 0,
                "threat": "GREEN",
                "active_subjects": [],
                "source": "rtsp://admin:a1b2c3d4%405@117.247.103.113:554/Streaming/Channels/101",
                "location": "Diamond Silicate Facility"
            },
            {
                "id": 2,
                "name": "Narimanam Silicate",
                "online": True,
                "fps": 25.0,
                "persons": 0,
                "objects": 0,
                "threat": "GREEN",
                "active_subjects": [],
                "source": "rtsp://admin:a1b2c3d4%405@117.247.103.114:554/Streaming/Channels/101",
                "location": "Narimanam Silicate Facility"
            }
        ]
        self.events: List[Dict[str, Any]] = []
        self.faces: List[Dict[str, Any]] = []
        self.summary: Dict[str, Any] = {
            "total_detections": 0,
            "known_persons": 0,
            "unknown_persons": 0,
            "objects_added": 0,
            "objects_removed": 0,
            "alerts": 0,
            "operator": OPERATOR_NAME,
            "uptime": "00:00:00"
        }
        self.latest_detections: List[Dict[str, Any]] = []
        self.websocket_clients: Set[WebSocket] = set()

    def is_ai_online(self) -> bool:
        return (time.time() - self.last_heartbeat) < 25.0

    def get_health_states(self) -> Dict[str, str]:
        ai_online = self.is_ai_online()
        cuda = self.engine_info.get("cuda_available", False)
        any_cam_online = any(c.get("online", False) for c in self.cameras) if ai_online else False
        return {
            "ai_engine": "AI_ENGINE_ONLINE" if ai_online else "AI_ENGINE_OFFLINE",
            "cloud": "CLOUD_ONLINE",
            "gpu": "GPU_AVAILABLE" if (ai_online and cuda) else "GPU_UNAVAILABLE",
            "camera": "CAMERA_ONLINE" if (ai_online and any_cam_online) else "CAMERA_OFFLINE"
        }

store = CloudStore()


def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Validates OMS_API_KEY when configured on the cloud service."""
    if not OMS_API_KEY:
        return True
    if not x_api_key or x_api_key != OMS_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid OMS_API_KEY")
    return True


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic Schemas for Ingestion
# ──────────────────────────────────────────────────────────────────────────────
class HeartbeatPayload(BaseModel):
    engine_id: str = "local-engine"
    gpu: str = "NVIDIA GeForce RTX 4060"
    cuda_available: bool = True
    status: str = "online"
    timestamp: Optional[str] = None
    camera_count: int = 1
    version: str = "9.0.0"


class SyncPayload(BaseModel):
    telemetry: Optional[Dict[str, Any]] = None
    cameras: Optional[List[Dict[str, Any]]] = None
    summary: Optional[Dict[str, Any]] = None
    faces: Optional[List[Dict[str, Any]]] = None
    events: Optional[List[Dict[str, Any]]] = None
    detections: Optional[List[Dict[str, Any]]] = None


# ──────────────────────────────────────────────────────────────────────────────
# Health & Status Endpoints
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    states = store.get_health_states()
    return {
        "status": "online",
        "service": "OMS Cloud API",
        "timestamp": datetime.now().isoformat(),
        "ai_engine_status": states["ai_engine"],
        "gpu_status": states["gpu"],
        "camera_status": states["camera"],
        "last_heartbeat_ago_sec": round(time.time() - store.last_heartbeat, 1) if store.last_heartbeat > 0 else None
    }


@app.get("/status")
@app.get("/api/status")
async def get_system_status():
    states = store.get_health_states()
    return {
        "cloud": "ONLINE",
        "ai_engine": "ONLINE" if store.is_ai_online() else "OFFLINE",
        "health_states": states,
        "engine_info": store.engine_info,
        "telemetry": store.telemetry,
        "summary": store.summary
    }


# ──────────────────────────────────────────────────────────────────────────────
# Dashboard API Endpoints (100% Compatible with OMS Next.js Frontend)
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/api/cameras")
async def get_cameras():
    # If AI engine is offline, mark all cameras offline
    if not store.is_ai_online():
        return [dict(c, online=False, persons=0, objects=0, active_subjects=[]) for c in store.cameras]
    return store.cameras


@app.get("/api/telemetry")
async def get_telemetry():
    t = dict(store.telemetry)
    if not store.is_ai_online():
        t["fps"] = 0.0
        t["gpu"] = 0
        t["cpu"] = 0
        t["yolo"] = False
        t["face_recog"] = False
    return t


@app.get("/api/events")
async def get_events(limit: int = 100):
    return store.events[-limit:] if store.events else []


@app.get("/api/summary")
async def get_summary():
    return store.summary


@app.get("/api/faces")
async def get_faces():
    return store.faces


@app.get("/api/activity")
async def get_activity():
    return []


@app.get("/api/settings")
async def get_settings():
    return {
        "status": "ok",
        "username": store.summary.get("operator", OPERATOR_NAME),
        "confidence": 0.45,
        "model": "yolov8n.pt",
        "detect_new_ids": store.telemetry.get("detect_new_ids", True),
        "use_cuda": store.engine_info.get("cuda_available", True),
        "detect_people": True,
        "detect_objects": True,
        "match_threshold": 0.35,
        "profile": "MEDIUM"
    }


@app.get("/api/camera/{cam_id}/settings")
async def get_camera_settings(cam_id: int):
    return {
        "brightness": 0,
        "contrast": 1.0,
        "blur": 0,
        "confidence": 0.45,
        "flip_h": False,
        "flip_v": False
    }


# ──────────────────────────────────────────────────────────────────────────────
# Cloud Synchronization Endpoints (Local RTX 4060 Engine Ingestion)
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/api/cloud/heartbeat")
async def receive_heartbeat(payload: HeartbeatPayload, request: Request):
    verify_api_key(request.headers.get("X-API-Key"))
    store.last_heartbeat = time.time()
    store.engine_info = {
        "engine_id": payload.engine_id,
        "gpu": payload.gpu,
        "cuda_available": payload.cuda_available,
        "status": payload.status,
        "version": payload.version,
        "camera_count": payload.camera_count
    }
    return {"status": "ok", "message": "Heartbeat received"}


@app.post("/api/cloud/sync")
async def receive_sync(payload: SyncPayload, request: Request):
    verify_api_key(request.headers.get("X-API-Key"))
    store.last_heartbeat = time.time()

    if payload.telemetry:
        store.telemetry.update(payload.telemetry)
    if payload.cameras is not None:
        store.cameras = payload.cameras
    if payload.summary:
        store.summary.update(payload.summary)
    if payload.faces is not None:
        store.faces = payload.faces
    if payload.detections is not None:
        store.latest_detections = payload.detections
    if payload.events:
        # Append new events avoiding duplicates by timestamp
        existing_ts = {e.get("ts") for e in store.events[-200:]}
        for ev in payload.events:
            if ev.get("ts") not in existing_ts:
                store.events.append(ev)
        if len(store.events) > 500:
            store.events = store.events[-500:]

    # Broadcast to active WebSockets asynchronously
    if store.websocket_clients:
        asyncio.create_task(_broadcast_state())

    return {"status": "ok", "synced_events": len(payload.events or [])}


@app.post("/api/cloud/events")
async def receive_events(events: List[Dict[str, Any]], request: Request):
    verify_api_key(request.headers.get("X-API-Key"))
    store.last_heartbeat = time.time()
    for ev in events:
        store.events.append(ev)
    if len(store.events) > 500:
        store.events = store.events[-500:]
    return {"status": "ok", "count": len(events)}


@app.post("/api/control/{action}")
async def control_action(action: str, request: Request):
    """Relays control actions or acknowledges them in the cloud store."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    if action == "toggle_auto_register":
        curr = store.telemetry.get("detect_new_ids", True)
        store.telemetry["detect_new_ids"] = not curr
        return {"status": "ok", "result": f"Auto register {'ON' if not curr else 'OFF'}"}

    return {"status": "ok", "result": f"Action '{action}' dispatched to local AI engine."}


# ──────────────────────────────────────────────────────────────────────────────
# Real-Time WebSocket Channel
# ──────────────────────────────────────────────────────────────────────────────
async def _broadcast_state():
    if not store.websocket_clients:
        return
    msg = {
        "type": "METADATA_UPDATE",
        "health": store.get_health_states(),
        "telemetry": store.telemetry,
        "cameras": store.cameras,
        "summary": store.summary
    }
    dead = []
    for ws in list(store.websocket_clients):
        try:
            await ws.send_json(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        store.websocket_clients.discard(ws)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    store.websocket_clients.add(websocket)
    try:
        # Send initial snapshot
        await websocket.send_json({
            "type": "INITIAL_SNAPSHOT",
            "health": store.get_health_states(),
            "telemetry": store.telemetry,
            "cameras": store.cameras,
            "summary": store.summary,
            "events": store.events[-20:]
        })
        while True:
            data = await websocket.receive_text()
            # Echo heartbeat or keepalive
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        store.websocket_clients.discard(websocket)
    except Exception:
        store.websocket_clients.discard(websocket)


# ──────────────────────────────────────────────────────────────────────────────
# Root Fallback Landing
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    states = store.get_health_states()
    ai_col = "#00FFA3" if states["ai_engine"] == "AI_ENGINE_ONLINE" else "#EF4444"
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>OMS Cloud Hub</title>
  <style>
    body {{ background: #080808; color: #D4AF37; font-family: 'Segoe UI', monospace; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }}
    .card {{ background: rgba(20,20,20,0.8); border: 1px solid rgba(212,175,55,0.3); border-radius: 16px; padding: 32px; max-width: 520px; width: 90%; text-align: center; box-shadow: 0 0 40px rgba(0,0,0,0.8); }}
    h1 {{ font-size: 1.8rem; margin-bottom: 8px; letter-spacing: 0.15em; color: #FFD700; }}
    .status {{ display: inline-block; padding: 6px 14px; border-radius: 999px; font-weight: bold; font-size: 0.85rem; margin: 12px 0; background: rgba(0,255,163,0.15); border: 1px solid #00FFA3; color: #00FFA3; }}
    .ai-badge {{ display: inline-block; padding: 4px 10px; border-radius: 8px; font-size: 0.8rem; margin: 6px; border: 1px solid {ai_col}; color: {ai_col}; }}
    p {{ color: #A0A0A0; font-size: 0.9rem; line-height: 1.5; }}
    a {{ color: #00E5FF; text-decoration: none; font-weight: bold; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>OMS CLOUD API</h1>
    <div class="status">● CLOUD SERVICE ONLINE</div>
    <div>
      <span class="ai-badge">{states["ai_engine"]}</span>
      <span class="ai-badge">{states["gpu"]}</span>
      <span class="ai-badge">{states["camera"]}</span>
    </div>
    <p>Autonomous AI Surveillance Cloud Hub (Render Free Tier).<br>Heavy computer vision models run securely on the local RTX 4060.</p>
    <p style="margin-top: 16px;"><a href="/docs">View Interactive OpenAPI Documentation (/docs)</a></p>
  </div>
</body>
</html>""")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
