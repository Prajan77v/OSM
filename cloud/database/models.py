"""
OMS Cloud — Database Models
Supports both SQLite (local/Render disk) and PostgreSQL (Render Managed DB).
"""

import json
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class EdgeAgent(Base):
    """Represents an active or registered edge computing machine."""
    __tablename__ = "edge_agents"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), default="OMS-Edge-Node")
    token_hash = Column(String(128), nullable=True)
    hostname = Column(String(128), nullable=True)
    ip_address = Column(String(64), nullable=True)
    status = Column(String(32), default="OFFLINE")     # ONLINE, OFFLINE, DEGRADED
    hardware_profile = Column(String(32), default="CPU")
    gpu_name = Column(String(128), default="CPU Mode")
    cuda_available = Column(Boolean, default=False)
    cpu_usage = Column(Float, default=0.0)
    ram_usage = Column(Float, default=0.0)
    version = Column(String(32), default="9.0.0")
    last_heartbeat = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    cameras = relationship("Camera", back_populates="edge_agent", cascade="all, delete-orphan")
    events = relationship("SurveillanceEvent", back_populates="edge_agent", cascade="all, delete-orphan")


class Camera(Base):
    """Metadata and live status of cameras connected via Edge Nodes."""
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cam_index = Column(Integer, default=0)
    edge_agent_id = Column(String(64), ForeignKey("edge_agents.id"), nullable=True)
    name = Column(String(128), default="Camera Feed")
    location = Column(String(128), default="Main Sector")
    source_mask = Column(String(256), default="MASKED") # Never store clear-text RTSP passwords
    online = Column(Boolean, default=False)
    fps = Column(Float, default=0.0)
    persons_count = Column(Integer, default=0)
    objects_count = Column(Integer, default=0)
    threat_level = Column(String(32), default="GREEN")
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    edge_agent = relationship("EdgeAgent", back_populates="cameras")

    __table_args__ = (
        Index("idx_camera_edge", "edge_agent_id", "cam_index"),
    )


class SurveillanceEvent(Base):
    """Production event record transmitted from Edge Agents."""
    __tablename__ = "surveillance_events"

    event_id = Column(String(64), primary_key=True)
    edge_agent_id = Column(String(64), ForeignKey("edge_agents.id"), nullable=True)
    camera_id = Column(String(64), nullable=False)
    event_type = Column(String(64), nullable=False)
    severity = Column(String(32), default="medium")     # info, low, medium, high, critical
    confidence = Column(Float, default=1.0)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    track_ids_json = Column(Text, default="[]")
    location = Column(String(128), default="Monitored Sector")
    snapshot_base64 = Column(Text, nullable=True)
    clip_url = Column(String(512), nullable=True)
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    edge_agent = relationship("EdgeAgent", back_populates="events")

    __table_args__ = (
        Index("idx_event_type_ts", "event_type", "timestamp"),
        Index("idx_event_camera", "camera_id", "timestamp"),
    )


class NotificationLog(Base):
    """Audit log of Telegram and webhook alerts dispatched to administrators."""
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel = Column(String(32), default="telegram")
    event_id = Column(String(64), nullable=True)
    target = Column(String(128), nullable=True)
    message_snippet = Column(Text, nullable=True)
    status = Column(String(32), default="SENT")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
