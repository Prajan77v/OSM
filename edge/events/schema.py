"""
OMS Edge — Unified Production Event Schema
All timestamps are generated in UTC ISO 8601 format.
"""

from __future__ import annotations
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


@dataclass
class OMSEvent:
    event_type: str
    camera_id: str
    severity: str = "medium"             # info, low, medium, high, critical
    confidence: float = 1.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    track_ids: List[int] = field(default_factory=list)
    location: str = "Monitored Sector"
    snapshot_base64: Optional[str] = None
    clip_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    synced: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OMSEvent:
        return cls(
            event_id=data.get("event_id", f"evt_{uuid.uuid4().hex[:12]}"),
            camera_id=str(data.get("camera_id", "CAM_00")),
            event_type=data.get("event_type", "generic_event"),
            severity=data.get("severity", "medium"),
            confidence=float(data.get("confidence", 1.0)),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            track_ids=data.get("track_ids", []),
            location=data.get("location", "Monitored Sector"),
            snapshot_base64=data.get("snapshot_base64"),
            clip_url=data.get("clip_url"),
            metadata=data.get("metadata", {}),
            synced=bool(data.get("synced", False)),
        )
