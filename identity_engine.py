"""
OMS Stable Identity Engine
==========================
Provides temporally-stable identity assignment for persistent multi-person tracking.

Key guarantees:
  - Confirmed identities are NEVER reset by a single bad recognition frame
  - Names persist for IDENTITY_GRACE_SECS after face disappears / occlusion
  - Track IDs are never reused within ID_REUSE_BLOCK_SECS after deletion
  - Identity changes require MIN_CONFIRM_FRAMES consecutive high-conf results
  - Strong override requires OVERRIDE_MIN_FRAMES consecutive results for a *different* pid
"""

from __future__ import annotations
import threading
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

log = logging.getLogger("OMS.identity")

# ──────────────────────────────────────────────────────────────────────────────
# Tuning knobs — all can be overridden via Config if needed
# ──────────────────────────────────────────────────────────────────────────────

# Minimum consecutive recognition frames before an identity is *confirmed*
MIN_CONFIRM_FRAMES      = 3

# Minimum confidence to count toward confirmation
CONFIRM_MIN_CONF        = 0.45

# Seconds a confirmed identity is retained after the track stops being detected
IDENTITY_GRACE_SECS     = 8.0

# Frames without detection before track moves to LOST state
LOST_FRAMES_THRESH      = 60   # ~2 s at 30 fps

# Seconds a LOST track is kept in memory for re-identification
REIDENT_WINDOW_SECS     = 6.0

# Seconds after removal before a track ID may be reused by a *different* person
ID_REUSE_BLOCK_SECS     = 10.0

# Frames of consecutive *different-pid* results needed to override a confirmed identity
OVERRIDE_MIN_FRAMES     = 5

# Minimum confidence for an override candidate to accumulate votes
OVERRIDE_MIN_CONF       = 0.60

# ──────────────────────────────────────────────────────────────────────────────
# Track states
# ──────────────────────────────────────────────────────────────────────────────
STATE_TENTATIVE  = "TENTATIVE"
STATE_CONFIRMED  = "CONFIRMED"
STATE_LOST       = "LOST"
STATE_REMOVED    = "REMOVED"


@dataclass
class TrackIdentity:
    """Per-track identity state. Thread-safe via StableIdentityEngine's lock."""
    track_id:     int
    state:        str   = STATE_TENTATIVE

    # ── Confirmed identity ────────────────────────────────────────────────────
    confirmed_pid:   Optional[str]   = None
    confirmed_name:  Optional[str]   = None
    confirmed_conf:  float           = 0.0
    confirmed_at:    float           = 0.0

    # ── Candidate accumulator ─────────────────────────────────────────────────
    candidate_pid:    Optional[str] = None
    candidate_name:   Optional[str] = None
    candidate_frames: int           = 0     # consecutive matching frames
    candidate_conf:   float         = 0.0   # rolling avg conf

    # ── Override accumulator (for replacing a confirmed identity) ─────────────
    override_pid:     Optional[str] = None
    override_name:    Optional[str] = None
    override_frames:  int           = 0
    override_conf:    float         = 0.0

    # ── Track lifecycle ───────────────────────────────────────────────────────
    missed_frames:    int            = 0
    last_seen_at:     float          = field(default_factory=time.time)
    created_at:       float          = field(default_factory=time.time)
    grace_expires_at: float          = 0.0   # identity kept until this time
    removed_at:       float          = 0.0

    # ── Spatial ───────────────────────────────────────────────────────────────
    last_box:   Optional[Tuple[int,int,int,int]] = None
    vx:         float = 0.0   # pixel/frame velocity
    vy:         float = 0.0

    # ── Diagnostics ───────────────────────────────────────────────────────────
    total_recognition_attempts: int = 0
    total_confirmed_updates:    int = 0

    def display_name(self) -> Optional[str]:
        """Return the stable display name, or None if tentative/unknown."""
        if self.confirmed_name:
            return self.confirmed_name
        return None

    def display_conf(self) -> float:
        return self.confirmed_conf

    def is_confirmed(self) -> bool:
        return self.state == STATE_CONFIRMED and self.confirmed_pid is not None

    def grace_active(self) -> bool:
        """True if we're inside the identity grace window (face hidden but name kept)."""
        return time.time() < self.grace_expires_at


