"""
OMS Edge — Persistent Local SQLite Event Queue
Guarantees zero event loss during network outages or application crashes.
"""

from __future__ import annotations
import sqlite3
import json
import logging
import threading
from pathlib import Path
from typing import List, Optional
from edge.events.schema import OMSEvent

log = logging.getLogger("OMS.EventQueue")


class PersistentEventQueue:
    """
    SQLite-backed local queue for edge surveillance events.
    Thread-safe and ACID-compliant using WAL mode.
    """

    def __init__(self, db_path: str = "logs/oms_event_queue.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_db(self):
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS event_queue (
                        event_id TEXT PRIMARY KEY,
                        camera_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        timestamp TEXT NOT NULL,
                        track_ids TEXT,
                        location TEXT,
                        snapshot_base64 TEXT,
                        clip_url TEXT,
                        metadata TEXT,
                        synced INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_synced_created ON event_queue(synced, created_at);")
                conn.commit()
        log.info(f"[EVENT QUEUE] Persistent SQLite queue initialized at {self.db_path}")

    def push(self, event: OMSEvent) -> bool:
        """Enqueues an event to local persistent storage."""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO event_queue (
                            event_id, camera_id, event_type, severity, confidence,
                            timestamp, track_ids, location, snapshot_base64, clip_url,
                            metadata, synced
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """, (
                        event.event_id,
                        event.camera_id,
                        event.event_type,
                        event.severity,
                        event.confidence,
                        event.timestamp,
                        json.dumps(event.track_ids),
                        event.location,
                        event.snapshot_base64,
                        event.clip_url,
                        json.dumps(event.metadata),
                    ))
                    conn.commit()
                return True
            except Exception as e:
                log.error(f"[EVENT QUEUE] Failed to push event {event.event_id}: {e}")
                return False

    def get_pending(self, limit: int = 50) -> List[OMSEvent]:
        """Fetches unsynced events in chronological order."""
        events: List[OMSEvent] = []
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT event_id, camera_id, event_type, severity, confidence,
                               timestamp, track_ids, location, snapshot_base64, clip_url,
                               metadata, synced
                        FROM event_queue
                        WHERE synced = 0
                        ORDER BY created_at ASC
                        LIMIT ?
                    """, (limit,))
                    rows = cursor.fetchall()
                    for r in rows:
                        events.append(OMSEvent(
                            event_id=r[0],
                            camera_id=r[1],
                            event_type=r[2],
                            severity=r[3],
                            confidence=r[4],
                            timestamp=r[5],
                            track_ids=json.loads(r[6]) if r[6] else [],
                            location=r[7] or "Monitored Sector",
                            snapshot_base64=r[8],
                            clip_url=r[9],
                            metadata=json.loads(r[10]) if r[10] else {},
                            synced=bool(r[11])
                        ))
            except Exception as e:
                log.error(f"[EVENT QUEUE] Error fetching pending events: {e}")
        return events

    def mark_synced(self, event_ids: List[str]) -> bool:
        """Marks a batch of events as successfully transmitted to cloud."""
        if not event_ids:
            return True
        with self._lock:
            try:
                with self._get_connection() as conn:
                    placeholders = ",".join("?" for _ in event_ids)
                    conn.execute(f"""
                        UPDATE event_queue
                        SET synced = 1
                        WHERE event_id IN ({placeholders})
                    """, event_ids)
                    conn.commit()
                return True
            except Exception as e:
                log.error(f"[EVENT QUEUE] Error marking events synced: {e}")
                return False

    def get_queue_stats(self) -> dict:
        """Returns statistics on pending and total events."""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM event_queue WHERE synced = 0")
                    pending = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM event_queue")
                    total = cursor.fetchone()[0]
                    return {"pending_events": pending, "total_events": total}
            except Exception:
                return {"pending_events": 0, "total_events": 0}

    def purge_old_synced(self, keep_days: int = 7):
        """Purges old synced events to reclaim disk space."""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.execute("""
                        DELETE FROM event_queue
                        WHERE synced = 1
                        AND created_at < datetime('now', '-' || ? || ' days')
                    """, (keep_days,))
                    conn.commit()
            except Exception as e:
                log.warning(f"[EVENT QUEUE] Error purging old synced events: {e}")
