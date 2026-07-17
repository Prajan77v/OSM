# ══════════════════════════════════════════════════════════════════════════════
# HUMAN ACTIVITY & EXPRESSION ANALYSIS ENGINE (HAAE) — OMS v9.0
# ══════════════════════════════════════════════════════════════════════════════
"""
Standalone module providing:
  • EmotionAnalyzer     — facial expression recognition (deepface with fallbacks)
  • ActivityScorer      — kinematic float score 0.0–1.0 derived from BehaviorRecord
  • AttentionEstimator  — proxy-based attention level (HIGH/MEDIUM/LOW/UNKNOWN)
  • HAEARecord          — per-person state container
  • HumanActivityExpressionEngine — orchestrates all sub-engines
  • haae_pool           — separate ThreadPoolExecutor (never contends with face_pool)
  • Telegram formatters for emotion and activity events

All inference is non-blocking: submitted to haae_pool and collected via
Future polling on the NEXT frame. Zero additional latency on the camera thread.
"""

import math
import threading
import time
import logging
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

app_log = logging.getLogger("OMS")

# ── Optional dependency: deepface ──────────────────────────────────────────────
DEEPFACE_AVAILABLE = False
_df_import_attempted = False

def _try_import_deepface():
    global DEEPFACE_AVAILABLE, _df_import_attempted
    if _df_import_attempted:
        return DEEPFACE_AVAILABLE
    _df_import_attempted = True
    try:
        from deepface import DeepFace  # noqa: F401
        DEEPFACE_AVAILABLE = True
        app_log.info("[HAAE] DeepFace emotion recognition loaded successfully.")
    except ImportError:
        app_log.warning(
            "[HAAE] DeepFace not installed. Emotion analysis disabled. "
            "Install with: pip install deepface tf-keras"
        )
        DEEPFACE_AVAILABLE = False
    return DEEPFACE_AVAILABLE

# Try to import at module load (non-fatal)
_try_import_deepface()

# ── Config defaults (overridden by main.py after Config is loaded) ─────────────
HAAE_EMOTION_FRAME_INTERVAL:  int   = 8    # analyze emotion every N frames per person
HAAE_EMOTION_ALERT_COOLDOWN:  float = 300.0  # seconds between Telegram alerts per emotion/person
HAAE_RUNNING_SPEED_THRESHOLD: float = 120.0  # px/sec
HAAE_RUNNING_ALERT_COOLDOWN:  float = 60.0   # seconds between RUNNING alerts
HAAE_ATTENTION_MIN_CONF:      float = 0.5    # face confidence for HIGH attention
HAAE_ENABLED:                 bool  = True   # master switch

# ── Emotion metadata ──────────────────────────────────────────────────────────
EMOTION_EMOJI = {
    "happy":     "😊",
    "neutral":   "😐",
    "sad":       "😢",
    "angry":     "😠",
    "surprise":  "😲",
    "fear":      "😨",
    "disgusted": "🤢",
    "disgust":   "🤢",
}

EMOTION_ALERT_SET = {"angry", "fear", "surprise"}  # emotions that trigger Telegram alerts

# ── Separate thread pool — never competes with face_pool ─────────────────────
haae_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="HAAE")

# ══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class HAEARecord:
    pid: str
    # Emotion state
    emotion: str = "Neutral"
    emotion_score: float = 0.0
    emotion_history: deque = field(default_factory=lambda: deque(maxlen=10))
    # Activity state
    activity_score: float = 0.5
    activity_label: str = "ACTIVE"   # RUNNING / ACTIVE / IDLE
    # Attention state
    attention_level: str = "UNKNOWN"  # HIGH / MEDIUM / LOW / UNKNOWN
    # Presence timing
    first_seen: float = field(default_factory=time.time)
    # Async emotion analysis
    _emotion_future: Any = field(default=None, repr=False, compare=False)
    last_emotion_frame: int = 0
    # Anti-spam cooldowns
    emotion_alerted_at: Dict[str, float] = field(default_factory=dict)
    running_alerted_at: float = 0.0
    # Grace-period tracking (mirrors BehaviorRecord pattern)
    pending_removal: bool = False
    removed_at: float = 0.0

    def presence_duration_str(self) -> str:
        s = int(time.time() - self.first_seen)
        if s < 60:
            return f"{s}s"
        m, s = divmod(s, 60)
        if m < 60:
            return f"{m}m {s:02d}s"
        h, m = divmod(m, 60)
        return f"{h}h {m:02d}m"

    def emotion_display(self) -> str:
        emoji = EMOTION_EMOJI.get(self.emotion.lower(), "🤔")
        pct = int(self.emotion_score * 100)
        return f"{emoji} {self.emotion.capitalize()} {pct}%"

    def activity_display(self) -> str:
        if self.activity_label == "RUNNING":
            return "🏃 RUNNING"
        elif self.activity_label == "ACTIVE":
            return "⚡ ACTIVE"
        else:
            return "🧍 IDLE"

    def attention_display(self) -> str:
        if self.attention_level == "HIGH":
            return "👁 HIGH"
        elif self.attention_level == "MEDIUM":
            return "👁 MED"
        elif self.attention_level == "LOW":
            return "👁 LOW"
        return "👁 ---"


