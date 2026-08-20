"""
OMS Edge — Fault-Tolerant Camera Stream Worker
Supports RTSP, IP, USB cameras and Webcams with automatic reconnect and worker isolation.
"""

from __future__ import annotations
import os
import time
import threading
import logging
from typing import Optional, Tuple, Any
import cv2
import numpy as np

log = logging.getLogger("OMS.Camera")

# Force TCP transport for reliable RTSP streaming without UDP packet loss
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"


class CameraWorker:
    """
    Independent, isolated camera stream reader.
    Automatically reconnects with exponential backoff on network disruptions.
    """

    def __init__(self, cam_id: int, source: Any, name: str = "Camera", location: str = "Sector"):
        self.cam_id = cam_id
        self.source = source
        self.name = name
        self.location = location

        self.online = False
        self.fps = 0.0
        self.total_frames = 0
        self.dropped_frames = 0
        self.last_frame_time = 0.0

        self._lock = threading.Lock()
        self._latest_frame: Optional[np.ndarray] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Reconnection parameters
        self._reconnect_delay = 2.0
        self._max_reconnect_delay = 30.0

    def start(self):
        """Spawns background capture thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, name=f"Cam-{self.cam_id}", daemon=True)
        self._thread.start()
        log.info(f"[CAMERA {self.cam_id}] Stream worker started for {self.name}")

    def stop(self):
        """Stops the stream worker."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def read_latest(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Retrieves latest uncorrupted frame.
        Guarantees zero latency by retrieving latest decoded buffer.
        """
        with self._lock:
            if self._latest_frame is not None and self.online:
                return True, self._latest_frame.copy()
            return False, None

    def _open_capture(self) -> Optional[cv2.VideoCapture]:
        """Attempts to open video capture handle."""
        try:
            # Parse integer for USB webcams
            src = int(self.source) if isinstance(self.source, str) and self.source.isdigit() else self.source
            if isinstance(self.source, int):
                src = self.source

            cap = cv2.VideoCapture(src)
            if cap.isOpened():
                # Set buffer size to 1 to avoid stale frames
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                return cap
            cap.release()
        except Exception as e:
            log.debug(f"[CAMERA {self.cam_id}] Open error: {e}")
        return None

    def _capture_loop(self):
        """Continuous capture loop with auto-reconnect."""
        fps_counter = 0
        fps_timer = time.time()

        while self._running:
            cap = self._open_capture()
            if not cap:
                self.online = False
                time.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._max_reconnect_delay, self._reconnect_delay * 1.5)
                continue

            # Connection established
            self.online = True
            self._reconnect_delay = 2.0
            log.info(f"[CAMERA {self.cam_id}] {self.name} connected successfully.")

            consecutive_read_failures = 0

            while self._running and cap.isOpened():
                ret, frame = cap.read()

                if not ret or frame is None or frame.size == 0:
                    consecutive_read_failures += 1
                    if consecutive_read_failures > 15:
                        log.warning(f"[CAMERA {self.cam_id}] Frame timeout. Reconnecting...")
                        break
                    time.sleep(0.02)
                    continue

                consecutive_read_failures = 0
                now = time.time()
                self.last_frame_time = now
                self.total_frames += 1

                # Update latest frame buffer
                with self._lock:
                    self._latest_frame = frame

                # Measure actual FPS
                fps_counter += 1
                if now - fps_timer >= 1.0:
                    self.fps = round(fps_counter / (now - fps_timer), 1)
                    fps_counter = 0
                    fps_timer = now

            # Release before reconnecting
            self.online = False
            try:
                cap.release()
            except Exception:
                pass
            time.sleep(self._reconnect_delay)
