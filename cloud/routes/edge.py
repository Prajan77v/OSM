"""
OMS Cloud — Edge Management & Synchronization Routes
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from cloud.database.session import get_db
from cloud.database.models import EdgeAgent, Camera, SurveillanceEvent
from cloud.auth.security import verify_edge_token, mask_rtsp_url

router = APIRouter(prefix="/api", tags=["Edge Management"])


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic Schemas
# ──────────────────────────────────────────────────────────────────────────────
class HeartbeatRequest(BaseModel):
    engine_id: str = "edge-node-1"
    name: Optional[str] = "OMS-Edge-Node"
    gpu: str = "CPU Mode"
    cuda_available: bool = False
    status: str = "ONLINE"
    hardware_profile: str = "CPU"
    cpu: Optional[float] = 0.0
    ram: Optional[float] = 0.0
    version: str = "9.0.0"
    timestamp: Optional[str] = None


class CameraMeta(BaseModel):
    id: int
    name: str = "Camera"
    location: str = "Main Sector"
    online: bool = False
    fps: float = 0.0
    persons: int = 0
    objects: int = 0
    threat: str = "GREEN"
    source: Optional[str] = None
    active_subjects: Optional[List[Any]] = []


class SyncRequest(BaseModel):
    engine_id: str = "edge-node-1"
    telemetry: Optional[Dict[str, Any]] = None
    cameras: Optional[List[CameraMeta]] = None
    summary: Optional[Dict[str, Any]] = None
    faces: Optional[List[Dict[str, Any]]] = None
    events: Optional[List[Dict[str, Any]]] = None


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────
@router.post("/edge/heartbeat", dependencies=[Depends(verify_edge_token)])
@router.post("/cloud/heartbeat", dependencies=[Depends(verify_edge_token)])
def receive_heartbeat(payload: HeartbeatRequest, db: Session = Depends(get_db)):
    """Ingests lightweight health ping from Edge Node and updates database."""
    now_utc = datetime.now(timezone.utc)
    agent = db.query(EdgeAgent).filter(EdgeAgent.id == payload.engine_id).first()

    if not agent:
        agent = EdgeAgent(
            id=payload.engine_id,
            name=payload.name or "OMS-Edge-Node",
            gpu_name=payload.gpu,
            cuda_available=payload.cuda_available,
            status=payload.status.upper(),
            hardware_profile=payload.hardware_profile,
            cpu_usage=payload.cpu or 0.0,
            ram_usage=payload.ram or 0.0,
            version=payload.version,
            last_heartbeat=now_utc
        )
        db.add(agent)
    else:
        agent.gpu_name = payload.gpu
        agent.cuda_available = payload.cuda_available
        agent.status = payload.status.upper()
        agent.hardware_profile = payload.hardware_profile
        if payload.cpu is not None:
            agent.cpu_usage = payload.cpu
        if payload.ram is not None:
            agent.ram_usage = payload.ram
        agent.version = payload.version
        agent.last_heartbeat = now_utc

    db.commit()
    return {"status": "ok", "message": "Heartbeat recorded", "server_time": now_utc.isoformat()}


@router.post("/edge/sync", dependencies=[Depends(verify_edge_token)])
@router.post("/cloud/sync", dependencies=[Depends(verify_edge_token)])
def receive_sync(payload: SyncRequest, db: Session = Depends(get_db)):
    """Receives comprehensive edge sync payload with telemetry, cameras, and events."""
    now_utc = datetime.now(timezone.utc)
    agent_id = payload.engine_id

    # 1. Update Edge Agent
    agent = db.query(EdgeAgent).filter(EdgeAgent.id == agent_id).first()
    t = payload.telemetry or {}
    if not agent:
        agent = EdgeAgent(
            id=agent_id,
            status="ONLINE",
            cpu_usage=float(t.get("cpu", 0.0)),
            ram_usage=float(t.get("ram", 0.0)),
            gpu_name=str(t.get("gpu_name", "CPU Mode")),
            cuda_available=bool(t.get("cuda", False)),
            last_heartbeat=now_utc
        )
        db.add(agent)
    else:
        agent.status = "ONLINE"
        agent.cpu_usage = float(t.get("cpu", agent.cpu_usage))
        agent.ram_usage = float(t.get("ram", agent.ram_usage))
        agent.last_heartbeat = now_utc

    # 2. Update Cameras
    if payload.cameras:
        for c in payload.cameras:
            cam_record = db.query(Camera).filter(
                Camera.edge_agent_id == agent_id,
                Camera.cam_index == c.id
            ).first()

            masked_source = mask_rtsp_url(c.source or "")
            if not cam_record:
                cam_record = Camera(
                    cam_index=c.id,
                    edge_agent_id=agent_id,
                    name=c.name,
                    location=c.location,
                    source_mask=masked_source,
                    online=c.online,
                    fps=c.fps,
                    persons_count=c.persons,
                    objects_count=c.objects,
                    threat_level=c.threat,
                    last_seen=now_utc
                )
                db.add(cam_record)
            else:
                cam_record.name = c.name
                cam_record.location = c.location
                cam_record.source_mask = masked_source
                cam_record.online = c.online
                cam_record.fps = c.fps
                cam_record.persons_count = c.persons
                cam_record.objects_count = c.objects
                cam_record.threat_level = c.threat
                cam_record.last_seen = now_utc

    # 3. Store Batch Events (if transmitted in sync payload)
    synced_count = 0
    if payload.events:
        for evt in payload.events:
            evt_id = evt.get("event_id")
            if not evt_id:
                continue
            existing = db.query(SurveillanceEvent).filter(SurveillanceEvent.event_id == evt_id).first()
            if not existing:
                ts_str = evt.get("timestamp")
                try:
                    ts_dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00")) if ts_str else now_utc
                except Exception:
                    ts_dt = now_utc

                new_event = SurveillanceEvent(
                    event_id=evt_id,
                    edge_agent_id=agent_id,
                    camera_id=str(evt.get("camera_id", "CAM_00")),
                    event_type=str(evt.get("event_type", "event")),
                    severity=str(evt.get("severity", "medium")),
                    confidence=float(evt.get("confidence", 1.0)),
                    timestamp=ts_dt,
                    track_ids_json=json.dumps(evt.get("track_ids", [])),
                    location=str(evt.get("location", "Monitored Sector")),
                    snapshot_base64=evt.get("snapshot_base64"),
                    clip_url=evt.get("clip_url"),
                    metadata_json=json.dumps(evt.get("metadata", {}))
                )
                db.add(new_event)
                synced_count += 1

    db.commit()
    return {"status": "ok", "synced_events": synced_count, "timestamp": now_utc.isoformat()}


@router.get("/system/health")
def get_system_health(db: Session = Depends(get_db)):
    """Returns real-time health metrics of all Edge Agents and Cloud DB."""
    now_utc = datetime.now(timezone.utc)
    agents = db.query(EdgeAgent).all()
    
    # Active if heartbeat received within last 30 seconds
    online_agents = [
        a for a in agents
        if a.last_heartbeat and (now_utc - a.last_heartbeat.replace(tzinfo=timezone.utc)).total_seconds() < 30.0
    ]

    is_ai_online = len(online_agents) > 0
    any_cuda = any(a.cuda_available for a in online_agents)
    total_cameras = db.query(Camera).count()
    online_cameras = db.query(Camera).filter(Camera.online == True).count() if is_ai_online else 0

    return {
        "status": "HEALTHY",
        "cloud_status": "ONLINE",
        "ai_engine_status": "AI_ENGINE_ONLINE" if is_ai_online else "AI_ENGINE_OFFLINE",
        "edge_nodes_online": len(online_agents),
        "edge_nodes_total": len(agents),
        "cuda_acceleration": "GPU_AVAILABLE" if (is_ai_online and any_cuda) else "CPU_ONLY",
        "cameras_online": online_cameras,
        "cameras_total": total_cameras,
        "server_time": now_utc.isoformat()
    }