# ══════════════════════════════════════════════════════════════════════════════
# EMOTION ANALYZER
# ══════════════════════════════════════════════════════════════════════════════

class EmotionAnalyzer:
    """Analyzes facial expression from a face crop using DeepFace.
    Thread-safe; uses an internal lock to serialize DeepFace model calls.
    """
    def __init__(self):
        self._lock = threading.Lock()

    def analyze(self, face_bgr: np.ndarray) -> Optional[Tuple[str, float]]:
        """Returns (emotion_label, confidence_0_to_1) or None on failure."""
        if not DEEPFACE_AVAILABLE or not HAAE_ENABLED:
            return None
        if face_bgr is None or face_bgr.size == 0:
            return None
        # Minimum face size check to avoid garbage results
        h, w = face_bgr.shape[:2]
        if h < 24 or w < 24:
            return None
        try:
            from deepface import DeepFace
            with self._lock:
                result = DeepFace.analyze(
                    img_path=face_bgr,
                    actions=["emotion"],
                    enforce_detection=False,
                    silent=True,
                )
            # DeepFace may return a list or a single dict
            if isinstance(result, list):
                result = result[0]
            dominant = result.get("dominant_emotion", "neutral").lower()
            scores   = result.get("emotion", {})
            score    = scores.get(dominant, 0.0) / 100.0   # DeepFace gives 0–100
            return dominant, float(score)
        except Exception as e:
            app_log.debug(f"[HAAE] Emotion analysis error: {e}")
            return None


# ══════════════════════════════════════════════════════════════════════════════
# ACTIVITY SCORER
# ══════════════════════════════════════════════════════════════════════════════

class ActivityScorer:
    """Derives a continuous activity score 0.0–1.0 from existing BehaviorRecord data.
    No new inference — pure kinematic math. Zero latency, called on every frame.
    """

    def score(self, positions: deque, pos_times: deque,
              direction_changes: deque, still_start_time: float,
              status: str) -> Tuple[float, str]:
        """
        Returns (score_0_to_1, label).
        label is one of: RUNNING, ACTIVE, IDLE
        """
        now = time.time()

        # ── Component 1: Short-window velocity (last 3 positions, 40% weight) ──
        vel_score = 0.0
        if len(positions) >= 3 and len(pos_times) >= 3:
            pos_list  = list(positions)
            time_list = list(pos_times)
            speeds = []
            for i in range(max(0, len(pos_list)-3), len(pos_list)-1):
                dt = time_list[i+1] - time_list[i]
                if dt > 0:
                    dx = pos_list[i+1][0] - pos_list[i][0]
                    dy = pos_list[i+1][1] - pos_list[i][1]
                    speeds.append(math.hypot(dx, dy) / dt)
            if speeds:
                avg_speed = sum(speeds) / len(speeds)
                # Normalise: 0→0, 60 px/s→0.5, 120 px/s→1.0
                vel_score = min(1.0, avg_speed / HAAE_RUNNING_SPEED_THRESHOLD)
        else:
            vel_score = 0.5 if status == "ACTIVE" else 0.0

        # ── Component 2: Direction change rate (30% weight) ───────────────────
        dir_score = 0.0
        recent_changes = [t for t in direction_changes if now - t < 15.0]
        # 0 changes→0, 5 changes (pacing threshold)→0.5, 10+→1.0
        dir_score = min(1.0, len(recent_changes) / 10.0)

        # ── Component 3: Stillness component (30% weight) ─────────────────────
        still_elapsed = now - still_start_time if still_start_time > 0 else 0.0
        # 0 seconds still → 1.0 moving; 30+ seconds still → 0.0
        still_score = max(0.0, 1.0 - still_elapsed / 30.0)

        # ── Weighted combination ───────────────────────────────────────────────
        raw = (vel_score * 0.40) + (dir_score * 0.30) + (still_score * 0.30)
        score = max(0.0, min(1.0, raw))

        # ── Label mapping ──────────────────────────────────────────────────────
        if vel_score >= 1.0 and score >= 0.75:
            label = "RUNNING"
        elif score >= 0.35:
            label = "ACTIVE"
        else:
            label = "IDLE"

        return score, label


