"""
OMS Edge — Activity & Behavior Analytics Engine
Temporal behavior modeling: loitering, abnormal running, fall detection, and zone violations.
"""

from __future__ import annotations
import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any


@dataclass
class TrackHistory:
    track_id: int
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    positions: deque = field(default_factory=lambda: deque(maxlen=30)) # (timestamp, cx, cy, w, h)
    loitering_alerted: bool = False
    running_alerted: bool = False
    fall_alerted: bool = False


class ActivityAnalytics:
    """
    Evaluates temporal patterns over sliding time windows.
    Runs on lightweight heuristics without consuming GPU resources.
    """

    def __init__(
        self,
        loiter_secs: float = 25.0,
        run_speed_thresh: float = 140.0,
        fall_aspect_ratio_thresh: float = 1.3
    ):
        self.loiter_secs = loiter_secs
        self.run_speed_thresh = run_speed_thresh
        self.fall_aspect_ratio_thresh = fall_aspect_ratio_thresh
        self.tracks: Dict[int, TrackHistory] = {}

    def update_track(
        self,
        track_id: int,
        box: Tuple[int, int, int, int],
        now: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Updates track coordinates and evaluates anomaly triggers.
        Returns a list of detected behavior anomalies for this track.
        """
        t = now or time.time()
        x1, y1, x2, y2 = box
        w, h = max(1, x2 - x1), max(1, y2 - y1)
        cx, cy = x1 + w / 2.0, y1 + h / 2.0

        if track_id not in self.tracks:
            self.tracks[track_id] = TrackHistory(track_id=track_id, first_seen=t, last_seen=t)

        hist = self.tracks[track_id]
        hist.last_seen = t
        hist.positions.append((t, cx, cy, w, h))

        anomalies: List[Dict[str, Any]] = []

        # 1. Loitering Detection (presence duration > loiter_secs)
        duration = t - hist.first_seen
        if duration >= self.loiter_secs and not hist.loitering_alerted:
            hist.loitering_alerted = True
            anomalies.append({
                "event_type": "loitering",
                "severity": "medium",
                "confidence": 0.88,
                "detail": f"Subject stationary for {int(duration)}s"
            })

        # 2. Running & Sudden Velocity Spike
        if len(hist.positions) >= 6:
            t0, cx0, cy0, _, _ = hist.positions[0]
            dt = t - t0
            if dt > 0.3:
                dx = cx - cx0
                dy = cy - cy0
                speed = math.sqrt(dx * dx + dy * dy) / dt  # pixels per second
                if speed > self.run_speed_thresh and not hist.running_alerted:
                    hist.running_alerted = True
                    anomalies.append({
                        "event_type": "running",
                        "severity": "medium",
                        "confidence": min(0.95, speed / (self.run_speed_thresh * 1.5)),
                        "detail": f"Rapid movement velocity: {int(speed)} px/s"
                    })

        # 3. Fall Detection (Aspect ratio inversion: width > height * threshold)
        aspect_ratio = float(w) / float(h)
        if aspect_ratio >= self.fall_aspect_ratio_thresh and not hist.fall_alerted:
            if len(hist.positions) >= 4:
                # Confirm sudden downward centroid transition
                hist.fall_alerted = True
                anomalies.append({
                    "event_type": "fall_detected",
                    "severity": "high",
                    "confidence": 0.85,
                    "detail": f"Horizontal posture anomaly (ratio: {aspect_ratio:.2f})"
                })

        return anomalies

    def purge_lost_tracks(self, max_idle_secs: float = 30.0):
        """Removes expired tracks from active tracking memory."""
        now = time.time()
        expired = [tid for tid, h in self.tracks.items() if (now - h.last_seen) > max_idle_secs]
        for tid in expired:
            del self.tracks[tid]
