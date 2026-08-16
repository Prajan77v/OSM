"""
OMS Production-Grade Tracking & Stable Identity Engine

Duplicate-box prevention via IoU NMS in predict_all().
======================================================
Provides:
  1. High-precision 2D Kalman Filter (KalmanBoxTracker) per track
  2. Velocity-adaptive temporal box smoothing (AdaptiveBoxSmoother) for zero-jitter HUD
  3. Continuous prediction & interpolation across skipped/detector frames (30+ FPS HUD)
  4. Robust track state machine (NEW -> TENTATIVE -> CONFIRMED -> LOST -> TERMINATED)
  5. Multi-frame identity confirmation & permanent locking through occlusions (e.g. phone in front of face)
  6. Clean sequential temporary IDs for unknown persons (UNKNOWN #01, UNKNOWN #02)
"""

from __future__ import annotations
import threading
import time
import math
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

log = logging.getLogger("OMS.tracker")

# ──────────────────────────────────────────────────────────────────────────────
# Default Hyperparameters
# ──────────────────────────────────────────────────────────────────────────────
TRACK_MIN_HITS               = 3     # Hits required before track is considered confirmed
TRACK_MAX_AGE                = 30    # Max missed frames before track is marked terminated
IDENTITY_CONFIRMATION_FRAMES = 4     # Consecutive consistent recognition frames to lock identity
IDENTITY_CONFIRM_MIN_CONF    = 0.42  # Minimum confidence to count toward identity confirmation
IDENTITY_LOST_TIMEOUT_SECS   = 8.0   # Seconds identity is held during occlusion / detection drop
ID_REUSE_BLOCK_SECS          = 10.0  # Seconds before a terminated track ID can be reused
OVERRIDE_MIN_FRAMES          = 5     # Frames required to override an already locked identity
OVERRIDE_MIN_CONF            = 0.62  # Confidence required for override candidate
SMOOTHING_ALPHA_STILL        = 0.20  # Alpha when stationary (rock-solid, zero jitter)
SMOOTHING_ALPHA_MOVE         = 0.75  # Alpha when moving quickly (responsive, zero lag)
VELOCITY_THRESHOLD_LOW       = 3.0   # Pixels/frame velocity for still regime
VELOCITY_THRESHOLD_HIGH      = 25.0  # Pixels/frame velocity for fast move regime

# NMS settings for predict_all() to prevent duplicate boxes on the same person
NMS_IOU_THRESHOLD            = 0.35  # IoU above this = boxes overlap = suppress lower-priority one
HUD_MIN_CONF                 = 0.32  # Below this confidence, don't render the box at all
HUD_MAX_LOST_AGE_FRAMES      = 8     # TEMPORARILY_LOST tracks shown for at most this many frames

# ──────────────────────────────────────────────────────────────────────────────
# Track States
# ──────────────────────────────────────────────────────────────────────────────
STATE_NEW              = "NEW"
STATE_TENTATIVE        = "TENTATIVE"
STATE_CONFIRMED        = "CONFIRMED"
STATE_TRACKED          = "TRACKED"
STATE_TEMPORARILY_LOST = "TEMPORARILY_LOST"
STATE_REACQUIRED       = "REACQUIRED"
STATE_TERMINATED       = "TERMINATED"