# ══════════════════════════════════════════════════════════════════════════════
# ATTENTION ESTIMATOR
# ══════════════════════════════════════════════════════════════════════════════

class AttentionEstimator:
    """Proxy-based attention estimation.
    HIGH   = face is large (close), stable, frontal, high confidence
    MEDIUM = face present but smaller or moving
    LOW    = face is tiny, occluded, or person looking away
    UNKNOWN = no face crop available this update
    """

    def estimate(self, face_crop: Optional[np.ndarray],
                 face_conf: float = 0.0,
                 position_stability: float = 1.0) -> str:
        """
        Args:
            face_crop: BGR face crop (may be None if not detected)
            face_conf: YuNet face detection confidence 0.0–1.0
            position_stability: 1.0 = very stable, 0.0 = jittery
        """
        if face_crop is None or face_crop.size == 0:
            return "UNKNOWN"
        h, w = face_crop.shape[:2]
        area = h * w
        # Face area proxy — larger = closer to camera = more engaged
        if area >= 90 * 90 and face_conf >= HAAE_ATTENTION_MIN_CONF and position_stability >= 0.6:
            return "HIGH"
        elif area >= 36 * 36 and face_conf >= 0.3:
            return "MEDIUM"
        else:
            return "LOW"


# ══════════════════════════════════════════════════════════════════════════════
# HUMAN ACTIVITY & EXPRESSION ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class HumanActivityExpressionEngine:
    """Orchestrates EmotionAnalyzer, ActivityScorer, AttentionEstimator for a
    single camera's tracked persons. Each CameraState gets its own instance.
    """

    def __init__(self):
        self._records: Dict[str, HAEARecord] = {}
        self._emotion_analyzer  = EmotionAnalyzer()
        self._activity_scorer   = ActivityScorer()
        self._attention_estimator = AttentionEstimator()
        self._lock = threading.Lock()

    # ── Record management ─────────────────────────────────────────────────────

    def get(self, pid: str) -> HAEARecord:
        with self._lock:
            if pid not in self._records:
                self._records[pid] = HAEARecord(pid=pid)
            rec = self._records[pid]
            if rec.pending_removal:
                rec.pending_removal = False
                rec.removed_at = 0.0
            return rec

    def soft_remove(self, pid: str):
        """Mirror of BehaviorEngine.soft_remove — 45-second grace period."""
        with self._lock:
            rec = self._records.get(pid)
            if rec:
                rec.pending_removal = True
                rec.removed_at = time.time()

    def remove(self, pid: str):
        with self._lock:
            self._records.pop(pid, None)

    def purge_expired_removals(self, grace_secs: float = 45.0):
        now = time.time()
        with self._lock:
            expired = [p for p, r in self._records.items()
                       if r.pending_removal and (now - r.removed_at) > grace_secs]
            for p in expired:
                del self._records[p]

    # ── Core update methods ───────────────────────────────────────────────────

    def update_activity(self, pid: str, behavior_rec, frame_n: int):
        """Update activity score/label from existing BehaviorRecord kinematics.
        Called every frame — zero latency (no inference).
        """
        if not HAAE_ENABLED:
            return
        rec = self.get(pid)
        score, label = self._activity_scorer.score(
            positions=behavior_rec.positions,
            pos_times=behavior_rec.pos_times,
            direction_changes=behavior_rec.direction_changes,
            still_start_time=behavior_rec.still_start_time,
            status=behavior_rec.status,
        )
        rec.activity_score = score
        rec.activity_label = label

    def submit_emotion(self, pid: str, face_crop: np.ndarray,
                       frame_n: int, pool: ThreadPoolExecutor):
        """Submit async emotion analysis if gating allows. Non-blocking."""
        if not self.should_submit_emotion(pid, frame_n):
            return
        rec = self.get(pid)
        rec.last_emotion_frame = frame_n
        crop_copy = face_crop.copy()
        rec._emotion_future = pool.submit(self._emotion_analyzer.analyze, crop_copy)

    def should_submit_emotion(self, pid: str, frame_n: int) -> bool:
        """Cheap preflight so callers can avoid cropping/copying when gated."""
        if not HAAE_ENABLED or not DEEPFACE_AVAILABLE:
            return False
        rec = self.get(pid)
        if frame_n - rec.last_emotion_frame < HAAE_EMOTION_FRAME_INTERVAL:
            return False
        return rec._emotion_future is None or rec._emotion_future.done()

    def collect_emotion(self, pid: str) -> Optional[Tuple[str, float]]:
        """Poll completed emotion Future (non-blocking). Returns result if ready."""
        if not HAAE_ENABLED:
            return None
        rec = self.get(pid)
        fut = rec._emotion_future
        if fut is None or not fut.done():
            return None
        rec._emotion_future = None
        try:
            result = fut.result()
        except Exception as e:
            app_log.debug(f"[HAAE] collect_emotion error for {pid}: {e}")
            return None
        if result is not None:
            emotion, score = result
            rec.emotion = emotion.capitalize()
            rec.emotion_score = score
            rec.emotion_history.append((emotion, score, time.time()))
        return result

    def update_attention(self, pid: str, face_crop: Optional[np.ndarray],
                         face_conf: float = 0.0, position_stability: float = 1.0):
        """Update attention level estimate. Called when a face crop is available."""
        if not HAAE_ENABLED:
            return
        rec = self.get(pid)
        rec.attention_level = self._attention_estimator.estimate(
            face_crop, face_conf, position_stability
        )

    # ── Display helpers ───────────────────────────────────────────────────────

    def get_display(self, pid: str) -> Tuple[str, str, str, str]:
        """Returns (emotion_str, activity_str, attention_str, duration_str).
        Safe to call from the rendering thread with no locks held.
        """
        with self._lock:
            rec = self._records.get(pid)
        if rec is None:
            return ("😐 Neutral 0%", "⚡ ACTIVE", "👁 ---", "0s")
        return (
            rec.emotion_display(),
            rec.activity_display(),
            rec.attention_display(),
            rec.presence_duration_str(),
        )

    def get_record_snapshot(self, pid: str) -> Optional[dict]:
        """Returns a JSON-serializable snapshot for telemetry."""
        with self._lock:
            rec = self._records.get(pid)
        if rec is None:
            return None
        return {
            "pid":            rec.pid,
            "emotion":        rec.emotion,
            "emotion_score":  round(rec.emotion_score, 3),
            "activity_label": rec.activity_label,
            "activity_score": round(rec.activity_score, 3),
            "attention":      rec.attention_level,
            "duration_secs":  int(time.time() - rec.first_seen),
            "duration_str":   rec.presence_duration_str(),
        }

    def get_all_for_telemetry(self) -> List[dict]:
        """Returns list of all non-pending-removal records as dicts."""
        with self._lock:
            pids = [p for p, r in self._records.items() if not r.pending_removal]
        out = []
        for pid in pids:
            snap = self.get_record_snapshot(pid)
            if snap:
                out.append(snap)
        return out

    # ── Alert generation ──────────────────────────────────────────────────────

    def check_alerts(self, pid: str, name: str) -> List[dict]:
        """Returns list of alert dicts that should be sent via NotificationQueue.
        Called from the camera thread after update_activity and collect_emotion.
        Each dict: {'type': 'RUNNING'|'EMOTION', 'emotion': str, 'score': float}
        """
        if not HAAE_ENABLED:
            return []
        alerts = []
        now = time.time()
        rec = self.get(pid)

        # RUNNING alert
        if rec.activity_label == "RUNNING":
            if now - rec.running_alerted_at >= HAAE_RUNNING_ALERT_COOLDOWN:
                rec.running_alerted_at = now
                alerts.append({"type": "RUNNING"})

        # Emotion alerts for dangerous/notable emotions
        emotion_lower = rec.emotion.lower()
        if emotion_lower in EMOTION_ALERT_SET and rec.emotion_score >= 0.65:
            last = rec.emotion_alerted_at.get(emotion_lower, 0.0)
            if now - last >= HAAE_EMOTION_ALERT_COOLDOWN:
                rec.emotion_alerted_at[emotion_lower] = now
                alerts.append({
                    "type":    "EMOTION",
                    "emotion": rec.emotion,
                    "score":   rec.emotion_score,
                })
        return alerts


