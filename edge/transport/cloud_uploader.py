"""
OMS Edge — Cloud Telemetry & Persistent Event Synchronization Daemon
Transmits events and telemetry to Render Cloud API with zero loss.
"""

from __future__ import annotations
import os
import time
import threading
import logging
from typing import Optional, Callable, List, Dict, Any
import requests

from edge.events.queue import PersistentEventQueue
from edge.events.schema import OMSEvent

log = logging.getLogger("OMS.CloudUploader")


class CloudUploader:
    """
    Background worker that flushes queued events and sends
    live hardware heartbeats to the Cloud API.
    """

    def __init__(
        self,
        queue: PersistentEventQueue,
        cloud_url: Optional[str] = None,
        edge_token: Optional[str] = None,
        engine_id: str = "edge-node-1"
    ):
        self.queue = queue
        self.cloud_url = (cloud_url or os.getenv("OMS_CLOUD_API_URL", "https://oms-sentinel-cloud.onrender.com")).rstrip("/")
        self.edge_token = edge_token or os.getenv("OMS_EDGE_TOKEN", "")
        self.engine_id = engine_id

        self.enabled = bool(self.cloud_url and self.cloud_url.startswith("http"))
        self.cloud_available = False
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Callbacks to extract live edge state
        self._get_telemetry_fn: Optional[Callable] = None
        self._get_cameras_fn: Optional[Callable] = None

        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "OMS-Edge-Node/9.0",
            "Content-Type": "application/json"
        })
        if self.edge_token:
            self._session.headers.update({"X-Edge-Token": self.edge_token})

        self._consecutive_failures = 0
        self._next_retry_t = 0.0

    def bind_state_providers(self, get_telemetry_fn: Callable, get_cameras_fn: Callable):
        self._get_telemetry_fn = get_telemetry_fn
        self._get_cameras_fn = get_cameras_fn

    def start(self):
        if not self.enabled or self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, name="OMS-CloudUploader", daemon=True)
        self._thread.start()
        log.info(f"[CLOUD UPLOADER] Started sync daemon for target: {self.cloud_url}")

    def stop(self):
        self._running = False

    def _worker_loop(self):
        last_heartbeat = 0.0

        while self._running:
            now = time.time()
            if now < self._next_retry_t:
                time.sleep(1.0)
                continue

            try:
                # 1. Heartbeat every 10 seconds
                if now - last_heartbeat >= 10.0:
                    self._send_heartbeat()
                    last_heartbeat = now

                # 2. Flush pending events from SQLite queue
                pending = self.queue.get_pending(limit=25)
                if pending:
                    self._upload_batch_events(pending)

                # 3. Full sync every 4 seconds (cameras & telemetry)
                self._send_sync()

                if not self.cloud_available:
                    self.cloud_available = True
                    log.info(f"[CLOUD UPLOADER] Connected to Cloud Hub ({self.cloud_url})")

                self._consecutive_failures = 0
                self._next_retry_t = 0.0

            except requests.exceptions.RequestException as req_err:
                self._handle_failure(req_err)
            except Exception as e:
                log.debug(f"[CLOUD UPLOADER] Sync loop error: {e}")

            time.sleep(3.0)

    def _send_heartbeat(self):
        telemetry = self._get_telemetry_fn() if self._get_telemetry_fn else {}
        payload = {
            "engine_id": self.engine_id,
            "status": "ONLINE",
            "gpu": telemetry.get("gpu_name", "CPU Mode"),
            "cuda_available": telemetry.get("cuda", False),
            "hardware_profile": telemetry.get("hw_profile", "CPU"),
            "cpu": telemetry.get("cpu", 0.0),
            "ram": telemetry.get("ram", 0.0),
            "version": "9.0.0",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        res = self._session.post(f"{self.cloud_url}/api/edge/heartbeat", json=payload, timeout=4.0)
        res.raise_for_status()

    def _upload_batch_events(self, events: List[OMSEvent]):
        payload = {
            "engine_id": self.engine_id,
            "events": [e.to_dict() for e in events]
        }
        res = self._session.post(f"{self.cloud_url}/api/events/batch", json=payload, timeout=5.0)
        res.raise_for_status()

        # Successfully sent: mark as synced in local SQLite
        event_ids = [e.event_id for e in events]
        self.queue.mark_synced(event_ids)
        log.info(f"[CLOUD UPLOADER] Synced {len(event_ids)} events to cloud hub.")

    def _send_sync(self):
        telemetry = self._get_telemetry_fn() if self._get_telemetry_fn else {}
        cameras = self._get_cameras_fn() if self._get_cameras_fn else []

        cam_payload = []
        for c in cameras:
            cam_payload.append({
                "id": c.cam_id,
                "name": c.name,
                "location": c.location,
                "online": c.online,
                "fps": c.fps,
                "persons": getattr(c, "persons_count", 0),
                "objects": getattr(c, "objects_count", 0),
                "threat": getattr(c, "threat_level", "GREEN"),
                "source": str(c.source)
            })

        payload = {
            "engine_id": self.engine_id,
            "telemetry": telemetry,
            "cameras": cam_payload
        }
        res = self._session.post(f"{self.cloud_url}/api/edge/sync", json=payload, timeout=5.0)
        res.raise_for_status()

    def _handle_failure(self, err):
        self.cloud_available = False
        self._consecutive_failures += 1
        backoff_sec = min(45.0, 3.0 * (1.4 ** min(self._consecutive_failures, 6)))
        self._next_retry_t = time.time() + backoff_sec
        if self._consecutive_failures == 1:
            log.info(f"[CLOUD UPLOADER] Cloud temporarily unreachable. Buffering events locally in SQLite.")
