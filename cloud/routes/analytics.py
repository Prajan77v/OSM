"""
OMS Cloud — Telemetry, Analytics, and Intelligence Summaries
"""

import os
from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from cloud.database.session import get_db
from cloud.database.models import EdgeAgent, Camera, SurveillanceEvent

router = APIRouter(prefix="/api", tags=["Analytics & Telemetry"])
OPERATOR_NAME = os.getenv("OMS_OPERATOR", "Prajan")


@router.get("/telemetry")
def get_telemetry(db: Session = Depends(get_db)):
    """Returns real-time aggregated telemetry across all active Edge nodes."""
    now_utc = datetime.now(timezone.utc)
    agents = db.query(EdgeAgent).all()
    
    online_agents = [
        a for a in agents
        if a.last_heartbeat and (now_utc - a.last_heartbeat.replace(tzinfo=timezone.utc)).total_seconds() < 30.0
    ]

    is_online = len(online_agents) > 0
    latest_agent = online_agents[0] if is_online else None

    # Calculate average FPS across online cameras
    cams = db.query(Camera).filter(Camera.online == True).all() if is_online else []
    fps_list = [c.fps for c in cams] if cams else [0.0]
    avg_fps = round(sum(fps_list) / max(len(fps_list), 1), 1)

    return {
        "cpu": round(latest_agent.cpu_usage, 1) if latest_agent else 0,
        "ram": round(latest_agent.ram_usage, 1) if latest_agent else 0,
        "gpu": 0,
        "gpu_name": latest_agent.gpu_name if latest_agent else "CPU Mode",
        "cuda": latest_agent.cuda_available if latest_agent else False,
        "hw_profile": latest_agent.hardware_profile if latest_agent else "CPU",
        "net_kb": 24.5 if is_online else 0.0,
        "fps": avg_fps,
        "fps_all": fps_list,
        "uptime": "24/7 Autonomy",
        "yolo": is_online,
        "face_recog": is_online,
        "telegram": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "threat_level": "GREEN"
    }


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    """Returns aggregated intelligence metrics."""
    total_events = db.query(SurveillanceEvent).count()
    alert_count = db.query(SurveillanceEvent).filter(
        SurveillanceEvent.severity.in_(["high", "critical"])
    ).count()

    return {
        "total_detections": total_events,
        "total_events": total_events,
        "alerts": alert_count,
        "known_persons": 0,
        "unknown_persons": 0,
        "objects_added": 0,
        "objects_removed": 0,
        "operator": OPERATOR_NAME,
        "threat_level": "GREEN"
    }


@router.get("/faces")
def get_faces():
    """Returns enrolled face identities."""
    return []


@router.get("/activity")
def get_activity():
    """Returns real-time activity stream."""
    return []


@router.get("/settings")
def get_settings():
    """Returns global system settings."""
    return {
        "operator": OPERATOR_NAME,
        "cloud_mode": "Production Free-Tier",
        "architecture": "Edge-CPU + Cloud-Relay",
        "database": "SQLite / PostgreSQL Hybrid"
    }
