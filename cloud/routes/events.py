"""
OMS Cloud — Surveillance Events Ingestion, Querying, and Alert Routing
"""

import json
import os
import requests
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from cloud.database.session import get_db
from cloud.database.models import SurveillanceEvent, NotificationLog
from cloud.auth.security import verify_edge_token

router = APIRouter(prefix="/api", tags=["Events & Alerts"])
log = logging.getLogger("OMS.CloudEvents")

# Cloud-level Telegram Configuration
TG_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
TG_SEVERITIES = {"high", "critical"}


def _send_telegram_alert(event_type: str, camera_id: str, severity: str, confidence: float, location: str, db: Session):
    """Dispatches Telegram notifications for high and critical surveillance incidents."""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return

    msg = (
        f"🚨 <b>OMS SENTINEL ALERT</b>\n"
        f"<b>Event:</b> {event_type.upper().replace('_', ' ')}\n"
        f"<b>Severity:</b> {severity.upper()}\n"
        f"<b>Camera:</b> {camera_id}\n"
        f"<b>Confidence:</b> {confidence * 100:.1f}%\n"
        f"<b>Location:</b> {location}\n"
        f"<b>Time (UTC):</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
    )

    try:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={
            "chat_id": TG_CHAT_ID,
            "text": msg,
            "parse_mode": "HTML"
        }, timeout=4.0)

        status_text = "SENT" if resp.status_code == 200 else f"FAILED_{resp.status_code}"
        notif = NotificationLog(
            channel="telegram",
            target=TG_CHAT_ID,
            message_snippet=msg[:200],
            status=status_text
        )
        db.add(notif)
    except Exception as e:
        log.warning(f"[TELEGRAM] Cloud dispatch error: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic Schemas
# ──────────────────────────────────────────────────────────────────────────────
class EventPayload(BaseModel):
    event_id: str
    camera_id: str
    event_type: str
    severity: str = "medium"
    confidence: float = 1.0
    timestamp: Optional[str] = None
    track_ids: Optional[List[int]] = []
    location: Optional[str] = "Monitored Sector"
    snapshot_base64: Optional[str] = None
    clip_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}


class BatchEventPayload(BaseModel):
    engine_id: str = "edge-node-1"
    events: List[EventPayload]


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────
@router.post("/events", dependencies=[Depends(verify_edge_token)])
def ingest_event(payload: EventPayload, db: Session = Depends(get_db)):
    """Ingests a single verified surveillance event from an Edge Node."""
    now_utc = datetime.now(timezone.utc)
    existing = db.query(SurveillanceEvent).filter(SurveillanceEvent.event_id == payload.event_id).first()
    if existing:
        return {"status": "ok", "message": "Event already registered", "event_id": payload.event_id}

    ts_dt = now_utc
    if payload.timestamp:
        try:
            ts_dt = datetime.fromisoformat(payload.timestamp.replace("Z", "+00:00"))
        except Exception:
            pass

    event = SurveillanceEvent(
        event_id=payload.event_id,
        camera_id=payload.camera_id,
        event_type=payload.event_type,
        severity=payload.severity.lower(),
        confidence=payload.confidence,
        timestamp=ts_dt,
        track_ids_json=json.dumps(payload.track_ids or []),
        location=payload.location or "Monitored Sector",
        snapshot_base64=payload.snapshot_base64,
        clip_url=payload.clip_url,
        metadata_json=json.dumps(payload.metadata or {})
    )
    db.add(event)

    # Trigger critical notification if configured
    if payload.severity.lower() in TG_SEVERITIES:
        _send_telegram_alert(payload.event_type, payload.camera_id, payload.severity, payload.confidence, payload.location or "Sector", db)

    db.commit()
    return {"status": "ok", "event_id": payload.event_id}


@router.post("/events/batch", dependencies=[Depends(verify_edge_token)])
def ingest_batch_events(payload: BatchEventPayload, db: Session = Depends(get_db)):
    """Ingests a batch of events from edge persistent queue."""
    inserted = 0
    now_utc = datetime.now(timezone.utc)

    for item in payload.events:
        existing = db.query(SurveillanceEvent).filter(SurveillanceEvent.event_id == item.event_id).first()
        if not existing:
            ts_dt = now_utc
            if item.timestamp:
                try:
                    ts_dt = datetime.fromisoformat(item.timestamp.replace("Z", "+00:00"))
                except Exception:
                    pass

            event = SurveillanceEvent(
                event_id=item.event_id,
                edge_agent_id=payload.engine_id,
                camera_id=item.camera_id,
                event_type=item.event_type,
                severity=item.severity.lower(),
                confidence=item.confidence,
                timestamp=ts_dt,
                track_ids_json=json.dumps(item.track_ids or []),
                location=item.location or "Monitored Sector",
                snapshot_base64=item.snapshot_base64,
                clip_url=item.clip_url,
                metadata_json=json.dumps(item.metadata or {})
            )
            db.add(event)
            inserted += 1

            if item.severity.lower() in TG_SEVERITIES:
                _send_telegram_alert(item.event_type, item.camera_id, item.severity, item.confidence, item.location or "Sector", db)

    db.commit()
    return {"status": "ok", "inserted_count": inserted}


@router.get("/events")
def list_events(
    severity: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    camera_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Queries historical surveillance events with optional filters."""
    query = db.query(SurveillanceEvent)

    if severity:
        query = query.filter(SurveillanceEvent.severity == severity.lower())
    if event_type:
        query = query.filter(SurveillanceEvent.event_type == event_type)
    if camera_id:
        query = query.filter(SurveillanceEvent.camera_id == camera_id)

    total_count = query.count()
    events = query.order_by(desc(SurveillanceEvent.timestamp)).offset(offset).limit(limit).all()

    results = []
    for e in events:
        results.append({
            "event_id": e.event_id,
            "camera_id": e.camera_id,
            "event_type": e.event_type,
            "severity": e.severity,
            "confidence": e.confidence,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "track_ids": json.loads(e.track_ids_json) if e.track_ids_json else [],
            "location": e.location,
            "has_snapshot": bool(e.snapshot_base64),
            "clip_url": e.clip_url,
            "metadata": json.loads(e.metadata_json) if e.metadata_json else {}
        })

    return {"total": total_count, "limit": limit, "offset": offset, "events": results}


@router.get("/events/{event_id}")
def get_event_detail(event_id: str, db: Session = Depends(get_db)):
    """Retrieves full details of a specific event including snapshot."""
    event = db.query(SurveillanceEvent).filter(SurveillanceEvent.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return {
        "event_id": event.event_id,
        "camera_id": event.camera_id,
        "event_type": event.event_type,
        "severity": event.severity,
        "confidence": event.confidence,
        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
        "track_ids": json.loads(event.track_ids_json) if event.track_ids_json else [],
        "location": event.location,
        "snapshot_base64": event.snapshot_base64,
        "clip_url": event.clip_url,
        "metadata": json.loads(event.metadata_json) if event.metadata_json else {}
    }