# ──────────────────────────────────────────────────────────────────────────────
# 2D Kalman Box Filter
# ──────────────────────────────────────────────────────────────────────────────
class KalmanBoxTracker:
    """
    Standard 8-dimensional Kalman filter for 2D bounding box tracking:
    State: x = [cx, cy, aspect_ratio, height, v_cx, v_cy, v_a, v_h]^T
    Measurement: z = [cx, cy, aspect_ratio, height]^T
    """
    def __init__(self, initial_box: Tuple[int, int, int, int]):
        # State dimension 8, measurement dimension 4
        self.dim_x = 8
        self.dim_z = 4

        x1, y1, x2, y2 = initial_box
        w = max(1.0, float(x2 - x1))
        h = max(1.0, float(y2 - y1))
        cx = float(x1 + x2) / 2.0
        cy = float(y1 + y2) / 2.0
        aspect_ratio = w / h

        # State vector
        self.x = np.zeros((8, 1), dtype=np.float64)
        self.x[0, 0] = cx
        self.x[1, 0] = cy
        self.x[2, 0] = aspect_ratio
        self.x[3, 0] = h

        # State transition matrix F
        self.F = np.eye(8, dtype=np.float64)
        for i in range(4):
            self.F[i, i + 4] = 1.0  # dt = 1 frame

        # Measurement matrix H
        self.H = np.zeros((4, 8), dtype=np.float64)
        for i in range(4):
            self.H[i, i] = 1.0

        # Initial state covariance P
        self.P = np.eye(8, dtype=np.float64)
        self.P[4:, 4:] *= 1000.0  # High uncertainty in initial velocities
        self.P *= 10.0

        # Process noise covariance Q
        self.Q = np.eye(8, dtype=np.float64)
        self.Q[:4, :4] *= 1.0
        self.Q[4:, 4:] *= 0.01

        # Measurement noise covariance R
        self.R = np.eye(4, dtype=np.float64)
        self.R[0, 0] = 1.0   # cx
        self.R[1, 1] = 1.0   # cy
        self.R[2, 2] = 10.0  # aspect ratio (penalize sudden aspect changes)
        self.R[3, 3] = 1.0   # height

    def predict(self) -> Tuple[float, float, float, float]:
        """Advance state by 1 step. Returns predicted (x1, y1, x2, y2)."""
        # Ensure aspect ratio and height remain positive
        if self.x[3, 0] + self.x[7, 0] <= 0:
            self.x[7, 0] = 0.0
        if self.x[2, 0] + self.x[6, 0] <= 0:
            self.x[6, 0] = 0.0

        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.get_current_box()

    def update(self, box: Tuple[int, int, int, int], confidence: float = 1.0):
        """Update filter with detection measurement."""
        x1, y1, x2, y2 = box
        w = max(1.0, float(x2 - x1))
        h = max(1.0, float(y2 - y1))
        cx = float(x1 + x2) / 2.0
        cy = float(y1 + y2) / 2.0
        aspect_ratio = w / h

        z = np.array([[cx], [cy], [aspect_ratio], [h]], dtype=np.float64)

        # Scale R inversely with confidence
        conf_scale = 1.0 / max(0.2, min(1.0, confidence))
        R = self.R * conf_scale

        y = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + R
        try:
            K = self.P @ self.H.T @ np.linalg.inv(S)
        except np.linalg.LinAlgError:
            K = self.P @ self.H.T @ np.linalg.pinv(S)

        self.x = self.x + K @ y
        I = np.eye(self.dim_x, dtype=np.float64)
        self.P = (I - K @ self.H) @ self.P

    def get_current_box(self) -> Tuple[float, float, float, float]:
        """Convert state [cx, cy, a, h] to (x1, y1, x2, y2)."""
        cx = self.x[0, 0]
        cy = self.x[1, 0]
        a  = max(0.05, min(10.0, self.x[2, 0]))
        h  = max(2.0, self.x[3, 0])
        w  = a * h
        x1 = cx - w / 2.0
        y1 = cy - h / 2.0
        x2 = cx + w / 2.0
        y2 = cy + h / 2.0
        return (x1, y1, x2, y2)

    def get_velocity(self) -> Tuple[float, float]:
        """Returns velocity magnitude in pixels per frame."""
        return (float(self.x[4, 0]), float(self.x[5, 0]))