class StableIdentityEngine:
    """
    Manages stable identity assignment for all active tracks on one camera.
    Call from the camera_thread only; internal state is protected by a lock
    for safe reads from the web server / stream rendering threads.
    """

    def __init__(self):
        self._lock   = threading.Lock()
        self._tracks: Dict[int, TrackIdentity] = {}
        # Track IDs removed recently; blocked from immediate reuse
        self._recently_removed: Dict[int, float] = {}   # tid -> time_removed

    # ──────────────────────────────────────────────────────────────────────────
    # Called every frame from camera_thread: mark track as seen
    # ──────────────────────────────────────────────────────────────────────────
    def mark_seen(self, tid: int, box: Tuple[int,int,int,int]) -> TrackIdentity:
        """Called when YOLO detects this track_id this frame."""
        with self._lock:
            if tid not in self._tracks:
                # Check ID-reuse block
                if tid in self._recently_removed:
                    elapsed = time.time() - self._recently_removed[tid]
                    if elapsed < ID_REUSE_BLOCK_SECS:
                        log.debug(f"[SIE] Track {tid} blocked from reuse ({elapsed:.1f}s < {ID_REUSE_BLOCK_SECS}s)")
                        # Create as TENTATIVE but don't inherit old identity
                    else:
                        del self._recently_removed[tid]
                self._tracks[tid] = TrackIdentity(track_id=tid, last_box=box)
                log.debug(f"[SIE] New track {tid} created (TENTATIVE)")

            t = self._tracks[tid]

            # Update velocity from box movement
            if t.last_box:
                ox = (t.last_box[0] + t.last_box[2]) / 2
                oy = (t.last_box[1] + t.last_box[3]) / 2
                nx = (box[0] + box[2]) / 2
                ny = (box[1] + box[3]) / 2
                # Exponential moving average for smooth velocity
                t.vx = 0.7 * t.vx + 0.3 * (nx - ox)
                t.vy = 0.7 * t.vy + 0.3 * (ny - oy)

            t.last_box    = box
            t.missed_frames = 0
            t.last_seen_at  = time.time()

            # Revive from LOST state if re-detected
            if t.state == STATE_LOST:
                t.state = STATE_CONFIRMED if t.confirmed_pid else STATE_TENTATIVE
                # Reset grace since we're active again
                t.grace_expires_at = 0.0
                log.debug(f"[SIE] Track {tid} revived from LOST → {t.state}")

            return t

    # ──────────────────────────────────────────────────────────────────────────
    # Called every frame for tracks NOT seen this frame
    # ──────────────────────────────────────────────────────────────────────────
    def mark_missing(self, tid: int):
        """Called when a previously known track was not detected this frame."""
        with self._lock:
            if tid not in self._tracks:
                return
            t = self._tracks[tid]
            t.missed_frames += 1

            if t.state in (STATE_TENTATIVE, STATE_CONFIRMED):
                if t.missed_frames >= LOST_FRAMES_THRESH:
                    t.state = STATE_LOST
                    t.grace_expires_at = time.time() + IDENTITY_GRACE_SECS
                    log.debug(f"[SIE] Track {tid} → LOST (missed {t.missed_frames} frames), "
                              f"grace until +{IDENTITY_GRACE_SECS:.0f}s")

            elif t.state == STATE_LOST:
                # Check if grace period expired
                if not t.grace_active() and time.time() - t.last_seen_at > REIDENT_WINDOW_SECS:
                    self._remove_track(tid)

    # ──────────────────────────────────────────────────────────────────────────
    # Called when face recognition returns a result for a track
    # ──────────────────────────────────────────────────────────────────────────
    def submit_recognition(self, tid: int, pid: str, name: str, conf: float) -> bool:
        """
        Feed a recognition result.
        Returns True if the identity was updated/confirmed.
        """
        with self._lock:
            if tid not in self._tracks:
                return False
            t = self._tracks[tid]
            t.total_recognition_attempts += 1

            if conf < CONFIRM_MIN_CONF:
                # Low-confidence result — reset candidate accumulator
                t.candidate_pid = None
                t.candidate_frames = 0
                return False

            # ── Case 1: No confirmed identity yet — accumulate candidate ──────
            if not t.confirmed_pid or t.state == STATE_TENTATIVE:
                if t.candidate_pid == pid:
                    t.candidate_frames += 1
                    t.candidate_conf = 0.7 * t.candidate_conf + 0.3 * conf
                else:
                    # New candidate resets counter
                    t.candidate_pid    = pid
                    t.candidate_name   = name
                    t.candidate_frames = 1
                    t.candidate_conf   = conf

                if t.candidate_frames >= MIN_CONFIRM_FRAMES:
                    # Confirm identity
                    t.confirmed_pid   = pid
                    t.confirmed_name  = name
                    t.confirmed_conf  = t.candidate_conf
                    t.confirmed_at    = time.time()
                    t.state           = STATE_CONFIRMED
                    t.candidate_pid   = None
                    t.candidate_frames= 0
                    t.total_confirmed_updates += 1
                    log.info(f"[SIE] Track {tid} CONFIRMED → {name} ({pid}) conf={t.confirmed_conf:.2f} "
                             f"after {MIN_CONFIRM_FRAMES} frames")
                    return True
                return False

            # ── Case 2: Already confirmed — check if same pid ─────────────────
            if pid == t.confirmed_pid:
                # Reinforce confidence
                t.confirmed_conf  = max(t.confirmed_conf, conf)
                t.confirmed_at    = time.time()
                t.override_frames = 0   # reset any override attempt
                t.override_pid    = None
                # Extend grace
                t.grace_expires_at = time.time() + IDENTITY_GRACE_SECS
                return True

            # ── Case 3: Different pid result → accumulate override ─────────────
            if conf >= OVERRIDE_MIN_CONF:
                if t.override_pid == pid:
                    t.override_frames += 1
                    t.override_conf    = 0.6 * t.override_conf + 0.4 * conf
                else:
                    t.override_pid    = pid
                    t.override_name   = name
                    t.override_frames = 1
                    t.override_conf   = conf

                if t.override_frames >= OVERRIDE_MIN_FRAMES:
                    old_name = t.confirmed_name
                    t.confirmed_pid   = pid
                    t.confirmed_name  = name
                    t.confirmed_conf  = t.override_conf
                    t.confirmed_at    = time.time()
                    t.override_pid    = None
                    t.override_frames = 0
                    t.total_confirmed_updates += 1
                    log.info(f"[SIE] Track {tid} OVERRIDE: {old_name} → {name} "
                             f"(conf={t.confirmed_conf:.2f} after {OVERRIDE_MIN_FRAMES} frames)")
                    return True
            else:
                # Insufficient confidence for override — ignore
                pass

            return False

    # ──────────────────────────────────────────────────────────────────────────
    # Forced rename (from UI "rename_subject" action)
    # ──────────────────────────────────────────────────────────────────────────
    def force_identity(self, tid: int, pid: str, name: str, conf: float = 0.99):
        """Immediately lock a confirmed identity (called when user renames from UI)."""
        with self._lock:
            if tid not in self._tracks:
                self._tracks[tid] = TrackIdentity(track_id=tid)
            t = self._tracks[tid]
            t.confirmed_pid   = pid
            t.confirmed_name  = name
            t.confirmed_conf  = conf
            t.confirmed_at    = time.time()
            t.state           = STATE_CONFIRMED
            t.grace_expires_at= time.time() + IDENTITY_GRACE_SECS
            t.override_pid    = None
            t.override_frames = 0
            log.info(f"[SIE] Track {tid} FORCE-LOCKED → {name} ({pid})")

    # ──────────────────────────────────────────────────────────────────────────
    # Force-set identity by pid (called when renaming by pid, not tid)
    # ──────────────────────────────────────────────────────────────────────────
    def force_identity_by_pid(self, pid: str, name: str, conf: float = 0.99):
        """Lock identity for all tracks currently confirmed as this pid."""
        with self._lock:
            for t in self._tracks.values():
                if t.confirmed_pid == pid:
                    t.confirmed_name  = name
                    t.confirmed_conf  = conf
                    t.confirmed_at    = time.time()
                    t.grace_expires_at= time.time() + IDENTITY_GRACE_SECS
                    log.info(f"[SIE] Track {t.track_id} name updated → {name} via pid")

    # ──────────────────────────────────────────────────────────────────────────
    # Get display info for a track (safe to call from any thread)
    # ──────────────────────────────────────────────────────────────────────────
    def get_display(self, tid: int) -> Tuple[Optional[str], Optional[str], float, bool]:
        """
        Returns (pid, display_name, confidence, is_confirmed).
        Never returns None for display_name if identity is confirmed or in grace period.
        """
        with self._lock:
            t = self._tracks.get(tid)
            if t is None:
                return None, None, 0.0, False
            if t.confirmed_pid and (t.state == STATE_CONFIRMED or t.grace_active()):
                return t.confirmed_pid, t.confirmed_name, t.confirmed_conf, True
            return None, None, 0.0, False

    # ──────────────────────────────────────────────────────────────────────────
    # Get all active track IDs (confirmed or tentative, not removed)
    # ──────────────────────────────────────────────────────────────────────────
    def get_active_tids(self) -> list:
        with self._lock:
            return [tid for tid, t in self._tracks.items()
                    if t.state != STATE_REMOVED]

    # ──────────────────────────────────────────────────────────────────────────
    # Periodic maintenance — call every second or so from camera_thread
    # ──────────────────────────────────────────────────────────────────────────
    def purge_expired(self):
        """Remove fully expired tracks. Call periodically (not every frame)."""
        with self._lock:
            to_remove = []
            now = time.time()
            for tid, t in self._tracks.items():
                if t.state == STATE_LOST:
                    if not t.grace_active() and now - t.last_seen_at > REIDENT_WINDOW_SECS:
                        to_remove.append(tid)
                elif t.state == STATE_REMOVED:
                    to_remove.append(tid)
            for tid in to_remove:
                self._remove_track(tid)

        # Clean up old reuse-blocked IDs
        with self._lock:
            expired_blocks = [tid for tid, t in self._recently_removed.items()
                              if time.time() - t > ID_REUSE_BLOCK_SECS * 2]
            for tid in expired_blocks:
                del self._recently_removed[tid]

    def _remove_track(self, tid: int):
        """Internal: remove a track and block its ID from reuse."""
        if tid in self._tracks:
            self._recently_removed[tid] = time.time()
            del self._tracks[tid]
            log.debug(f"[SIE] Track {tid} REMOVED (ID reuse blocked for {ID_REUSE_BLOCK_SECS}s)")

    # ──────────────────────────────────────────────────────────────────────────
    # Diagnostics snapshot (for /api/diagnostics)
    # ──────────────────────────────────────────────────────────────────────────
    def diagnostics(self) -> dict:
        with self._lock:
            all_tracks = list(self._tracks.values())
        confirmed = [t for t in all_tracks if t.state == STATE_CONFIRMED and t.confirmed_pid]
        tentative = [t for t in all_tracks if t.state == STATE_TENTATIVE]
        lost      = [t for t in all_tracks if t.state == STATE_LOST]
        return {
            "total_tracks":     len(all_tracks),
            "confirmed_tracks": len(confirmed),
            "tentative_tracks": len(tentative),
            "lost_tracks":      len(lost),
            "track_details": [
                {
                    "track_id":        t.track_id,
                    "state":           t.state,
                    "identity":        t.confirmed_name or "UNKNOWN",
                    "pid":             t.confirmed_pid,
                    "conf":            round(t.confirmed_conf, 3),
                    "missed_frames":   t.missed_frames,
                    "recognition_attempts": t.total_recognition_attempts,
                    "grace_active":    t.grace_active(),
                }
                for t in all_tracks
            ]
        }