# ══════════════════════════════════════════════════════════════════════════════
# TELEGRAM FORMATTERS
# ══════════════════════════════════════════════════════════════════════════════

def _tg_running(cam: str, pid: str, name: str, ts: str) -> str:
    """Formats a RUNNING detection Telegram alert."""
    return (
        "🏃 OMS ACTIVITY ALERT\n━━━━━━━━━━━━━━━━━━━\n\n"
        "🧠 EVENT TYPE\nRUNNING DETECTED\n\n"
        f"📷 CAMERA\n{cam}\n\n🆔 TRACK ID\n{pid}\n\n"
        f"👤 SUBJECT\n{name}\n\n⏰ TIME\n{ts}\n\n"
        "🔥 THREAT LEVEL\nORANGE\n\n"
        "🛰 AI ANALYSIS\nABNORMAL MOVEMENT SPEED DETECTED\n"
        "POSSIBLE EMERGENCY OR SECURITY BREACH\n\n"
        "━━━━━━━━━━━━━━━━━━━\nOMS • ACTIVITY INTELLIGENCE ENGINE"
    )


def _tg_emotion_alert(cam: str, pid: str, name: str,
                      emotion: str, score: float, ts: str) -> str:
    """Formats an emotion-based Telegram alert."""
    emoji = EMOTION_EMOJI.get(emotion.lower(), "⚠")
    threat = "HIGH" if emotion.lower() in {"angry", "fear"} else "MEDIUM"
    analysis_map = {
        "angry":    "HOSTILE EXPRESSION DETECTED\nPOTENTIAL AGGRESSION OR CONFLICT",
        "fear":     "FEARFUL EXPRESSION DETECTED\nPOTENTIAL DISTRESS OR THREAT NEARBY",
        "surprise": "SURPRISE EXPRESSION DETECTED\nUNEXPECTED EVENT RESPONSE",
    }
    analysis = analysis_map.get(emotion.lower(), "NOTABLE EXPRESSION DETECTED")
    return (
        f"{emoji} OMS EXPRESSION ALERT\n━━━━━━━━━━━━━━━━━━━\n\n"
        "🧠 EVENT TYPE\nEMOTION DETECTED\n\n"
        f"📷 CAMERA\n{cam}\n\n🆔 TRACK ID\n{pid}\n\n"
        f"👤 SUBJECT\n{name}\n\n"
        f"😶 EXPRESSION\n{emotion.upper()}\n\n"
        f"🎯 CONFIDENCE\n{score:.0%}\n\n"
        f"⏰ TIME\n{ts}\n\n"
        f"🔥 THREAT LEVEL\n{threat}\n\n"
        f"🛰 AI ANALYSIS\n{analysis}\n\n"
        "━━━━━━━━━━━━━━━━━━━\nOMS • EXPRESSION ANALYSIS MODULE"
    )