# ──────────────────────────────────────────────────────────────────────────────
# Adaptive Bounding Box Smoother
# ──────────────────────────────────────────────────────────────────────────────
class AdaptiveBoxSmoother:
    """
    Applies an adaptive EMA filter to predicted/measured coordinates.
    Stationary objects get high smoothing (zero pixel jitter).
    Moving objects get dynamic low smoothing (zero lag / trailing).
    """
    def __init__(self, initial_box: Tuple[float, float, float, float]):
        self.smoothed_box = np.array(initial_box, dtype=np.float64)

    def smooth(self, target_box: Tuple[float, float, float, float], velocity: Tuple[float, float]) -> Tuple[int, int, int, int]:
        vx, vy = velocity
        speed = math.hypot(vx, vy)

        # Dynamic alpha calculation based on speed
        if speed <= VELOCITY_THRESHOLD_LOW:
            alpha = SMOOTHING_ALPHA_STILL
        elif speed >= VELOCITY_THRESHOLD_HIGH:
            alpha = SMOOTHING_ALPHA_MOVE
        else:
            t = (speed - VELOCITY_THRESHOLD_LOW) / (VELOCITY_THRESHOLD_HIGH - VELOCITY_THRESHOLD_LOW)
            alpha = SMOOTHING_ALPHA_STILL + t * (SMOOTHING_ALPHA_MOVE - SMOOTHING_ALPHA_STILL)

        tgt = np.array(target_box, dtype=np.float64)
        self.smoothed_box = alpha * tgt + (1.0 - alpha) * self.smoothed_box

        x1 = int(round(self.smoothed_box[0]))
        y1 = int(round(self.smoothed_box[1]))
        x2 = int(round(self.smoothed_box[2]))
        y2 = int(round(self.smoothed_box[3]))
        return (x1, y1, x2, y2)


# ──────────────────────────────────────────────────────────────────────────────
# Track State Object
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class TrackIdentity:
    """Complete physical track state with Kalman filter and identity persistence."""
    track_id:     int
    label:        str               = "person"
    state:        str               = STATE_NEW
    hits:         int               = 1
    age:          int               = 1
    missed_frames:int               = 0

    # ── Identity State ────────────────────────────────────────────────────────
    confirmed_pid:   Optional[str]   = None
    confirmed_name:  Optional[str]   = None
    confirmed_conf:  float           = 0.0
    confirmed_at:    float           = 0.0
    identity_locked: bool            = False

    # ── Unknown Tag (e.g. UNKNOWN #01) ────────────────────────────────────────
    unknown_tag:     str             = ""

    # ── Candidate Accumulator ─────────────────────────────────────────────────
    candidate_pid:    Optional[str]  = None
    candidate_name:   Optional[str]  = None
    candidate_frames: int            = 0
    candidate_conf:   float          = 0.0

    # ── Override Accumulator ──────────────────────────────────────────────────
    override_pid:     Optional[str]  = None
    override_name:    Optional[str]  = None
    override_frames:  int            = 0
    override_conf:    float          = 0.0

    # ── Temporal / Occlusion ──────────────────────────────────────────────────
    created_at:       float          = field(default_factory=time.time)
    last_seen_at:     float          = field(default_factory=time.time)
    grace_expires_at: float          = 0.0

    # ── Spatial Filters ───────────────────────────────────────────────────────
    kalman:   Optional[KalmanBoxTracker]   = None
    smoother: Optional[AdaptiveBoxSmoother]= None
    latest_smoothed_box: Tuple[int, int, int, int] = (0, 0, 0, 0)
    last_raw_conf: float = 0.5

    # ── Diagnostics ───────────────────────────────────────────────────────────
    total_recognition_attempts: int  = 0
    total_confirmed_updates:    int  = 0

    def is_confirmed(self) -> bool:
        return self.identity_locked and self.confirmed_pid is not None

    def grace_active(self) -> bool:
        return time.time() < self.grace_expires_at

    def display_name(self) -> str:
        """Returns stable display name."""
        if self.confirmed_name:
            return self.confirmed_name
        if self.label != "person":
            return self.label.upper()
        return self.unknown_tag or f"UNKNOWN #{self.track_id:02d}"

    def display_conf(self) -> float:
        if self.confirmed_conf > 0.0:
            return self.confirmed_conf
        return self.last_raw_conf


