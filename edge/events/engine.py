"""
OMS Edge — Modular Event Engine with Cooldown, Deduplication, and Severity Grading.
Prevents notification spam while ensuring zero critical events are missed.
"""

from __future__ import annotations
import time
import hashlib
import logging
from typing import Dict, Optional, Tuple, Any, List
from edge.events.schema import OMSEvent
from edge.events.queue import PersistentEventQueue

log = logging.getLogger("OMS.EventEngine")


class EventEngine:
    """
    Intelligent event processor for edge surveillance.
    Manages cooldowns, deduplication hashes, and persists verified events.
    """

    # Default event cooldown periods in seconds
    DEFAULT_COOLDOWNS: Dict[str, float] = {
        "person_detected": 45.0,
        "intruder": 30.0,
        "loitering": 180.0,
        "running": 60.0,
        "fall_detected": 15.0,
        "accident": 15.0,
        "restricted_area": 20.0,
        "garbage_dump": 120.0,
        "object_abandoned": 60.0,
        "object_removed": 60.0,
        "camera_offline": 300.0,
        "camera_online": 60.0,
    }

    # Minimum confidence thresholds per event category
    MIN_CONFIDENCE: Dict[str, float] = {
        "person_detected": 0.40,
        "intruder": 0.50,
        "loitering": 0.60,
        "running": 0.55,
        "fall_detected": 0.65,
        "accident": 0.65,
        "restricted_area": 0.50,
        "garbage_dump": 0.60,
        "object_abandoned": 0.55,
        "object_removed": 0.55,
    }

    def __init__(self, queue: PersistentEventQueue, custom_cooldowns: Optional[Dict[str, float]] = None):
        self.queue = queue
        self.cooldowns = {**self.DEFAULT_COOLDOWNS, **(custom_cooldowns or {})}
        self._last_event_time: Dict[str, float] = {}   # key: (event_type, camera_id, subject_id) -> timestamp
        self._msg_hashes: Dict[str, float] = {}        # hash -> expire timestamp

    def _generate_cooldown_key(self, event_type: str, camera_id: str, track_id: Optional[int] = None, subject: Optional[str] = None) -> str:
        ident = subject if subject else (str(track_id) if track_id is not None else "global")
        return f"{event_type}:{camera_id}:{ident}"

    def trigger_event(
        self,
        event_type: str,
        camera_id: str,
        severity: str = "medium",
        confidence: float = 1.0,
        track_ids: Optional[List[int]] = None,
        location: str = "Monitored Sector",
        snapshot_base64: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        subject: Optional[str] = None,
        force: bool = False
    ) -> Optional[OMSEvent]:
        """
        Validates event confidence, applies cooldown & deduplication,
        and saves to local persistent event queue.
        """
        meta = metadata or {}
        tracks = track_ids or []

        # 1. Filter below-threshold noise
        min_conf = self.MIN_CONFIDENCE.get(event_type, 0.35)
        if confidence < min_conf and not force:
            return None

        # 2. Check Cooldown
        now = time.time()
        primary_track = tracks[0] if tracks else None
        cd_key = self._generate_cooldown_key(event_type, camera_id, primary_track, subject)
        last_t = self._last_event_time.get(cd_key, 0.0)
        cooldown_duration = self.cooldowns.get(event_type, 30.0)

        if not force and (now - last_t) < cooldown_duration:
            # Drop redundant alert within cooldown window
            return None

        # 3. Check Deduplication Hash (for exact duplicate payloads)
        dedup_payload = f"{event_type}_{camera_id}_{primary_track}_{meta.get('label', '')}_{location}"
        dedup_hash = hashlib.md5(dedup_payload.encode()).hexdigest()
        if not force and dedup_hash in self._msg_hashes:
            if now < self._msg_hashes[dedup_hash]:
                return None

        # Update cooldown timestamp & deduplication hash
        self._last_event_time[cd_key] = now
        self._msg_hashes[dedup_hash] = now + min(cooldown_duration, 120.0)

        # 4. Construct event
        event = OMSEvent(
            event_type=event_type,
            camera_id=camera_id,
            severity=severity,
            confidence=round(confidence, 3),
            track_ids=tracks,
            location=location,
            snapshot_base64=snapshot_base64,
            metadata=meta
        )

        # 5. Persist to local queue
        self.queue.push(event)
        log.info(f"[EVENT] [{severity.upper()}] {event_type} on {camera_id} (conf: {confidence:.2f}) -> {event.event_id}")
        return event

    def cleanup_expired_hashes(self):
        """Purges old deduplication hashes."""
        now = time.time()
        self._msg_hashes = {k: v for k, v in self._msg_hashes.items() if v > now}