# ══════════════════════════════════════════════════════════════════════════════
# CONFIG LOADER (called by main.py after Config is initialised)
# ══════════════════════════════════════════════════════════════════════════════

def configure_haae(cfg_dict: dict):
    """Apply haae config section from config.yaml.
    Called once from main.py after Config is loaded.
    """
    global HAAE_EMOTION_FRAME_INTERVAL, HAAE_EMOTION_ALERT_COOLDOWN
    global HAAE_RUNNING_SPEED_THRESHOLD, HAAE_RUNNING_ALERT_COOLDOWN
    global HAAE_ATTENTION_MIN_CONF, HAAE_ENABLED

    haae = cfg_dict.get("haae", {})
    HAAE_ENABLED                = haae.get("enabled", True)
    HAAE_EMOTION_FRAME_INTERVAL = int(haae.get("emotion_frame_interval", 8))
    HAAE_EMOTION_ALERT_COOLDOWN = float(haae.get("emotion_alert_cooldown", 300.0))
    HAAE_RUNNING_SPEED_THRESHOLD= float(haae.get("running_speed_threshold", 120.0))
    HAAE_RUNNING_ALERT_COOLDOWN = float(haae.get("running_alert_cooldown", 60.0))
    HAAE_ATTENTION_MIN_CONF     = float(haae.get("attention_frontal_min_conf", 0.5))

    status = "ENABLED" if HAAE_ENABLED else "DISABLED"
    df_status = "DeepFace LOADED" if DEEPFACE_AVAILABLE else "DeepFace NOT INSTALLED (emotion analysis off)"
    app_log.info(
        f"[HAAE] Engine {status} | Emotion interval={HAAE_EMOTION_FRAME_INTERVAL} frames | "
        f"Running threshold={HAAE_RUNNING_SPEED_THRESHOLD}px/s | {df_status}"
    )