# ──────────────────────────────────────────────────────────────────────────────
# Stable Identity & Tracking Engine
# ──────────────────────────────────────────────────────────────────────────────
class StableIdentityEngine:
    """
    Production-grade multi-object tracking and identity persistence manager.
    Maintains a 2D Kalman filter and dynamic smoother per track.
    Decoupled: predict_all() runs on every frame (30+ FPS) while updates run on YOLO frames.
    """
    def __init__(self):
        self._lock   = threading.Lock()
        self._tracks: Dict[int, TrackIdentity] = {}
        self._recently_removed: Dict[int, float] = {}
        self._next_unknown_idx: int = 1
        self._unknown_tag_map: Dict[int, str] = {}  # tid -> UNKNOWN #XX

    def _get_or_create_unknown_tag(self, tid: int) -> str:
        if tid not in self._unknown_tag_map:
            self._unknown_tag_map[tid] = f"UNKNOWN #{self._next_unknown_idx:02d}"
            self._next_unknown_idx += 1
        return self._unknown_tag_map[tid]

    # ──────────────────────────────────────────────────────────────────────────
    # Called on EVERY frame (both detection frames and skipped frames)
    # ──────────────────────────────────────────────────────────────────────────
    # ──────────────────────────────────────────────────────────────────────────
    # Internal: overlap & containment computation for NMS deduplication
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _track_priority(det: dict) -> int:
        """Higher = more important in NMS (keep this one, suppress others)."""
        state = det.get("state", "")
        locked = det.get("locked", False)
        if locked:
            return 4   # Confirmed & locked — always keep
        if state == STATE_CONFIRMED:
            return 3
        if state in (STATE_TRACKED, STATE_REACQUIRED):
            return 2
        if state == STATE_NEW:
            return 1
        return 0       # TEMPORARILY_LOST, TENTATIVE — lowest priority

    def predict_all(self) -> List[dict]:
        """
        Advance all Kalman filters by 1 step and compute smoothed coordinates.
        Returns a deduplicated list of active detection dicts for HUD rendering.
        IoU NMS prevents duplicate boxes from multiple ByteTrack IDs on same person.
        """
        with self._lock:
            raw_dets = []
            for tid, t in list(self._tracks.items()):
                if t.state == STATE_TERMINATED:
                    continue

                t.age += 1

                # Don't advance / show TEMPORARILY_LOST after a short grace window
                if t.state == STATE_TEMPORARILY_LOST and t.missed_frames > HUD_MAX_LOST_AGE_FRAMES:
                    continue

                if t.kalman is not None and t.smoother is not None:
                    pred_box = t.kalman.predict()
                    vel = t.kalman.get_velocity()
                    smoothed = t.smoother.smooth(pred_box, vel)
                    t.latest_smoothed_box = smoothed

                    # Visibility gates
                    if t.label == "person":
                        if t.hits < TRACK_MIN_HITS and not t.is_confirmed():
                            continue   # Too new — suppress until confirmed enough
                        if t.display_conf() < HUD_MIN_CONF and not t.is_confirmed():
                            continue   # Too low confidence — suppress ghost detections
                    else:
                        # Non-person objects: stable confidence threshold without dropping on alternate frames
                        if t.display_conf() < 0.38:
                            continue

                    is_known = t.is_confirmed() and not (t.confirmed_pid and t.confirmed_pid.startswith("Unknown-"))
                    raw_dets.append({
                        "label":    t.label,
                        "conf":     t.display_conf(),
                        "box":      smoothed,
                        "disp":     t.display_name(),
                        "pid":      t.confirmed_pid or f"Unknown-{tid}",
                        "tid":      tid,
                        "is_known": is_known,
                        "locked":   t.identity_locked,
                        "state":    t.state,
                        "_priority": self._track_priority({"state": t.state, "locked": t.identity_locked, "label": t.label})
                    })

            # ── IoU NMS: suppress duplicate overlapping boxes ──────────────────
            # Sort by priority descending so we always keep the best-quality track
            raw_dets.sort(key=lambda d: (d["_priority"], d["conf"]), reverse=True)
            kept: List[dict] = []
            suppressed_tids: set = set()
            for det in raw_dets:
                if det["tid"] in suppressed_tids:
                    continue
                # Check overlap against already-kept boxes
                duplicate = False
                for kept_det in kept:
                    is_det_p  = (det.get("label") == "person")
                    is_kept_p = (kept_det.get("label") == "person")

                    # Case 1: Person vs Person duplicate
                    if is_det_p and is_kept_p:
                        ovl = _overlap(det["box"], kept_det["box"])
                        if ovl > NMS_IOU_THRESHOLD:
                            suppressed_tids.add(det["tid"])
                            log.debug(f"[SIE-NMS] Suppressed track {det['tid']} (overlap={ovl:.2f} with track {kept_det['tid']})")
                            duplicate = True
                            break

                    # Case 2: Object vs Object competing on the same physical item
                    # (e.g. Remote vs Cell Phone or duplicate Chair boxes)
                    elif not is_det_p and not is_kept_p:
                        ovl = _overlap(det["box"], kept_det["box"])
                        if ovl > 0.40:
                            suppressed_tids.add(det["tid"])
                            log.debug(f"[SIE-NMS] Suppressed competing object track {det['tid']} {det.get('disp')} (overlap={ovl:.2f} with {kept_det['tid']} {kept_det.get('disp')})")
                            duplicate = True
                            break

                    # Case 3: Person vs Object (e.g. person holding phone) -> Allowed to coexist!

                if not duplicate:
                    # Clean up internal field before returning
                    det.pop("_priority", None)
                    kept.append(det)

            return kept

    # ──────────────────────────────────────────────────────────────────────────
    # Called on YOLO detection frames: update measurement
    # ──────────────────────────────────────────────────────────────────────────
    def update_track_measurement(self, tid: int, box: Tuple[int, int, int, int],
                                 conf: float, label: str = "person") -> TrackIdentity:
        """Update Kalman filter and state machine with actual YOLO detection."""
        with self._lock:
            if tid not in self._tracks:
                # Check reuse block
                if tid in self._recently_removed:
                    if time.time() - self._recently_removed[tid] < ID_REUSE_BLOCK_SECS:
                        log.debug(f"[SIE] Track {tid} blocked from reuse")
                    else:
                        del self._recently_removed[tid]

                t = TrackIdentity(
                    track_id=tid,
                    label=label,
                    state=STATE_NEW,
                    unknown_tag=self._get_or_create_unknown_tag(tid),
                    last_raw_conf=conf
                )
                t.kalman = KalmanBoxTracker(box)
                t.smoother = AdaptiveBoxSmoother((float(box[0]), float(box[1]), float(box[2]), float(box[3])))
                t.latest_smoothed_box = box
                self._tracks[tid] = t
                log.debug(f"[SIE] Track {tid} initialized (NEW)")

            t = self._tracks[tid]
            t.hits += 1
            t.missed_frames = 0
            t.last_seen_at = time.time()
            t.last_raw_conf = conf
            t.label = label

            # Update Kalman filter
            if t.kalman is not None:
                t.kalman.update(box, confidence=conf)
                vel = t.kalman.get_velocity()
                if t.smoother is not None:
                    t.latest_smoothed_box = t.smoother.smooth(t.kalman.get_current_box(), vel)

            # State transitions
            if t.state in (STATE_NEW, STATE_TENTATIVE):
                if t.hits >= TRACK_MIN_HITS:
                    t.state = STATE_TRACKED
            elif t.state == STATE_TEMPORARILY_LOST:
                t.state = STATE_REACQUIRED
                t.grace_expires_at = 0.0

            return t

    # ──────────────────────────────────────────────────────────────────────────
    # Called on YOLO detection frames for tracks NOT detected
    # ──────────────────────────────────────────────────────────────────────────
    def mark_missing(self, tid: int):
        """Called when a known track was missing in this detection cycle."""
        with self._lock:
            if tid not in self._tracks:
                return
            t = self._tracks[tid]
            t.missed_frames += 1

            if t.state in (STATE_TRACKED, STATE_CONFIRMED, STATE_REACQUIRED):
                if t.missed_frames >= 2:
                    t.state = STATE_TEMPORARILY_LOST
                    t.grace_expires_at = time.time() + IDENTITY_LOST_TIMEOUT_SECS

            elif t.state == STATE_TEMPORARILY_LOST:
                if t.missed_frames > TRACK_MAX_AGE and not t.grace_active():
                    self._remove_track(tid)

    # ──────────────────────────────────────────────────────────────────────────
    # Face Recognition Result Ingestion
    # ──────────────────────────────────────────────────────────────────────────
    def submit_recognition(self, tid: int, pid: str, name: str, conf: float) -> bool:
        """
        Feeds async face recognition result into identity state.
        Requires IDENTITY_CONFIRMATION_FRAMES consistent matches to confirm.
        Once confirmed, identity is locked and resilient to occlusions.
        """
        with self._lock:
            if tid not in self._tracks:
                return False
            t = self._tracks[tid]
            t.total_recognition_attempts += 1

            if conf < IDENTITY_CONFIRM_MIN_CONF:
                t.candidate_pid = None
                t.candidate_frames = 0
                return False

            # Case 1: Track does not have a confirmed identity yet
            if not t.identity_locked or not t.confirmed_pid:
                if t.candidate_pid == pid:
                    t.candidate_frames += 1
                    t.candidate_conf = 0.7 * t.candidate_conf + 0.3 * conf
                else:
                    t.candidate_pid = pid
                    t.candidate_name = name
                    t.candidate_frames = 1
                    t.candidate_conf = conf

                is_known_person = not pid.startswith("Unknown-") and not name.startswith("Intruder-")
                required_frames = 1 if (is_known_person or conf >= 0.50) else 2

                if t.candidate_frames >= required_frames:
                    t.confirmed_pid = pid
                    t.confirmed_name = name
                    t.confirmed_conf = t.candidate_conf
                    t.confirmed_at = time.time()
                    t.identity_locked = True
                    t.state = STATE_CONFIRMED
                    t.candidate_pid = None
                    t.candidate_frames = 0
                    t.total_confirmed_updates += 1
                    log.info(f"[SIE] Track {tid} LOCKED & CONFIRMED -> {name} ({pid}) conf={t.confirmed_conf:.2f}")
                    return True
                return False

            # Case 2: Already confirmed — same person reinforces confidence and extends grace
            if pid == t.confirmed_pid:
                t.confirmed_conf = max(t.confirmed_conf, conf)
                t.confirmed_at = time.time()
                t.override_frames = 0
                t.override_pid = None
                t.grace_expires_at = time.time() + IDENTITY_LOST_TIMEOUT_SECS
                return True

            # Case 3: Contradictory result (different person detected on locked track)
            # Requires OVERRIDE_MIN_FRAMES high-confidence results to override
            if conf >= OVERRIDE_MIN_CONF:
                if t.override_pid == pid:
                    t.override_frames += 1
                    t.override_conf = 0.6 * t.override_conf + 0.4 * conf
                else:
                    t.override_pid = pid
                    t.override_name = name
                    t.override_frames = 1
                    t.override_conf = conf

                if t.override_frames >= OVERRIDE_MIN_FRAMES:
                    old_name = t.confirmed_name
                    t.confirmed_pid = pid
                    t.confirmed_name = name
                    t.confirmed_conf = t.override_conf
                    t.confirmed_at = time.time()
                    t.override_pid = None
                    t.override_frames = 0
                    t.total_confirmed_updates += 1
                    log.info(f"[SIE] Track {tid} OVERRIDE: {old_name} -> {name} ({pid}) conf={t.confirmed_conf:.2f}")
                    return True

            return False

    # ──────────────────────────────────────────────────────────────────────────
    # Forced Identity Locking (from UI Rename / Face Enrollment)
    # ──────────────────────────────────────────────────────────────────────────
    def force_identity(self, tid: int, pid: str, name: str, conf: float = 0.99):
        """Immediately locks confirmed identity onto a track (e.g. from user UI action)."""
        with self._lock:
            if tid not in self._tracks:
                self._tracks[tid] = TrackIdentity(track_id=tid)
            t = self._tracks[tid]
            t.confirmed_pid = pid
            t.confirmed_name = name
            t.confirmed_conf = conf
            t.confirmed_at = time.time()
            t.identity_locked = True
            t.state = STATE_CONFIRMED
            t.grace_expires_at = time.time() + IDENTITY_LOST_TIMEOUT_SECS
            t.override_pid = None
            t.override_frames = 0
            log.info(f"[SIE] Track {tid} FORCE-LOCKED -> {name} ({pid})")

    def force_identity_by_pid(self, pid: str, name: str, conf: float = 0.99):
        """Update identity for all tracks matching this pid."""
        with self._lock:
            for t in self._tracks.values():
                if t.confirmed_pid == pid:
                    t.confirmed_name = name
                    t.confirmed_conf = conf
                    t.confirmed_at = time.time()
                    t.identity_locked = True
                    t.grace_expires_at = time.time() + IDENTITY_LOST_TIMEOUT_SECS

    # ──────────────────────────────────────────────────────────────────────────
    # Queries & Display State
    # ──────────────────────────────────────────────────────────────────────────
    def get_display(self, tid: int) -> Tuple[Optional[str], Optional[str], float, bool]:
        """Returns (pid, display_name, confidence, is_confirmed)."""
        with self._lock:
            t = self._tracks.get(tid)
            if t is None:
                return None, None, 0.0, False
            if t.confirmed_pid and (t.identity_locked or t.grace_active()):
                return t.confirmed_pid, t.confirmed_name, t.confirmed_conf, True
            return None, t.display_name(), t.display_conf(), False

    def get_active_tids(self) -> List[int]:
        with self._lock:
            return [tid for tid, t in self._tracks.items() if t.state != STATE_TERMINATED]

    def purge_expired(self):
        """Periodic maintenance."""
        with self._lock:
            now = time.time()
            to_remove = []
            for tid, t in self._tracks.items():
                if t.state == STATE_TEMPORARILY_LOST:
                    if not t.grace_active() and t.missed_frames > TRACK_MAX_AGE:
                        to_remove.append(tid)
                elif t.state == STATE_TERMINATED:
                    to_remove.append(tid)
            for tid in to_remove:
                self._remove_track(tid)

            # Prune reuse blocks
            expired_blocks = [tid for tid, ts in self._recently_removed.items()
                              if now - ts > ID_REUSE_BLOCK_SECS * 2]
            for tid in expired_blocks:
                del self._recently_removed[tid]

    def _remove_track(self, tid: int):
        if tid in self._tracks:
            self._recently_removed[tid] = time.time()
            del self._tracks[tid]
            self._unknown_tag_map.pop(tid, None)
            log.debug(f"[SIE] Track {tid} TERMINATED")

    def diagnostics(self) -> dict:
        with self._lock:
            all_tracks = list(self._tracks.values())
        confirmed = [t for t in all_tracks if t.is_confirmed()]
        tracked   = [t for t in all_tracks if t.state in (STATE_TRACKED, STATE_CONFIRMED)]
        lost      = [t for t in all_tracks if t.state == STATE_TEMPORARILY_LOST]
        return {
            "total_tracks":     len(all_tracks),
            "confirmed_tracks": len(confirmed),
            "tracked_tracks":   len(tracked),
            "lost_tracks":      len(lost),
            "track_details": [
                {
                    "track_id":        t.track_id,
                    "state":           t.state,
                    "identity":        t.display_name(),
                    "pid":             t.confirmed_pid,
                    "conf":            round(t.display_conf(), 3),
                    "missed_frames":   t.missed_frames,
                    "hits":            t.hits,
                    "locked":          t.identity_locked,
                    "smoothed_box":    t.latest_smoothed_box
                }
                for t in all_tracks
            ]
        }


