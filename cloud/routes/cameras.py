"""
OMS Cloud — Camera Feeds & Channel Management Routes
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from cloud.database.session import get_db
from cloud.database.models import Camera, EdgeAgent
from cloud.auth.security import verify_edge_token, mask_rtsp_url

router = APIRouter(prefix="/api/cameras", tags=["Cameras"])


class CameraRegisterPayload(BaseModel):
    cam_index: int
    name: str = "Camera"
    location: str = "Main Sector"
    source: Optional[str] = "0"
    edge_agent_id: Optional[str] = "edge-node-1"


@router.get("")
def list_cameras(db: Session = Depends(get_db)):
    """
    Returns list of all active cameras.
    If the parent Edge Agent is offline (>30s), marks online=False.
    """
    now_utc = datetime.now(timezone.utc)
    agents = {a.id: a for a in db.query(EdgeAgent).all()}
    cams = db.query(Camera).order_by(Camera.cam_index).all()

    if not cams:
        # Fallback default seed if database is brand new
        return [
            {
                "id": 0,
                "name": "LOCAL WEBCAM",
                "location": "Control Desk",
                "online": True,
                "fps": 30.0,
                "persons": 0,
                "objects": 0,
                "threat": "GREEN",
                "source": "0"
            },
            {
                "id": 1,
                "name": "Diamond Silicate",
                "location": "Diamond Silicate Facility",
                "online": False,
                "fps": 0.0,
                "persons": 0,
                "objects": 0,
                "threat": "GREEN",
                "source": "rtsp://admin:***@117.247.103.113:554/Streaming/Channels/101"
            },
            {
                "id": 2,
                "name": "Narimanam Silicate",
                "location": "Narimanam Silicate Facility",
                "online": True,
                "fps": 25.0,
                "persons": 0,
                "objects": 0,
                "threat": "GREEN",
                "source": "rtsp://admin:***@117.247.103.114:554/Streaming/Channels/101"
            }
        ]

    results = []
    for c in cams:
        parent_agent = agents.get(c.edge_agent_id)
        is_edge_online = False
        if parent_agent and parent_agent.last_heartbeat:
            is_edge_online = (now_utc - parent_agent.last_heartbeat.replace(tzinfo=timezone.utc)).total_seconds() < 30.0

        effective_online = bool(c.online and is_edge_online)
        results.append({
            "id": c.cam_index,
            "name": c.name,
            "location": c.location,
            "online": effective_online,
            "fps": c.fps if effective_online else 0.0,
            "persons": c.persons_count if effective_online else 0,
            "objects": c.objects_count if effective_online else 0,
            "threat": c.threat_level if effective_online else "GREEN",
            "source": c.source_mask or "MASKED"
        })

    return results


@router.post("/register", dependencies=[Depends(verify_edge_token)])
def register_camera(payload: CameraRegisterPayload, db: Session = Depends(get_db)):
    """Registers or updates a camera feed from an Edge Node."""
    now_utc = datetime.now(timezone.utc)
    cam = db.query(Camera).filter(
        Camera.edge_agent_id == payload.edge_agent_id,
        Camera.cam_index == payload.cam_index
    ).first()

    masked = mask_rtsp_url(payload.source or "")
    if not cam:
        cam = Camera(
            cam_index=payload.cam_index,
            edge_agent_id=payload.edge_agent_id,
            name=payload.name,
            location=payload.location,
            source_mask=masked,
            online=True,
            last_seen=now_utc
        )
        db.add(cam)
    else:
        cam.name = payload.name
        cam.location = payload.location
        cam.source_mask = masked
        cam.online = True
        cam.last_seen = now_utc

    db.commit()
    return {"status": "ok", "message": f"Camera {payload.name} registered"}
