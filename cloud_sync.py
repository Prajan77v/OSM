"""
OMS Sentinel — Local AI Engine Cloud Sync Daemon
Runs seamlessly on the Windows RTX 4060 machine.
Maintains continuous state sync with Render Cloud API while ensuring 100% offline autonomy.
"""

from __future__ import annotations
import os
import time
import threading
import logging
from typing import Dict, List, Any, Optional
import requests

log = logging.getLogger("OMS.CloudSync")


class CloudSyncHub:
    """
    Background Synchronization Daemon for OMS Edge Tier.
    Transmits metadata and telemetry to Render Free Cloud API.
    Buffers events during internet drops or Render cold-start spin-ups.
    """

    def __init__(self, cloud_url: Optional[str] = None, api_key: Optional[str] = None):
        self.cloud_url = (cloud_url or os.getenv("OMS_CLOUD_API_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("OMS_API_KEY", "")
        self.enabled = bool(self.cloud_url and self.cloud_url.startswith("http"))
        
        self.cloud_available = False
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Buffered events queue for offline resilience
        self._event_queue: List[Dict[str, Any]] = []
        self._max_queue_size = 1000

        # State providers injected from main.py
        self._get_telemetry_fn = None
        self._get_cameras_fn = None
        self._get_summary_fn = None
        self._get_faces_fn = None

        # Backoff tracking
        self._consecutive_failures = 0
        self._next_retry_time = 0.0
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "OMS-Local-RTX4060/9.0",
            "Content-Type": "application/json"
        })
        if self.api_key:
            self._session.headers.update({"X-API-Key": self.api_key})

        if self.enabled:
            log.info(f"[CLOUD SYNC] Initialized target: {self.cloud_url}")
        else:
            log.info("[CLOUD SYNC] Local-only mode (OMS_CLOUD_API_URL not configured)")

    def bind_providers(self, get_telemetry_fn, get_cameras_fn, get_summary_fn, get_faces_fn=None):
        """Binds telemetry extraction functions from the running OMS instance."""
        self._get_telemetry_fn = get_telemetry_fn
        self._get_cameras_fn = get_cameras_fn
        self._get_summary_fn = get_summary_fn
        self._get_faces_fn = get_faces_fn

    def queue_event(self, event_dict: Dict[str, Any]):
        """Queues an event for instant or deferred cloud synchronization."""
        if not self.enabled:
            return
        with self._lock:
            self._event_queue.append(event_dict)
            if len(self._event_queue) > self._max_queue_size:
                self._event_queue.pop(0)

    def start(self):
        """Starts the background synchronization loop."""
        if not self.enabled or self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._sync_loop, name="OMS-CloudSyncDaemon", daemon=True)
        self._thread.start()
        log.info("[CLOUD SYNC] Background sync daemon started.")

    def stop(self):
        """Stops the sync daemon."""
        self._running = False

    def _sync_loop(self):
        """Periodic background sync loop."""
        last_heartbeat = 0.0

        while self._running:
            now = time.time()
            if now < self._next_retry_time:
                time.sleep(1.0)
                continue

            try:
                # 1. Send Heartbeat every 10 seconds
                if now - last_heartbeat >= 10.0:
                    self._send_heartbeat()
                    last_heartbeat = now

                # 2. Push Metadata & Flush Queued Events
                self._push_sync_payload()

                # On success: reset failure backoff
                if not self.cloud_available:
                    log.info(f"[CLOUD SYNC] Render Cloud API ONLINE ({self.cloud_url}). Sync active.")
                    self.cloud_available = True
                self._consecutive_failures = 0
                self._next_retry_time = 0.0

            except requests.exceptions.RequestException as req_err:
                self._handle_failure(req_err)
            except Exception as e:
                log.debug(f"[CLOUD SYNC] Unexpected sync error: {e}")

            time.sleep(4.0)

    def _send_heartbeat(self):
        """Sends lightweight heartbeat payload."""
        import torch
        gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU Mode"
        cuda_ok = torch.cuda.is_available()

        payload = {
            "engine_id": "rtx4060-local",
            "gpu": gpu_name,
            "cuda_available": cuda_ok,
            "status": "ONLINE",
            "version": "9.0.0",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        res = self._session.post(
            f"{self.cloud_url}/api/cloud/heartbeat",
            json=payload,
            timeout=5.0
        )
        res.raise_for_status()

    def _push_sync_payload(self):
        """Extracts current OMS telemetry and pushes to cloud endpoint."""
        telemetry = self._get_telemetry_fn() if self._get_telemetry_fn else {}
        cameras = self._get_cameras_fn() if self._get_cameras_fn else []
        summary = self._get_summary_fn() if self._get_summary_fn else {}
        faces = self._get_faces_fn() if self._get_faces_fn else []

        # Serialize cameras into lightweight metadata dicts (excluding raw cv2 matrices)
        cam_meta = []
        if isinstance(cameras, list):
            for c in cameras:
                if hasattr(c, "cam_id"):
                    cam_meta.append({
                        "id": c.cam_id,
                        "name": getattr(c, "name", f"CAM {c.cam_id}"),
                        "online": getattr(c, "online", False),
                        "fps": round(float(getattr(c, "fps", 0.0)), 1),
                        "persons": getattr(c, "persons", 0),
                        "objects": getattr(c, "objects", 0),
                        "threat": getattr(c, "threat_level", "GREEN"),
                        "active_subjects": getattr(c, "active_subjects", [])
                    })
                elif isinstance(c, dict):
                    cam_meta.append(c)

        with self._lock:
            events_to_send = list(self._event_queue[:50])

        payload = {
            "telemetry": telemetry,
            "cameras": cam_meta,
            "summary": summary,
            "faces": faces if isinstance(faces, list) else [],
            "events": events_to_send
        }

        res = self._session.post(
            f"{self.cloud_url}/api/cloud/sync",
            json=payload,
            timeout=6.0
        )
        res.raise_for_status()

        # Remove successfully sent events from queue
        with self._lock:
            del self._event_queue[:len(events_to_send)]

    def _handle_failure(self, err):
        """Exponential backoff handler for offline resilience."""
        self.cloud_available = False
        self._consecutive_failures += 1
        
        # Exponential backoff capped at 60 seconds
        backoff_sec = min(60.0, 4.0 * (1.5 ** min(self._consecutive_failures, 6)))
        self._next_retry_time = time.time() + backoff_sec

        if self._consecutive_failures == 1:
            log.info(f"[CLOUD SYNC] Cloud API temporarily unreachable ({err.__class__.__name__}). Buffering events locally.")
        elif self._consecutive_failures % 10 == 0:
            log.debug(f"[CLOUD SYNC] Cloud offline ({self._consecutive_failures} attempts). Next retry in {backoff_sec:.0f}s. Buffered events: {len(self._event_queue)}")


# Global singleton instance
cloud_sync = CloudSyncHub()