# ──────────────────────────────────────────────────────────────────────────────
# Module-level NMS: call from main.py on YOLO detection frames
# ──────────────────────────────────────────────────────────────────────────────
def _overlap(box_a, box_b) -> float:
    """
    Overlap score = max(IoU, intersection/area_of_smaller_box).
    Catches the case where ByteTrack assigns a smaller box that is fully
    contained inside a larger box (standard IoU would be low, but visually
    they are the same detection).
    """
    xa = max(box_a[0], box_b[0]); ya = max(box_a[1], box_b[1])
    xb = min(box_a[2], box_b[2]); yb = min(box_a[3], box_b[3])
    inter = max(0, xb - xa) * max(0, yb - ya)
    if inter == 0:
        return 0.0
    area_a = max(1, (box_a[2] - box_a[0]) * (box_a[3] - box_a[1]))
    area_b = max(1, (box_b[2] - box_b[0]) * (box_b[3] - box_b[1]))
    iou = inter / float(area_a + area_b - inter)
    # Containment: what fraction of the SMALLER box is covered by the intersection
    containment = inter / min(area_a, area_b)
    return max(iou, containment)


def _det_priority(d: dict) -> int:
    """
    NMS priority. Higher = preferred (kept), lower = suppressed.
    """
    label = d.get("label", "person")
    if label != "person":
        return 2   # Non-person objects
    if d.get("locked"):
        return 5   # User-confirmed identity — always keep
    pid = d.get("pid", "")
    if pid and not pid.startswith("Unknown-"):
        return 4   # Face-recognised known person
    state = d.get("state", "")
    if state == STATE_CONFIRMED:
        return 3
    if state in (STATE_TRACKED, STATE_REACQUIRED):
        return 2
    if state == STATE_NEW:
        return 1
    return 0       # TEMPORARILY_LOST, TENTATIVE, pure unknown


def nms_detections(dets: list,
                   iou_threshold: float = NMS_IOU_THRESHOLD,
                   min_conf: float = HUD_MIN_CONF) -> list:
    """
    Apply priority-aware IoU NMS to a flat list of detection dicts.
    Suppresses duplicate persons and competing overlapping objects,
    while preserving objects interacting with persons.
    """
    # Drop below-threshold confidence boxes (person >= min_conf, objects >= 0.42)
    filtered = []
    for d in dets:
        label = d.get("label", "person")
        conf = d.get("conf", 0)
        pid_val = str(d.get("pid") or "")
        if label == "person":
            if d.get("locked") or (pid_val and not pid_val.startswith("Unknown-")) or conf >= min_conf:
                filtered.append(d)
        else:
            if conf >= 0.42:
                filtered.append(d)

    # Sort: highest priority first, then highest confidence
    filtered.sort(key=lambda d: (_det_priority(d), d.get("conf", 0)), reverse=True)

    kept = []
    suppressed_tids = set()

    for det in filtered:
        tid = det.get("tid")
        if tid is not None and tid in suppressed_tids:
            continue

        duplicate = False
        for kept_det in kept:
            is_det_p  = (det.get("label") == "person")
            is_kept_p = (kept_det.get("label") == "person")

            # Case 1: Person vs Person duplicate
            if is_det_p and is_kept_p:
                ovl = _overlap(det["box"], kept_det["box"])
                if ovl > iou_threshold:
                    if tid is not None:
                        suppressed_tids.add(tid)
                    duplicate = True
                    break

            # Case 2: Object vs Object competing on the same physical item
            # (e.g. Remote vs Cell Phone or duplicate Chair boxes)
            elif not is_det_p and not is_kept_p:
                ovl = _overlap(det["box"], kept_det["box"])
                if ovl > 0.40:
                    if tid is not None:
                        suppressed_tids.add(tid)
                    log.debug(
                        "[NMS] Suppressed competing object tid=%s %s (overlap=%.2f with tid=%s %s)",
                        tid, det.get("disp"), ovl, kept_det.get("tid"), kept_det.get("disp")
                    )
                    duplicate = True
                    break

            # Case 3: Person vs Object -> Allowed to coexist!

        if not duplicate:
            kept.append(det)

    return kept

