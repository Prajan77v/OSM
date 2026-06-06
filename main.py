"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   OMS - Object Monitoring System v9.0                                        ║
║   Military-Grade Autonomous AI Surveillance Supercomputer                    ║
║   YOLO + YuNet/SFace Face ID + Object Ownership + Zone Restrictions          ║
║   Behavior Anomaly Engine + SQLite DB + YAML Config + Cyberpunk HUD          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations

import csv
import gc
import hashlib
import json
import logging
import logging.handlers
import math
import os
import platform
import queue
import random
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.request
from collections import Counter, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

# ── Frozen Executable Path Resolution ─────────────────────────────────────────
IS_FROZEN = getattr(sys, 'frozen', False)
if IS_FROZEN:
    WORKING_DIR = Path(sys.executable).parent.resolve()
    BUNDLE_DIR = Path(sys._MEIPASS).resolve()
else:
    WORKING_DIR = Path(__file__).parent.resolve()
    BUNDLE_DIR = Path(__file__).parent.resolve()

# ── Load .env secrets before anything else ────────────────────────────────────
def _load_env(path: str = str(WORKING_DIR / ".env")):
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    except FileNotFoundError:
        pass

_load_env()

# ── Load YAML config ──────────────────────────────────────────────────────────
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

def _load_yaml(path: str = str(WORKING_DIR / "config.yaml")) -> dict:
    if not YAML_AVAILABLE:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}

_CFG = _load_yaml()

def _cfg(*keys, default=None):
    d = _CFG
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, None)
        if d is None:
            return default
    return d

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX   = platform.system() == "Linux"

# ── OPTIONAL IMPORTS ──────────────────────────────────────────────────────────
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

# Statically disabled dlib face_recognition to prevent CUDA loading freezes on Windows. Falling back to stable YuNet/SFace.
FACE_RECOG_AVAILABLE = False

try:
    import win32gui
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
    CUDA_DEVICE    = torch.cuda.get_device_name(0) if CUDA_AVAILABLE else "CPU"
except ImportError:
    CUDA_AVAILABLE = False
    CUDA_DEVICE    = "CPU"

if IS_WINDOWS:
    try:
        import winsound
        WINSOUND_AVAILABLE = True
    except ImportError:
        WINSOUND_AVAILABLE = False
else:
    WINSOUND_AVAILABLE = False

# ══════════════════════════════════════════════════════════════════════════════
# HARDWARE PROFILE
# ══════════════════════════════════════════════════════════════════════════════
def _detect_profile() -> str:
    if CUDA_AVAILABLE: return "HIGH"
    cores  = os.cpu_count() or 2
    ram_gb = (psutil.virtual_memory().total / (1024**3)) if PSUTIL_AVAILABLE else 4.0
    if cores >= 6 and ram_gb >= 8: return "MEDIUM"
    return "LOW"

HW_PROFILE = _detect_profile()

print("╔══════════════════════════════════════════════════════════════════════════════╗")
print("║            OMS  ——  OBJECT MONITORING SYSTEM  v9.0  BOOT SEQUENCE            ║")
print("║                    AUTONOMOUS AI SURVEILLANCE SUPERCOMPUTER                  ║")
print("╚══════════════════════════════════════════════════════════════════════════════╝")
print(f"[✦] Hardware Profile:  {HW_PROFILE}")
print(f"[✦] CUDA Acceleration: {'ENABLED' if CUDA_AVAILABLE else 'DISABLED'}")
print(f"[✦] Neural GPU:        {CUDA_DEVICE}")
print(f"[✦] YOLO Engine:       {'✔ ONLINE (ultralytics)' if YOLO_AVAILABLE else '✘ OFFLINE (pip install ultralytics)'}")
print(f"[✦] Face Recognition:  {'✔ ONLINE (face_recognition)' if FACE_RECOG_AVAILABLE else '~ YUNET/SFACE DL FALLBACK'}")
print(f"[✦] System Monitor:    {'✔ ONLINE (psutil)' if PSUTIL_AVAILABLE else '✘ OFFLINE'}")
print(f"[✦] YAML Config:       {'✔ LOADED (config.yaml)' if YAML_AVAILABLE and _CFG else '~ DEFAULTS'}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION — Reads from YAML + .env, falls back to sane defaults
# ══════════════════════════════════════════════════════════════════════════════
class Config:
    USERNAME       = os.environ.get("OMS_OPERATOR",         _cfg("operator","username", default="Prajan"))
    BOT_TOKEN      = os.environ.get("TELEGRAM_BOT_TOKEN",   _cfg("threat", "tg_token", default="8938780809:AAHzpgv_fbfbmXJ9x_ui44LY83CWnTWfKPo"))
    CHAT_ID        = os.environ.get("TELEGRAM_CHAT_ID",     _cfg("threat", "tg_chat_id", default="8076971661"))
    TG_TIMEOUT     = 10
    TG_MAX_RETRIES = _cfg("threat","max_retries", default=3)
    TG_RETRY_DELAY = _cfg("threat","retry_delay",  default=2.0)
    TG_QUEUE_SIZE  = _cfg("threat","queue_size",   default=128)

    COOLDOWN: Dict[str, float] = _cfg("threat","cooldown", default={
        "PERSON_ENTERED": 60, "PERSON_RETURNED": 60, "PERSON_LEFT": 45,
        "INTRUDER": 30, "OBJ_ADDED": 0, "OBJ_REMOVED": 0,
        "SYSTEM": 0, "BASELINE": 0,
    })
    TG_MSG_HASH_DEDUP_SECS = _cfg("threat","dedup_secs", default=60)

    # Camera configs — built from YAML or fallback
    @staticmethod
    def _load_cameras() -> List[dict]:
        cams = _cfg("cameras")
        if cams:
            return [{"source": c.get("source", "NONE"),
                     "name": c.get("name","CAM"),
                     "enabled": c.get("enabled", True),
                     "location": c.get("location", "Monitored Sector")} for c in cams]
        return [
            {"source": 0,      "name": "LOCAL CAM",      "enabled": True, "location": "Main Entrance Sector"},
            {"source": "NONE", "name": "CCTV NODE-2",    "enabled": True, "location": "Office Sector B"},
            {"source": "NONE", "name": "CCTV NODE-3",    "enabled": True, "location": "Restricted Storage Area"},
            {"source": "NONE", "name": "PHONE / IP CAM", "enabled": True, "location": "Mobile Sector D"},
        ]

    CAMERA_CONFIGS: List[dict] = _load_cameras.__func__()
    focused_cam_idx: int = -1

    MODEL_NAME  = str(BUNDLE_DIR / _cfg("detection","model",HW_PROFILE, default={"LOW":"yolov8n.pt","MEDIUM":"yolov8n.pt","HIGH":"yolov8s.pt"}[HW_PROFILE]))
    DEVICE      = "cuda" if CUDA_AVAILABLE else "cpu"
    CONFIDENCE  = _cfg("detection","confidence", default=0.45)

    FRAME_W = _cfg("detection","frame_w", default=640)
    FRAME_H = _cfg("detection","frame_h", default=360)
    DET_W   = _cfg("detection","det_w",HW_PROFILE, default={"LOW":320,"MEDIUM":416,"HIGH":640}[HW_PROFILE])
    DET_H   = _cfg("detection","det_h",HW_PROFILE, default={"LOW":192,"MEDIUM":256,"HIGH":384}[HW_PROFILE])

    PROCESS_EVERY_N    = _cfg("detection","process_every_n",HW_PROFILE, default={"LOW":4,"MEDIUM":3,"HIGH":2}[HW_PROFILE])
    TRACK_PERSIST      = True
    MOTION_THRESH_INIT = _cfg("detection","motion_thresh_init", default=300)
    MOTION_CALIB_FRAMES= _cfg("detection","motion_calib_frames", default=30)
    IDLE_SKIP_EXTRA    = _cfg("detection","idle_skip_extra", default=2)
    ABSENT_CYCLES_THRESH = _cfg("detection","absent_cycles_thresh", default=50)

    FACE_MATCH_THRESH   = _cfg("face_recognition","match_threshold", default=0.60)
    DETECT_NEW_IDS      = _cfg("face_recognition","detect_new_ids", default=True)
    FACE_DETECT_MODEL   = "cnn" if CUDA_AVAILABLE else "hog"
    FACE_POOL_WORKERS   = _cfg("face_recognition","pool_workers",HW_PROFILE, default={"LOW":1,"MEDIUM":2,"HIGH":3}[HW_PROFILE])
    FACE_RECHECK_CYCLES = _cfg("face_recognition","recheck_cycles",HW_PROFILE, default={"LOW":120,"MEDIUM":90,"HIGH":60}[HW_PROFILE])
    KNOWN_FACES_DIR     = str(WORKING_DIR / _cfg("face_recognition","known_faces_dir", default="faces/known"))
    YUNET_MODEL_PATH    = str(BUNDLE_DIR / _cfg("face_recognition","yunet_model_path", default="models/face_detection_yunet_2023mar.onnx"))
    SFACE_MODEL_PATH    = str(BUNDLE_DIR / _cfg("face_recognition","sface_model_path", default="models/face_recognition_sface_2021dec.onnx"))
    YUNET_MODEL_URL     = _cfg("face_recognition","yunet_model_url", default="https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx")
    SFACE_MODEL_URL     = _cfg("face_recognition","sface_model_url", default="https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx")

    LOITER_SECS          = _cfg("behavior","loiter_secs",      default=20.0)
    PACE_DIR_CHANGES     = _cfg("behavior","pace_direction_changes", default=5)
    PACE_WINDOW_SECS     = _cfg("behavior","pace_window_secs", default=15.0)
    RUN_SPEED_THRESHOLD  = _cfg("behavior","run_speed_threshold", default=120.0)

    OWNER_PROXIMITY_IOU  = _cfg("ownership","proximity_iou_threshold", default=0.05)
    ABANDONMENT_SECS     = _cfg("ownership","abandonment_secs", default=8.0)

    LOG_DIR       = WORKING_DIR / _cfg("storage","log_dir",    default="logs")
    SQLITE_DB     = WORKING_DIR / _cfg("storage","sqlite_db",  default="logs/OMS.db")
    FACES_DB_FILE = WORKING_DIR / _cfg("storage","faces_db_json", default="logs/faces_db.json")
    MODELS_DIR    = BUNDLE_DIR / _cfg("storage","models_dir", default="models")
    ALARM_WAV     = str(BUNDLE_DIR / "alarm.wav")

    WINDOW_W   = _cfg("display","window_w", default=1920)
    WINDOW_H   = _cfg("display","window_h", default=1080)
    TARGET_FPS = _cfg("display","target_fps",HW_PROFILE, default={"LOW":24,"MEDIUM":28,"HIGH":30}[HW_PROFILE])
    SIDE_W     = _cfg("display","side_w", default=260)
    EVENT_W    = _cfg("display","event_w", default=280)
    TOP_H      = _cfg("display","top_h",  default=65)
    FOOTER_H   = _cfg("display","footer_h", default=45)

    DB_SAVE_SECS      = _cfg("storage","db_save_secs", default=45)
    CAM_QUEUE_SIZE    = _cfg("storage","cam_queue_size", default=1)
    OVERLOAD_CPU_PCT  = _cfg("storage","overload_cpu_pct", default=88.0)
    GC_GEN0_FRAMES    = _cfg("storage","gc_gen0_frames", default=25)
    GC_GEN1_SECS      = _cfg("storage","gc_gen1_secs", default=30)
    SPARKLINE_SAMPLES = _cfg("display","sparkline_samples", default=40)

# ══════════════════════════════════════════════════════════════════════════════
# ZONE CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class MonitoringZone:
    name:         str
    color:        Tuple[int,int,int]
    threat_level: str
    rect_pct:     Tuple[float,float,float,float]  # x1,y1,x2,y2 0.0-1.0

    def pixel_rect(self, W: int, H: int) -> Tuple[int,int,int,int]:
        x1,y1,x2,y2 = self.rect_pct
        return (int(x1*W), int(y1*H), int(x2*W), int(y2*H))

    def contains(self, cx: float, cy: float, W: int, H: int) -> bool:
        px1,py1,px2,py2 = self.pixel_rect(W, H)
        return px1 <= cx <= px2 and py1 <= cy <= py2

def _load_zones() -> List[MonitoringZone]:
    return []

ZONES: List[MonitoringZone] = _load_zones()

# ══════════════════════════════════════════════════════════════════════════════
# CINEMATIC LUXURY BLACK & GOLD AI PALETTE  (OpenCV = BGR order)
# ══════════════════════════════════════════════════════════════════════════════
# BGR format: (Blue, Green, Red)
C_BG      = (5,   5,   5)       # Deep cinematic black #050505
C_PANEL   = (22,  20,  18)      # Warm panel BG rgba(18,20,22,0.82)
C_GOLD    = (55,  175, 212)     # Primary Gold #D4AF37 in BGR
C_GOLD_BRIGHT = (30, 210, 255)  # Bright warm gold glow #FFD21E in BGR
C_GOLD2   = (40,  155, 190)     # Soft muted gold
C_AMBER   = (10,  180, 245)     # Glowing amber
C_CYAN    = (255, 230, 0)       # Accent Cyan #00E5FF in BGR
C_MAGENTA = (200,  60, 220)     # Vibrant magenta/crimson accent
C_GREEN   = (120, 255, 0)       # Success green #00FF78 in BGR
C_RED     = (60,   60, 255)     # Alert Red #FF3C3C in BGR
C_ORANGE  = (0,   140, 255)     # Warning Orange #FF8C00 in BGR
C_YELLOW  = (55,  175, 212)     # Gold alias
C_BLUE    = (255, 180,  50)     # Info blue
C_BORDER  = (35,  48,  60)      # Subtle warm border
C_TEXT    = (245, 245, 245)     # Clean off-white #F5F5F5
C_DIM     = (160, 155, 150)     # Muted warm gray #9CA3AF
C_WHITE   = (248, 248, 248)     # Near-white
C_SCAN    = (2,   4,   2)       # Subtle scanline tint
C_GLOW    = (20,  80,  100)     # Gold ambient glow layer

selected_cam_idx = 0
_nav_tabs = ["DASHBOARD", "LIVE VIEW", "ANALYTICS", "DATABASE", "EVENTS", "CONFIG", "SYSTEM"]
_active_tab = 0
is_fs_state = False
hud_overlay_active = True
cam_area_pct = 0.76

THREAT_COLORS = {"GREEN":C_GREEN,"YELLOW":C_GOLD,"ORANGE":C_ORANGE,"RED":C_RED,"CRITICAL":C_MAGENTA}
THREAT_RANK   = {"GREEN":0,"YELLOW":1,"ORANGE":2,"RED":3,"CRITICAL":4}

# ══════════════════════════════════════════════════════════════════════════════
# THREAT ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class ThreatEngine:
    def __init__(self):
        self._lock  = threading.Lock()
        self.level  = "GREEN"
        self.factors: List[str] = []
        self._decay = 0.0

    def raise_threat(self, level: str, reason: str):
        pass

    def tick(self):
        self.level = "GREEN"
        self.factors = []

    @property
    def color(self): return C_GREEN

threat_engine = ThreatEngine()

# ══════════════════════════════════════════════════════════════════════════════
# ADAPTIVE CONTROLLER
# ══════════════════════════════════════════════════════════════════════════════
class AdaptiveController:
    def __init__(self):
        self._lock      = threading.Lock()
        self.fps_target = Config.TARGET_FPS
        self.det_w      = Config.DET_W
        self.det_h      = Config.DET_H
        self.skip_n     = Config.PROCESS_EVERY_N
        self.overloaded = False
        self._hist: deque = deque(maxlen=8)
        self._last_t    = 0.0

    def update(self):
        now = time.time()
        if now - self._last_t < 2.0: return
        self._last_t = now
        cpu = psutil.cpu_percent(interval=None) if PSUTIL_AVAILABLE else 50.0
        self._hist.append(cpu)
        avg = sum(self._hist) / len(self._hist)
        with self._lock:
            if avg > Config.OVERLOAD_CPU_PCT:
                self.fps_target = max(10, Config.TARGET_FPS // 3)
                self.skip_n     = Config.PROCESS_EVERY_N * 3
                self.det_w      = max(192, Config.DET_W // 2)
                self.det_h      = max(128, Config.DET_H // 2)
                self.overloaded = True
            elif avg > 72:
                self.fps_target = max(16, int(Config.TARGET_FPS * 0.7))
                self.skip_n     = Config.PROCESS_EVERY_N + 2
                self.det_w      = max(256, int(Config.DET_W * 0.75))
                self.det_h      = max(160, int(Config.DET_H * 0.75))
                self.overloaded = False
            else:
                self.fps_target = Config.TARGET_FPS
                self.skip_n     = Config.PROCESS_EVERY_N
                self.det_w      = Config.DET_W
                self.det_h      = Config.DET_H
                self.overloaded = False

    @property
    def frame_ms(self) -> int: return max(1, int(1000 / self.fps_target))

adaptive = AdaptiveController()

# ══════════════════════════════════════════════════════════════════════════════
# WATCHDOG SELF-DIAGNOSTICS
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class DiagSnapshot:
    ts:         float = field(default_factory=time.time)
    cpu_pct:    float = 0.0
    ram_pct:    float = 0.0
    ram_used_gb:float = 0.0
    gpu_pct:    float = 0.0
    overloaded: bool  = False
    fps_all:    List[float] = field(default_factory=list)
    queue_depths: Dict[str, int] = field(default_factory=dict)

_diag = DiagSnapshot()
_diag_lock = threading.Lock()

def _diag_worker(cameras):
    global _diag
    while True:
        try:
            time.sleep(2)
            snap = DiagSnapshot()
            if PSUTIL_AVAILABLE:
                snap.cpu_pct     = psutil.cpu_percent(interval=None)
                vm               = psutil.virtual_memory()
                snap.ram_pct     = vm.percent
                snap.ram_used_gb = vm.used / (1024**3)
            snap.overloaded = adaptive.overloaded
            snap.fps_all    = [cs.fps_inst for cs in cameras]
            with _diag_lock:
                _diag = snap
        except Exception:
            pass

# ══════════════════════════════════════════════════════════════════════════════
# TEXT-TO-SPEECH
# ══════════════════════════════════════════════════════════════════════════════
def speak(text: str):
    def _run():
        if IS_WINDOWS:
            try:
                import win32com.client
                win32com.client.Dispatch("SAPI.SpVoice").Speak(text); return
            except Exception: pass
            try:
                esc = text.replace("'", "''")
                cmd = f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{esc}')"
                subprocess.run(["powershell","-Command",cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception: pass
        elif platform.system() == "Darwin":
            try: subprocess.run(["say", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception: pass
        else:
            try:
                p = shutil.which("spd-say") or shutil.which("espeak")
                if p: subprocess.run([p, text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception: pass
    threading.Thread(target=_run, daemon=True, name="TTS").start()

# ══════════════════════════════════════════════════════════════════════════════
# LOGGING SETUP
# ══════════════════════════════════════════════════════════════════════════════
def _setup_logging():
    Config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    app = logging.getLogger("OMS.app"); app.setLevel(logging.DEBUG)
    sh  = logging.StreamHandler(); sh.setLevel(logging.INFO); sh.setFormatter(fmt)
    fh  = logging.handlers.RotatingFileHandler(Config.LOG_DIR/"app.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    fh.setLevel(logging.DEBUG); fh.setFormatter(fmt)
    app.addHandler(sh); app.addHandler(fh)
    evt = logging.getLogger("OMS.evt"); evt.setLevel(logging.INFO)
    efh = logging.handlers.RotatingFileHandler(Config.LOG_DIR/"events.jsonl", maxBytes=10_000_000, backupCount=10, encoding="utf-8")
    efh.setFormatter(logging.Formatter("%(message)s")); evt.addHandler(efh)
    return app, evt

app_log, evt_log = _setup_logging()

# ══════════════════════════════════════════════════════════════════════════════
# SQLITE DATABASE ENGINE
# ══════════════════════════════════════════════════════════════════════════════
_db_lock = threading.Lock()
_db_conn: Optional[sqlite3.Connection] = None

def _init_db():
    global _db_conn
    Config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    (WORKING_DIR / "faces/known").mkdir(parents=True, exist_ok=True)
    (WORKING_DIR / "faces/captured").mkdir(parents=True, exist_ok=True)
    (WORKING_DIR / "faces/unknown").mkdir(parents=True, exist_ok=True)
    _db_conn = sqlite3.connect(str(Config.SQLITE_DB), check_same_thread=False)
    _db_conn.execute("PRAGMA journal_mode=WAL")
    _db_conn.execute("PRAGMA synchronous=NORMAL")
    c = _db_conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS persons (
            pid TEXT PRIMARY KEY, name TEXT, known INTEGER,
            first_seen TEXT, last_seen TEXT, visit_count INTEGER DEFAULT 0,
            threat_level TEXT DEFAULT 'GREEN'
        );
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pid TEXT, camera TEXT, entered_at TEXT, exited_at TEXT,
            confidence REAL, threat_level TEXT
        );
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT, event TEXT, camera TEXT, pid TEXT,
            object TEXT, detail TEXT, threat_level TEXT,
            snapshot_path TEXT
        );
        CREATE TABLE IF NOT EXISTS object_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT, camera TEXT, label TEXT,
            event TEXT, before_count INTEGER, after_count INTEGER,
            owner_pid TEXT
        );
        CREATE TABLE IF NOT EXISTS threat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT, level TEXT, reason TEXT, camera TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_incidents_ts ON incidents(ts);
        CREATE INDEX IF NOT EXISTS idx_visits_pid   ON visits(pid);
    """)
    _db_conn.commit()

def db_log_incident(ts, event, camera, pid, obj, detail, threat_level, snapshot_path=""):
    if _db_conn is None: return
    with _db_lock:
        try:
            _db_conn.execute(
                "INSERT INTO incidents(ts,event,camera,pid,object,detail,threat_level,snapshot_path) VALUES(?,?,?,?,?,?,?,?)",
                (ts, event, camera, pid, obj, detail, threat_level, snapshot_path))
            _db_conn.commit()
        except Exception as e: app_log.debug(f"DB incident: {e}")

def db_log_person(pid, name, known, ts):
    if _db_conn is None: return
    with _db_lock:
        try:
            _db_conn.execute("""
                INSERT INTO persons(pid,name,known,first_seen,last_seen,visit_count) VALUES(?,?,?,?,?,1)
                ON CONFLICT(pid) DO UPDATE SET name=excluded.name, last_seen=excluded.last_seen,
                visit_count=visit_count+1""",
                (pid, name, 1 if known else 0, ts, ts))
            _db_conn.commit()
        except Exception as e: app_log.debug(f"DB person: {e}")

def db_log_visit_enter(pid, camera, ts, conf, threat):
    if _db_conn is None: return
    with _db_lock:
        try:
            _db_conn.execute("INSERT INTO visits(pid,camera,entered_at,confidence,threat_level) VALUES(?,?,?,?,?)",
                             (pid, camera, ts, conf, threat))
            _db_conn.commit()
        except Exception as e: app_log.debug(f"DB visit enter: {e}")

def db_log_threat(ts, level, reason, camera):
    if _db_conn is None: return
    with _db_lock:
        try:
            _db_conn.execute("INSERT INTO threat_logs(ts,level,reason,camera) VALUES(?,?,?,?)",
                             (ts, level, reason, camera))
            _db_conn.commit()
        except Exception as e: app_log.debug(f"DB threat: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# YUNET / SFACE — Deep Learning Face Recognition Fallback (no dlib!)
# ══════════════════════════════════════════════════════════════════════════════
YUNET_AVAILABLE = False
_yunet_detector  = None
_sface_recognizer= None

def _download_model(url: str, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if Path(path).exists(): return True
    try:
        app_log.info(f"[YUNET] Downloading {Path(path).name} ...")
        print(f"[OMS] Downloading neural face model: {Path(path).name}")
        urllib.request.urlretrieve(url, path)
        app_log.info(f"[YUNET] Downloaded {Path(path).name}")
        return True
    except Exception as e:
        app_log.error(f"[YUNET] Download failed: {e}")
        return False

def _init_yunet():
    global YUNET_AVAILABLE, _yunet_detector, _sface_recognizer
    if FACE_RECOG_AVAILABLE:
        return  # dlib version available, prefer it
    try:
        yu_ok = _download_model(Config.YUNET_MODEL_URL, Config.YUNET_MODEL_PATH)
        sf_ok = _download_model(Config.SFACE_MODEL_URL, Config.SFACE_MODEL_PATH)
        if not (yu_ok and sf_ok): return
        # Set score_threshold=0.45 to dramatically improve real-world face detection success rate
        _yunet_detector   = cv2.FaceDetectorYN.create(Config.YUNET_MODEL_PATH, "", (320, 320), 0.45)
        _sface_recognizer = cv2.FaceRecognizerSF.create(Config.SFACE_MODEL_PATH, "")
        YUNET_AVAILABLE   = True
        print("[OMS] ✔ YuNet + SFace Neural Face Engine ONLINE — No dlib required!")
        app_log.info("[YUNET] DL Face Recognition ONLINE")
    except Exception as e:
        app_log.error(f"[YUNET] Init failed: {e}")

# ── YuNet face encoding cache for known persons ───────────────────────────────
_yunet_enc_cache:  Dict[str, np.ndarray] = {}  # pid -> feature vector
_yunet_lock = threading.Lock()

def _yunet_encode(img_bgr: np.ndarray) -> Optional[np.ndarray]:
    if not YUNET_AVAILABLE: return None
    with _yunet_lock:
        try:
            h, w = img_bgr.shape[:2]
            if w < 30 or h < 30: return None
            
            # Dynamic Resolution Upgrade: If the crop is small, upscale it to 128x128
            # to significantly enhance landmark precision and match confidence scores!
            if w < 112 or h < 112:
                img_bgr = cv2.resize(img_bgr, (128, 128), interpolation=cv2.INTER_CUBIC)
                h, w = 128, 128
                
            _yunet_detector.setInputSize((w, h))
            _, faces = _yunet_detector.detect(img_bgr)
            
            # Smart Padding Fallback: If no face is detected on a tight crop,
            # pad the image with black borders on all sides to give YuNet convolutional layers context!
            if faces is None or len(faces) == 0:
                pad_h, pad_w = h // 2, w // 2
                padded = cv2.copyMakeBorder(img_bgr, pad_h, pad_h, pad_w, pad_w, cv2.BORDER_CONSTANT, value=[0, 0, 0])
                ph, pw = padded.shape[:2]
                _yunet_detector.setInputSize((pw, ph))
                _, faces = _yunet_detector.detect(padded)
                if faces is not None and len(faces) > 0:
                    face = faces[0]
                    aligned = _sface_recognizer.alignCrop(padded, face)
                    feat    = _sface_recognizer.feature(aligned)
                    return feat[0] if feat is not None else None
                return None
            
            face = faces[0]
            aligned = _sface_recognizer.alignCrop(img_bgr, face)
            feat    = _sface_recognizer.feature(aligned)
            return feat[0] if feat is not None else None
        except Exception as e:
            app_log.error(f"[YUNET] Encode exception: {e}")
            return None

def _yunet_match(enc: np.ndarray) -> Tuple[Optional[str], Optional[str], bool, float]:
    """Compare enc against all cached known encodings. Returns (pid, name, is_new, score)."""
    with _yunet_lock:
        best_score, best_pid = -1.0, None
        for pid, cached_enc in _yunet_enc_cache.items():
            try:
                score = float(_sface_recognizer.match(
                    enc.reshape(1,-1), cached_enc.reshape(1,-1), cv2.FaceRecognizerSF_FR_COSINE))
                if score > best_score:
                    best_score = score; best_pid = pid
            except Exception:
                pass
        # SFace Cosine matching standard threshold is 0.36; dlib distance is 0.60.
        thresh = 0.36 if Config.FACE_MATCH_THRESH >= 0.55 else Config.FACE_MATCH_THRESH
        if best_pid and best_score >= thresh:
            with _fdb_lock:
                name = faces_db.get(best_pid, {}).get("name", "Unknown")
            return best_pid, name, False, best_score
    return None, None, True, 0.0

def _yunet_detect_faces(frame: np.ndarray) -> List[Tuple[int,int,int,int]]:
    """Return list of (x1,y1,x2,y2) face boxes found in frame."""
    if not YUNET_AVAILABLE: return []
    with _yunet_lock:
        try:
            h, w = frame.shape[:2]
            _yunet_detector.setInputSize((w, h))
            _, faces = _yunet_detector.detect(frame)
            if faces is None: return []
            boxes = []
            for f in faces:
                x,y,fw,fh = int(f[0]),int(f[1]),int(f[2]),int(f[3])
                boxes.append((max(0,x), max(0,y), min(w-1,x+fw), min(h-1,y+fh)))
            return boxes
        except Exception:
            return []

# ══════════════════════════════════════════════════════════════════════════════
# EVENT LOGGING — ASCII TABLE + JSONL + SQLite
# ══════════════════════════════════════════════════════════════════════════════
_lq: queue.Queue    = queue.Queue(maxsize=8192)
_event_ring: deque  = deque(maxlen=100)
_event_ring_lock    = threading.Lock()
_data_stream: deque = deque(maxlen=20)
_log_file_lock      = threading.Lock()
_fdb_lock           = threading.RLock()   # defined early for forward refs

def _clean_cam_name(cam: str) -> str:
    if not cam or cam == "--": return "--"
    c = cam.upper()
    if "LOCAL" in c or "LOBBY" in c: return "Lobby Cam 01"
    if "NODE-2" in c or "OFFICE" in c: return "Office Cam 02"
    if "NODE-3" in c or "STORAGE" in c: return "Storage Cam 03"
    if "PHONE" in c or "MOBILE" in c: return "Mobile Cam 04"
    return cam[:20]

def _get_location(cam: str) -> str:
    c = cam.upper()
    if "LOCAL" in c or "LOBBY" in c: return "Main Entrance Sector"
    if "NODE-2" in c or "OFFICE" in c: return "Desk Sector B"
    if "NODE-3" in c or "STORAGE" in c: return "Restricted Storage Area"
    if "PHONE" in c or "MOBILE" in c: return "Mobile Sector D"
    return "Monitored Sector"

def _find_id_and_name(person_name: str) -> Tuple[str, str]:
    if not person_name or person_name == "--": return "--", "--"
    if "Intruder-" in person_name:
        pid = person_name.split("-")[-1]
        return pid, person_name
    with _fdb_lock:
        for pid, d in faces_db.items():
            if d.get("name","").lower() == person_name.lower():
                return pid, d.get("name", person_name)
    return "--", person_name

def _format_log_cols(ev, person_name, obj, detail):
    event_col = ev
    id_col = "—"
    name_obj_col = "—"
    details_col = detail if detail else "—"
    
    if ev == "SYSTEM_START":
        event_col = "SYSTEM START"
        details_col = "Surveillance system initialize"
    elif ev == "SYSTEM_SHUTDOWN":
        event_col = "SYSTEM STOP"
        details_col = "Surveillance session ended"
    elif ev == "BASELINE":
        event_col = "BASELINE"
        details_col = "Baseline snapshot saved"
    elif ev in ("PERSON_ENTERED", "PERSON_RETURNED"):
        pid, name = _find_id_and_name(person_name)
        id_col = pid if pid else "—"
        name_obj_col = name if name else "—"
        event_col = "RETURNED" if "Intruder" in name else "ARRIVED"
        visits = "1"
        if "visits=" in detail:
            try:
                for p in detail.split():
                    if p.startswith("visits="):
                        visits = p.split("=")[1]
            except:
                pass
        details_col = f"Visit #{visits}"
    elif ev == "PERSON_LEFT":
        pid, name = _find_id_and_name(person_name)
        id_col = pid if pid else "—"
        name_obj_col = name if name else "—"
        event_col = "LEFT"
        now_time = datetime.now().strftime("%H:%M:%S")
        details_col = f"Last seen {now_time}"
    elif ev == "OBJ_ADDED":
        event_col = "OBJ ADDED"
        name_obj_col = obj if obj else "—"
        before, after = "0", "1"
        if "->" in detail:
            try:
                before, after = detail.split("->")
            except:
                pass
        details_col = f"{before.strip()} → {after.strip()}"
    elif ev == "OBJ_REMOVED":
        event_col = "OBJ REMOVED"
        name_obj_col = obj if obj else "—"
        before, after = "1", "0"
        if "->" in detail:
            try:
                before, after = detail.split("->")
            except:
                pass
        details_col = f"{before.strip()} → {after.strip()}"
    elif ev == "ZONE_INTRUSION":
        event_col = "INTRUSION"
        id_col = person_name if person_name else "—"
        name_obj_col = obj if obj else "—"
        details_col = f"Zone Breach: {obj}"
    elif ev == "BEHAVIOR":
        event_col = "BEHAVIOR"
        id_col = person_name if person_name else "—"
        name_obj_col = obj if obj else "—"
        details_col = detail
        
    return event_col, id_col, name_obj_col, details_col

def append_to_pretty_log(ev, cam, person_name, obj, detail):
    log_path = Config.LOG_DIR / "events.log"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    div = "+-----------------------+------------------+------------+----------------------+--------------------------------+"
    hdr = "| TIMESTAMP             | EVENT            | OBJECT ID  | NAME                 | DETAIL                         |"
    ec, ic, nc, dc = _format_log_cols(ev, person_name, obj, detail)
    if cam:
        dc = f"[{_clean_cam_name(cam)}] {dc}"
    row = f"| {ts:<21} | {ec:<16} | {ic:<10} | {nc:<20} | {dc:<30} |"
    
    with _log_file_lock:
        try:
            exists = log_path.exists() and log_path.stat().st_size > 0
            if not exists:
                border = "=" * 113
                title = "OMS Object Monitoring System — EVENT LOG".center(113)
                start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                started = f"Started: {start_time}".center(113)
                
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(border + "\n")
                    f.write(title + "\n")
                    f.write(started + "\n")
                    f.write(border + "\n\n")
                    f.write(div + "\n")
                    f.write(hdr + "\n")
                    f.write(div + "\n")
                    f.write(row + "\n")
                    f.write(div + "\n")
            else:
                with open(log_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                while lines and not lines[-1].strip():
                    lines.pop()
                if lines and div in lines[-1]:
                    lines.pop()
                lines.append(row + "\n")
                lines.append(div + "\n")
                with open(log_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
        except Exception as e:
            app_log.error(f"Pretty log: {e}")

def _log_worker():
    while True:
        try:
            item = _lq.get(timeout=5)
            if item is None: break
            ev, cam, person, obj, detail = item
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            evt_log.info(json.dumps({"ts":ts,"event":ev,"camera":cam,"person":person,"object":obj,"detail":detail}))
            append_to_pretty_log(ev, cam, person, obj, detail)
            db_log_incident(ts, ev, _clean_cam_name(cam), person, obj, detail, threat_engine.level)
            clean_ev = ev
            if ev in ("PERSON_ENTERED","PERSON_RETURNED"):
                _, name = _find_id_and_name(person)
                if "Intruder" in name: clean_ev = "INTRUDER"
            short = f"[{ts[11:]}] {clean_ev:<16} {_clean_cam_name(cam):<14} {person}"
            with _event_ring_lock:
                _event_ring.append((short, ev, time.time()))
            hex_s = " ".join(f"{random.randint(0,255):02X}" for _ in range(8))
            _data_stream.append(f"{ts[11:]} >> {clean_ev[:8]} :: {hex_s}")
            app_log.info(f"{clean_ev:<18}| cam={_clean_cam_name(cam)} person={person} | {detail}")
        except queue.Empty: continue
        except Exception as e: print(f"[LOG-ERR] {e}")

threading.Thread(target=_log_worker, daemon=True, name="LogWorker").start()

def log_event(ev: str, camera: str="", person: str="--", obj: str="--", detail: str=""):
    try: _lq.put_nowait((ev, camera, person, obj, detail))
    except queue.Full: pass
    # Mirror to web dashboard
    try:
        import web_integration as _wi
        _ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _wi.record_event(_ts, ev, camera, person, detail)
    except Exception:
        pass

def export_csv(path: str = "logs/events_export.csv"):
    src = Config.LOG_DIR / "events.jsonl"
    if not src.exists(): return
    with open(src, encoding="utf-8") as f, open(path,"w",newline="",encoding="utf-8") as out:
        w = csv.DictWriter(out, fieldnames=["ts","event","camera","person","object","detail"])
        w.writeheader()
        for line in f:
            line = line.strip()
            if line:
                try: w.writerow(json.loads(line))
                except: pass
    app_log.info(f"CSV exported -> {path}")

def save_config_cameras(cameras):
    config_path = WORKING_DIR / "config.yaml"
    if not config_path.exists():
        return
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        cams_list = []
        for cs in cameras:
            cams_list.append({
                "id": cs.cam_id,
                "source": cs.source,
                "name": cs.name,
                "enabled": not cs.disconnected,
                "location": getattr(cs, "location", "Monitored Sector")
            })
        data["cameras"] = cams_list
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
        dist_config_path = WORKING_DIR / "dist" / "config.yaml"
        if dist_config_path.exists():
            with open(dist_config_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
        Config.CAMERA_CONFIGS = [{"source": c["source"], "name": c["name"], "enabled": c["enabled"], "location": c["location"]} for c in cams_list]
        app_log.info("Saved camera configurations to config.yaml")
    except Exception as e:
        app_log.error(f"Error saving camera config: {e}")

def reset_log_files(cameras=None):
    """Clear app.log, events.jsonl, events.log, clear SQLite events/visits, and reset Today's summary metrics."""
    # Truncate pretty events log
    with _log_file_lock:
        try:
            log_path = Config.LOG_DIR / "events.log"
            if log_path.exists():
                with open(log_path, "w", encoding="utf-8") as f:
                    f.truncate(0)
        except Exception as e:
            app_log.error(f"Reset pretty events log failed: {e}")

    # Truncate app.log and events.jsonl using the logging handlers
    try:
        for handler in app_log.handlers:
            if hasattr(handler, "stream") and handler.stream:
                try:
                    handler.stream.seek(0)
                    handler.stream.truncate(0)
                except Exception:
                    pass
    except Exception as e:
        app_log.error(f"Reset app_log failed: {e}")

    try:
        for handler in evt_log.handlers:
            if hasattr(handler, "stream") and handler.stream:
                try:
                    handler.stream.seek(0)
                    handler.stream.truncate(0)
                except Exception:
                    pass
    except Exception as e:
        app_log.error(f"Reset evt_log failed: {e}")

    # Clear visits in SQLite database
    with _db_lock:
        if _db_conn:
            try:
                _db_conn.execute("DELETE FROM visits")
                _db_conn.commit()
            except Exception as e:
                app_log.error(f"Reset DB visits failed: {e}")
                
    # Reset web integration event cache
    try:
        import web_integration as _wi
        _wi.clear_events()
    except Exception:
        pass

    # Reset running counters
    global _total_detections, _known_persons, _unknown_persons, _objs_added, _objs_removed, _alerts_generated
    _total_detections = 0
    _known_persons = 0
    _unknown_persons = 0
    _objs_added = 0
    _objs_removed = 0
    _alerts_generated = 0

    # Reset camera metrics
    if cameras:
        for cs in cameras:
            cs.persons_detected = 0
            cs.persons_left = 0

    # Reset faces database: remove intruders, reset known visitor count
    with _fdb_lock:
        to_delete = [pid for pid, d in faces_db.items() if not d.get("known", False)]
        for pid in to_delete:
            del faces_db[pid]
        for pid, d in faces_db.items():
            if d.get("known", False):
                d["visit_count"] = 0
        _save_db_json()

    app_log.info("System logs and visits database cleared.")
    speak("System logs reset.")

# ══════════════════════════════════════════════════════════════════════════════
# TELEGRAM NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════════════════
try:
    import requests as _requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

@dataclass
class Notification:
    kind:     str
    payload:  str
    caption:  str = ""
    priority: int = 5

class NotificationQueue:
    def __init__(self):
        self._q:       queue.PriorityQueue = queue.PriorityQueue(maxsize=Config.TG_QUEUE_SIZE)
        self._cooldown: Dict[str,float]   = {}
        self._hashes:   Dict[str,float]   = {}
        self._lock    = threading.Lock()
        self._counter = 0
        threading.Thread(target=self._worker, daemon=True, name="TG").start()

    def send_message(self, text:str, event_type:str="SYSTEM", camera:str="", person:str="", priority:int=5):
        key      = f"{event_type}:{camera}:{person}"
        cooldown = Config.COOLDOWN.get(event_type, 45)
        msg_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        now      = time.time()
        with self._lock:
            if cooldown > 0 and self._cooldown.get(key, 0) > now: return
            if self._hashes.get(msg_hash, 0) > now - Config.TG_MSG_HASH_DEDUP_SECS: return
            if cooldown > 0: self._cooldown[key] = now + cooldown
            self._hashes[msg_hash] = now
        self._enqueue(Notification("message", text, priority=priority))

    def send_photo(self, path:str, caption:str="", priority:int=6):
        self._enqueue(Notification("photo", path, caption=caption, priority=priority))

    def send_alert(self, text:str, photo_path:Optional[str]=None, event_type:str="SYSTEM",
                   camera:str="", person:str="", priority:int=5):
        self.send_message(text, event_type=event_type, camera=camera, person=person, priority=priority)
        if photo_path and os.path.exists(photo_path):
            self.send_photo(photo_path, caption=text[:200], priority=priority+1)

    def _enqueue(self, n: Notification):
        try:
            with self._lock:
                self._counter += 1; cnt = self._counter
            self._q.put_nowait((n.priority, cnt, n))
        except queue.Full: pass

    def _worker(self):
        while True:
            try:
                _, _, n = self._q.get(timeout=5)
                self._dispatch(n); self._q.task_done()
            except queue.Empty: continue
            except Exception as e: app_log.error(f"TG worker: {e}")

    def _dispatch(self, n: Notification):
        if not REQUESTS_AVAILABLE: return
        for attempt in range(1, Config.TG_MAX_RETRIES + 1):
            try:
                if n.kind == "message":
                    _requests.post(
                        f"https://api.telegram.org/bot{Config.BOT_TOKEN}/sendMessage",
                        json={"chat_id":Config.CHAT_ID, "text":n.payload},
                        timeout=Config.TG_TIMEOUT).raise_for_status()
                else:
                    if not os.path.exists(n.payload): return
                    with open(n.payload,"rb") as f:
                        _requests.post(
                            f"https://api.telegram.org/bot{Config.BOT_TOKEN}/sendPhoto",
                            files={"photo":f},
                            data={"chat_id":Config.CHAT_ID,"caption":n.caption},
                            timeout=Config.TG_TIMEOUT).raise_for_status()
                return
            except Exception as e:
                app_log.warning(f"[TG] attempt {attempt}: {e}")
                if attempt < Config.TG_MAX_RETRIES: time.sleep(Config.TG_RETRY_DELAY * attempt)

notif_queue = NotificationQueue()

def _tg_person_enter(cam, pid, name, visits, conf, ts):
    clean_cam = _clean_cam_name(cam); loc = _get_location(cam)
    if "Intruder" in name:
        t_id = name.split("-")[-1] if "-" in name else pid
        return (
            "🚨 OMS CRITICAL ALERT\n━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠ EVENT TYPE\nINTRUDER DETECTED\n\n"
            f"📷 CAMERA\n{clean_cam}\n\n🆔 TRACK ID\n{t_id}\n\n"
            f"👤 IDENTITY\n{name}\n\n🎯 CONFIDENCE\n{conf:.0%}\n\n"
            f"📍 LOCATION\n{loc}\n\n🕒 FIRST SEEN\n{datetime.now().strftime('%I:%M:%S %p')}\n\n"
            "🔥 THREAT LEVEL\nHIGH\n\n"
            "🧠 AI ANALYSIS\nUNKNOWN ENTITY DETECTED\nNO MATCH FOUND IN DATABASE\n\n"
            "📡 ACTIONS INITIATED\n✔ Snapshot Captured\n✔ Evidence Logged\n"
            "✔ Tracking Activated\n✔ Threat Monitoring Enabled\n\n"
            "━━━━━━━━━━━━━━━━━━━\nOMS • AI SECURITY NETWORK")
    else:
        return (
            "🟢 OMS AI ALERT\n━━━━━━━━━━━━━━━━━━━\n\n"
            "👤 EVENT TYPE\nPERSON ENTERED\n\n"
            f"📷 CAMERA\n{clean_cam}\n\n🆔 TRACK ID\n{pid}\n\n"
            f"🧠 IDENTITY\n{name}\n\n🎯 CONFIDENCE\n{conf:.0%}\n\n"
            f"📍 LOCATION\n{loc}\n\n⏰ TIME\n{ts}\n\n"
            "📊 THREAT LEVEL\nLOW\n\n🛰 STATUS\nAUTHORIZED PERSON DETECTED\n\n"
            "━━━━━━━━━━━━━━━━━━━\nOMS • OBJECT SENTINEL MATRIX")

def _tg_person_left(cam, pid, name, ts):
    clean_cam = _clean_cam_name(cam); loc = _get_location(cam)
    return (
        "🔵 OMS AI ALERT\n━━━━━━━━━━━━━━━━━━━\n\n"
        "👤 EVENT TYPE\nPERSON LEFT\n\n"
        f"📷 CAMERA\n{clean_cam}\n\n🆔 TRACK ID\n{pid}\n\n"
        f"🧠 IDENTITY\n{name}\n\n📍 LOCATION\n{loc}\n\n⏰ TIME\n{ts}\n\n"
        "📊 THREAT LEVEL\nLOW\n\n🛰 STATUS\nMONITORED SUBJECT DEPARTED\n\n"
        "━━━━━━━━━━━━━━━━━━━\nOMS • OBJECT SENTINEL MATRIX")

def _tg_obj(cam, ev, label, before, after, ts):
    clean_cam = _clean_cam_name(cam); loc = _get_location(cam)
    verb = "ADDED" if ev == "OBJ_ADDED" else "REMOVED"
    arrow = "📈" if ev == "OBJ_ADDED" else "📉"
    return (
        "⚠ OMS OBJECT ALERT\n━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 EVENT TYPE\nOBJECT {verb}\n\n📷 CAMERA\n{clean_cam}\n\n"
        f"🧠 OBJECT\n{label.capitalize()}\n\n{arrow} COUNT CHANGE\n{before} → {after}\n\n"
        f"📍 LAST KNOWN POSITION\n{loc}\n\n⏰ TIME\n{ts}\n\n"
        "🔥 THREAT LEVEL\nMEDIUM\n\n📸 FORENSIC SNAPSHOTS SAVED\n\n"
        "━━━━━━━━━━━━━━━━━━━\nOMS • FORENSIC TRACKING ENGINE")

def _tg_zone(cam, pid, name, zone_name, ts):
    clean_cam = _clean_cam_name(cam)
    return (
        "🔴 OMS ZONE INTRUSION ALERT\n━━━━━━━━━━━━━━━━━━━\n\n"
        "🚫 EVENT TYPE\nUNAUTHORIZED ZONE ACCESS\n\n"
        f"📷 CAMERA\n{clean_cam}\n\n🆔 TRACK ID\n{pid}\n\n"
        f"👤 IDENTITY\n{name}\n\n🗺 ZONE VIOLATED\n{zone_name}\n\n⏰ TIME\n{ts}\n\n"
        "🔥 THREAT LEVEL\nHIGH\n\n"
        "📡 ACTIONS\n✔ Zone Breach Logged\n✔ Evidence Captured\n✔ Alert Dispatched\n\n"
        "━━━━━━━━━━━━━━━━━━━\nOMS • ZONE CONTROL UNIT")

def _tg_behavior(cam, pid, name, behavior_type, ts):
    clean_cam = _clean_cam_name(cam)
    emoji = {"LOITERING":"⏳","PACING":"🔄","STILL":"🧍","ACTIVE":"🏃","ABANDONED_OBJ":"📦"}.get(behavior_type,"⚠")
    return (
        f"{emoji} OMS BEHAVIOR ALERT\n━━━━━━━━━━━━━━━━━━━\n\n"
        f"🧠 EVENT TYPE\n{behavior_type}\n\n📷 CAMERA\n{clean_cam}\n\n"
        f"🆔 TRACK ID\n{pid}\n\n👤 SUBJECT\n{name}\n\n⏰ TIME\n{ts}\n\n"
        "🔥 THREAT LEVEL\nORANGE\n\n"
        "🛰 AI ANALYSIS\nSUSPICIOUS BEHAVIOR PATTERN DETECTED\n\n"
        "━━━━━━━━━━━━━━━━━━━\nOMS • BEHAVIOR INTELLIGENCE ENGINE")

# ══════════════════════════════════════════════════════════════════════════════
# FACES DATABASE (JSON + SQLite sync)
# ══════════════════════════════════════════════════════════════════════════════
for _d in ["logs", "faces/known", "faces/unknown", "faces/captured", "models", "plugins"]:
    (WORKING_DIR / _d).mkdir(parents=True, exist_ok=True)

_next_pid = 1
faces_db: Dict[str, dict] = {}

def deduplicate_profiles():
    """Scan faces_db and merge/delete duplicate face profiles based on SFace embedding similarity."""
    if not YUNET_AVAILABLE or _sface_recognizer is None:
        return
    with _fdb_lock, _yunet_lock:
        pids = list(_yunet_enc_cache.keys())
        to_delete = set()
        for i in range(len(pids)):
            pid1 = pids[i]
            if pid1 in to_delete or pid1 not in faces_db:
                continue
            enc1 = _yunet_enc_cache[pid1]
            for j in range(i + 1, len(pids)):
                pid2 = pids[j]
                if pid2 in to_delete or pid2 not in faces_db:
                    continue
                enc2 = _yunet_enc_cache[pid2]
                try:
                    score = float(_sface_recognizer.match(
                        enc1.reshape(1,-1), enc2.reshape(1,-1), cv2.FaceRecognizerSF_FR_COSINE))
                    if score >= 0.40:
                        id1 = int(pid1[1:]) if pid1[1:].isdigit() else 0
                        id2 = int(pid2[1:]) if pid2[1:].isdigit() else 0
                        known1 = faces_db[pid1].get("known", False)
                        known2 = faces_db[pid2].get("known", False)
                        if known1 and not known2:
                            older, newer = pid1, pid2
                        elif known2 and not known1:
                            older, newer = pid2, pid1
                        else:
                            older, newer = (pid1, pid2) if id1 < id2 else (pid2, pid1)
                        to_delete.add(newer)
                        app_log.info(f"[DEDUP] Detected duplicate faces: {pid1} ({faces_db[pid1].get('name')}) and {pid2} ({faces_db[pid2].get('name')}) with similarity {score:.2f}. Auto-deleting recent profile {newer}.")
                except Exception as e:
                    pass
        if to_delete:
            for pid in to_delete:
                photo = faces_db[pid].get("photo")
                if photo:
                    p_path = WORKING_DIR / photo
                    if p_path.exists() and "faces/captured" in str(p_path):
                        try: p_path.unlink()
                        except: pass
                if pid in faces_db:
                    del faces_db[pid]
                if pid in _yunet_enc_cache:
                    del _yunet_enc_cache[pid]

def _load_db_json():
    global faces_db
    if not Config.FACES_DB_FILE.exists(): faces_db = {}; return
    try:
        with open(Config.FACES_DB_FILE, encoding="utf-8") as f:
            db = json.load(f)
        for pid, d in db.items():
            d["in_scene"] = False
            if "encoding" in d and d["encoding"] is not None:
                enc_arr = np.array(d["encoding"], dtype=np.float32)
                d["encoding"] = enc_arr
                if YUNET_AVAILABLE:
                    with _yunet_lock:
                        _yunet_enc_cache[pid] = enc_arr
        faces_db = db
    except Exception as e: app_log.error(f"DB load: {e}"); faces_db = {}

def _save_db_json():
    deduplicate_profiles()
    out = {}
    with _fdb_lock:
        for pid, d in faces_db.items():
            out[pid] = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k,v in d.items()}
    tmp = Config.FACES_DB_FILE.with_suffix(".tmp")
    try:
        with open(tmp,"w",encoding="utf-8") as f: json.dump(out, f, indent=2)
        if IS_WINDOWS and Config.FACES_DB_FILE.exists(): Config.FACES_DB_FILE.unlink()
        tmp.rename(Config.FACES_DB_FILE)
    except Exception as e: app_log.error(f"DB save: {e}")

_load_db_json()
for _p in faces_db:
    try:
        n = int(_p[1:])
        if n >= _next_pid: _next_pid = n + 1
    except: pass

def _new_pid() -> str:
    global _next_pid
    p = f"P{_next_pid}"; _next_pid += 1; return p

def preload_known():
    if not FACE_RECOG_AVAILABLE and not YUNET_AVAILABLE: return
    loaded = []
    p = Path(Config.KNOWN_FACES_DIR)
    if not p.exists(): return
    for fp in p.iterdir():
        if fp.suffix.lower() not in (".jpg",".jpeg",".png"): continue
        name = fp.stem
        try:
            img = cv2.imread(str(fp))
            if img is None: continue
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            by_name = {d["name"].lower(): pid for pid,d in faces_db.items() if d.get("known")}

            if FACE_RECOG_AVAILABLE:
                rgb  = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                import face_recognition as _fr
                encs = _fr.face_encodings(rgb)
                if not encs: continue
                rel_photo = str(fp.relative_to(WORKING_DIR)) if WORKING_DIR in fp.parents else str(fp)
                if name.lower() in by_name:
                    pid = by_name[name.lower()]
                    faces_db[pid]["encoding"] = encs[0]
                    faces_db[pid]["photo"] = rel_photo
                else:
                    pid = _new_pid()
                    faces_db[pid] = {"name":name,"encoding":encs[0],"first_seen":now,
                                     "last_seen":now,"visit_count":0,"known":True,
                                     "photo":rel_photo,"in_scene":False}
                loaded.append(name)
            elif YUNET_AVAILABLE:
                enc = _yunet_encode(img)
                if enc is None: continue
                rel_photo = str(fp.relative_to(WORKING_DIR)) if WORKING_DIR in fp.parents else str(fp)
                if name.lower() in by_name:
                    pid = by_name[name.lower()]
                    faces_db[pid]["encoding"] = enc
                    faces_db[pid]["photo"] = rel_photo
                else:
                    pid = _new_pid()
                    faces_db[pid] = {"name":name,"encoding":enc,"first_seen":now,"last_seen":now,
                                     "visit_count":0,"known":True,"photo":rel_photo,"in_scene":False}
                with _yunet_lock:
                    _yunet_enc_cache[pid] = enc
                loaded.append(name)
        except Exception as e: app_log.error(f"Load face {fp.name}: {e}")
    _save_db_json()
    if loaded: app_log.info(f"Known faces loaded: {loaded}")

_enc_arr:  Optional[np.ndarray] = None
_enc_pids: List[str]            = []
_enc_dirty = True

def _rebuild_enc_cache():
    global _enc_arr, _enc_pids, _enc_dirty
    with _fdb_lock:
        pids      = [p for p,d in faces_db.items() if "encoding" in d]
        _enc_pids = pids
        _enc_arr  = np.array([faces_db[p]["encoding"] for p in pids]) if pids else None
        _enc_dirty = False

def match_face_dlib(enc):
    global _enc_dirty
    if _enc_dirty: _rebuild_enc_cache()
    if _enc_arr is None:
        pid, name, is_new = _register_face_dlib(enc)
        return pid, name, is_new, 1.0
    import face_recognition as _fr
    dists = _fr.face_distance(_enc_arr, enc)
    bi    = int(np.argmin(dists))
    dist  = float(dists[bi])
    if dist <= Config.FACE_MATCH_THRESH:
        pid = _enc_pids[bi]
        with _fdb_lock: name = faces_db[pid]["name"]
        conf = max(0.0, min(1.0, 1.0 - dist))
        return pid, name, False, conf
    pid, name, is_new = _register_face_dlib(enc)
    return pid, name, is_new, 1.0

def _register_face_dlib(enc):
    global _enc_dirty
    with _fdb_lock:
        pid  = _new_pid(); name = f"Intruder-{pid}"
        now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        faces_db[pid] = {"name":name,"encoding":enc,"first_seen":now,"last_seen":now,
                         "visit_count":0,"known":False,"photo":None,"in_scene":False}
        _enc_dirty = True; _save_db_json()
    return pid, name, True

def _register_face_yunet(enc):
    with _fdb_lock:
        pid  = _new_pid(); name = f"Intruder-{pid}"
        now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        faces_db[pid] = {"name":name,"encoding":enc,"first_seen":now,"last_seen":now,
                         "visit_count":0,"known":False,"photo":None,"in_scene":False}
    with _yunet_lock:
        _yunet_enc_cache[pid] = enc
    _save_db_json()
    return pid, name, True

def async_face(rgb_or_bgr: np.ndarray, is_bgr: bool = False):
    """Returns (pid, name, conf) or (None, None, 0.0) for one face from a crop."""
    if FACE_RECOG_AVAILABLE:
        try:
            import face_recognition as _fr
            rgb = cv2.cvtColor(rgb_or_bgr, cv2.COLOR_BGR2RGB) if is_bgr else rgb_or_bgr
            locs = _fr.face_locations(rgb, model=Config.FACE_DETECT_MODEL)
            if not locs:
                locs = _fr.face_locations(rgb, number_of_times_to_upsample=1, model="hog")
            if not locs: return None, None, 0.0
            encs = _fr.face_encodings(rgb, locs)
            if not encs: return None, None, 0.0
            pid, name, _, conf = match_face_dlib(encs[0])
            return pid, name, conf
        except Exception as e: app_log.debug(f"face dlib: {e}"); return None, None, 0.0
    elif YUNET_AVAILABLE:
        try:
            bgr = rgb_or_bgr if is_bgr else cv2.cvtColor(rgb_or_bgr, cv2.COLOR_RGB2BGR)
            enc = _yunet_encode(bgr)
            if enc is None: return None, None, 0.0
            pid, name, is_new, score = _yunet_match(enc)
            if is_new:
                pid, name, _ = _register_face_yunet(enc)
                score = 1.0
            return pid, name, score
        except Exception as e: app_log.debug(f"face yunet: {e}"); return None, None, 0.0
    return None, None, 0.0

face_pool = ThreadPoolExecutor(max_workers=Config.FACE_POOL_WORKERS, thread_name_prefix="Face")

def register_user_face(cameras, username: str = Config.USERNAME):
    global _enc_dirty
    if not FACE_RECOG_AVAILABLE and not YUNET_AVAILABLE:
        speak("Face recognition module offline."); return False
    
    # Try up to 30 attempts (approx. 3 seconds of stream) to capture a clear face
    for attempt in range(30):
        for cs in cameras:
            if not cs.online:
                continue
            frame = None
            with cs.frame_lock:
                if cs.latest_frame is not None: frame = cs.latest_frame.copy()
            if frame is not None:
                try:
                    if FACE_RECOG_AVAILABLE:
                        import face_recognition as _fr
                        rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        locs = _fr.face_locations(rgb, model=Config.FACE_DETECT_MODEL)
                        if not locs: locs = _fr.face_locations(rgb, number_of_times_to_upsample=1, model="hog")
                        if locs:
                            top, right, bottom, left = locs[0]
                            h, w, _ = frame.shape; pad = 35
                            crop = frame[max(0,top-pad):min(h,bottom+pad), max(0,left-pad):min(w,right+pad)]
                            out  = Path(Config.KNOWN_FACES_DIR) / f"{username}.jpg"
                            out.parent.mkdir(parents=True, exist_ok=True)
                            cv2.imwrite(str(out), crop)
                            preload_known()
                            _enc_dirty = True
                            log_event("USER_REGISTERED", camera=cs.name, person=username)
                            speak(f"Identity confirmed. Welcome, {username}.")
                            cs.warning_msg = f"[REGISTERED] {username}"; cs.warning_time = time.time()
                            return True
                    elif YUNET_AVAILABLE:
                        with _yunet_lock:
                            h, w = frame.shape[:2]
                            _yunet_detector.setInputSize((w, h))
                            _, faces = _yunet_detector.detect(frame)
                        
                        if faces is not None and len(faces) > 0:
                            face = faces[0]
                            x, y, fw, fh = int(face[0]), int(face[1]), int(face[2]), int(face[3])
                            x1, y1, x2, y2 = max(0, x), max(0, y), min(w-1, x+fw), min(h-1, y+fh)
                            
                            pad = int(fh * 0.3)
                            crop = frame[max(0,y1-pad):min(h,y2+pad), max(0,x1-pad):min(w,x2+pad)]
                            
                            with _yunet_lock:
                                aligned = _sface_recognizer.alignCrop(frame, face)
                                feat    = _sface_recognizer.feature(aligned)
                                enc = feat[0] if feat is not None else None
                                
                            if enc is not None:
                                with _fdb_lock:
                                    by_name = {d["name"].lower(): pid for pid,d in faces_db.items() if d.get("known")}
                                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                out = Path(Config.KNOWN_FACES_DIR) / f"{username}.jpg"
                                out.parent.mkdir(parents=True, exist_ok=True)
                                cv2.imwrite(str(out), crop)
                                rel_out = str(out.relative_to(WORKING_DIR)) if WORKING_DIR in out.parents else str(out)
                                if username.lower() in by_name:
                                    pid = by_name[username.lower()]
                                    with _fdb_lock:
                                        faces_db[pid]["photo"] = rel_out
                                else:
                                    pid = _new_pid()
                                    with _fdb_lock:
                                        faces_db[pid] = {"name":username,"first_seen":now,"last_seen":now,
                                                         "visit_count":0,"known":True,"photo":rel_out,"in_scene":False}
                                with _yunet_lock: _yunet_enc_cache[pid] = enc
                                _save_db_json()
                                preload_known()
                                _enc_dirty = True
                                log_event("USER_REGISTERED", camera=cs.name, person=username)
                                speak(f"Identity confirmed. Welcome, {username}.")
                                cs.warning_msg = f"[REGISTERED] {username}"; cs.warning_time = time.time()
                                return True
                except Exception as e: app_log.error(f"Register: {e}")
        time.sleep(0.1)
    
    speak("Registration failed. No face detected."); return False

# ══════════════════════════════════════════════════════════════════════════════
# SPATIAL TRACKER (centroid fallback for non-person objects)
# ══════════════════════════════════════════════════════════════════════════════
class SpatialTracker:
    def __init__(self):
        self.next_tid = 1000
        self.history: Dict[int, Tuple] = {}

    def track(self, boxes: List[Tuple]) -> List[int]:
        now   = time.time()
        stale = [t for t,(_, ts) in self.history.items() if now - ts > 2.0]
        for t in stale: del self.history[t]
        tids = []
        for box in boxes:
            x1,y1,x2,y2 = box
            cx,cy = (x1+x2)/2.0, (y1+y2)/2.0
            best_t, best_d = None, 110.0
            for tid,(pb,_) in self.history.items():
                px,py = (pb[0]+pb[2])/2.0, (pb[1]+pb[3])/2.0
                d = math.hypot(cx-px, cy-py)
                if d < best_d: best_d = d; best_t = tid
            tid = best_t if best_t is not None else self.next_tid
            if best_t is None: self.next_tid += 1
            self.history[tid] = (box, now)
            tids.append(tid)
        return tids

# ══════════════════════════════════════════════════════════════════════════════
# MOTION DETECTOR
# ══════════════════════════════════════════════════════════════════════════════
class MotionDetector:
    def __init__(self):
        self._mog    = cv2.createBackgroundSubtractorMOG2(history=150, varThreshold=32, detectShadows=False)
        self._sw, self._sh = 160, 90
        self._thresh = Config.MOTION_THRESH_INIT
        self._scores: deque = deque(maxlen=Config.MOTION_CALIB_FRAMES)
        self._ready  = False

    def has_motion(self, frame: np.ndarray) -> bool:
        small = cv2.resize(frame, (self._sw, self._sh), interpolation=cv2.INTER_NEAREST)
        gray  = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        mask  = self._mog.apply(gray)
        score = int(np.sum(mask > 120))
        if not self._ready:
            self._scores.append(score)
            if len(self._scores) >= Config.MOTION_CALIB_FRAMES:
                base = sorted(self._scores)[len(self._scores)//2]
                self._thresh = max(200, base*3); self._ready = True
        return score > self._thresh

# ══════════════════════════════════════════════════════════════════════════════
# BEHAVIOR ANALYSIS ENGINE
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class BehaviorRecord:
    pid:              str
    zone_entry_time:  Dict[str, float] = field(default_factory=dict)
    positions:        deque = field(default_factory=lambda: deque(maxlen=60))
    pos_times:        deque = field(default_factory=lambda: deque(maxlen=60))
    direction_changes:deque = field(default_factory=lambda: deque(maxlen=20))
    last_dir:         Optional[float] = None
    loitering_alerted: Dict[str, float] = field(default_factory=dict)
    pacing_alerted:   float = 0.0
    status:           str = "ACTIVE"
    still_ref_pos:    Optional[Tuple[float, float]] = None
    still_start_time: float = 0.0
    last_tg_status:   Optional[str] = "ACTIVE"

class BehaviorEngine:
    def __init__(self):
        self._records: Dict[str, BehaviorRecord] = {}

    def get(self, pid: str) -> BehaviorRecord:
        if pid not in self._records:
            self._records[pid] = BehaviorRecord(pid=pid)
        return self._records[pid]

    def update(self, pid: str, cx: float, cy: float, zones_in: List[str]) -> List[str]:
        """Update position and return list of anomaly event strings."""
        rec = self.get(pid)
        now = time.time()
        anomalies: List[str] = []

        # Store position + time
        if rec.positions:
            lx,ly = rec.positions[-1]
            dt = now - rec.pos_times[-1] if rec.pos_times else 1.0
            if dt > 0:
                speed = math.hypot(cx-lx, cy-ly) / dt
                # Direction change (pacing)
                if speed > 5:
                    angle = math.atan2(cy-ly, cx-lx)
                    if rec.last_dir is not None:
                        diff = abs(math.degrees(angle - rec.last_dir)) % 360
                        if diff > 120:  # sharp reversal
                            rec.direction_changes.append(now)
                    rec.last_dir = angle

        rec.positions.append((cx,cy)); rec.pos_times.append(now)

        # Still / Active detection
        if rec.still_ref_pos is None:
            rec.still_ref_pos = (cx, cy)
            rec.still_start_time = now
        else:
            dist = math.hypot(cx - rec.still_ref_pos[0], cy - rec.still_ref_pos[1])
            if dist > 35:
                if rec.status == "STILL":
                    rec.status = "ACTIVE"
                    if rec.last_tg_status != "ACTIVE":
                        anomalies.append("ACTIVE")
                        rec.last_tg_status = "ACTIVE"
                rec.still_ref_pos = (cx, cy)
                rec.still_start_time = now
            else:
                elapsed = now - rec.still_start_time
                if elapsed > 300:  # 5 minutes
                    if rec.status == "ACTIVE":
                        rec.status = "STILL"
                        if rec.last_tg_status != "STILL":
                            anomalies.append("STILL")
                            rec.last_tg_status = "STILL"

        # Pacing detection
        recent_changes = [t for t in rec.direction_changes if now-t < Config.PACE_WINDOW_SECS]
        if len(recent_changes) >= Config.PACE_DIR_CHANGES and now - rec.pacing_alerted > 30:
            anomalies.append("PACING")
            rec.pacing_alerted = now

        # Zone loitering
        for zone_name in zones_in:
            if zone_name not in rec.zone_entry_time:
                rec.zone_entry_time[zone_name] = now
            elapsed = now - rec.zone_entry_time[zone_name]
            if elapsed > Config.LOITER_SECS:
                last_alerted = rec.loitering_alerted.get(zone_name, 0)
                if now - last_alerted > 30:
                    anomalies.append(f"LOITERING:{zone_name}")
                    rec.loitering_alerted[zone_name] = now
        # Clear zone timers for zones no longer occupied
        for zone_name in list(rec.zone_entry_time.keys()):
            if zone_name not in zones_in:
                del rec.zone_entry_time[zone_name]

        return anomalies

    def remove(self, pid: str):
        self._records.pop(pid, None)

# ══════════════════════════════════════════════════════════════════════════════
# OBJECT OWNERSHIP ENGINE
# ══════════════════════════════════════════════════════════════════════════════
def _iou(a: Tuple[int,int,int,int], b: Tuple[int,int,int,int]) -> float:
    ax1,ay1,ax2,ay2 = a; bx1,by1,bx2,by2 = b
    ix1 = max(ax1,bx1); iy1 = max(ay1,by1)
    ix2 = min(ax2,bx2); iy2 = min(ay2,by2)
    if ix2 <= ix1 or iy2 <= iy1: return 0.0
    inter = (ix2-ix1)*(iy2-iy1)
    area_a = (ax2-ax1)*(ay2-ay1); area_b = (bx2-bx1)*(by2-by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0

def _proximity(person_box, obj_box) -> float:
    """Distance between box centers, normalized to frame diagonal."""
    px = (person_box[0]+person_box[2])/2; py = (person_box[1]+person_box[3])/2
    ox = (obj_box[0]+obj_box[2])/2;      oy = (obj_box[1]+obj_box[3])/2
    diag = math.hypot(Config.FRAME_W, Config.FRAME_H)
    return math.hypot(px-ox, py-oy) / diag

class OwnershipEngine:
    """Associates persons with nearby objects. Detects abandonment."""
    def __init__(self):
        self._owners: Dict[str, str] = {}   # obj_id -> pid
        self._last_with_owner: Dict[str, float] = {}  # obj_id -> time
        self._alerted: Dict[str, float] = {}

    def _obj_id(self, label: str, box: Tuple) -> str:
        return f"{label}_{box[0]}_{box[1]}"

    def update(self, person_dets: List[dict], obj_dets: List[dict]) -> List[Tuple[str,str]]:
        """Returns list of (obj_label, owner_pid) for abandonment events."""
        now = time.time()
        events = []
        TRACKABLE = {"backpack","suitcase","laptop","cell phone","handbag","bag","bottle","book","clock"}
        for obj in obj_dets:
            if obj["label"] not in TRACKABLE: continue
            oid = self._obj_id(obj["label"], obj["box"])
            # Find nearest person
            best_pid, best_prox = None, 1.0
            for p in person_dets:
                if not p.get("pid"): continue
                prox = _proximity(p["box"], obj["box"])
                iou  = _iou(p["box"], obj["box"])
                score = min(prox, max(0, 1-iou))
                if score < best_prox: best_prox = score; best_pid = p["pid"]
            if best_pid and best_prox < 0.3:
                self._owners[oid]         = best_pid
                self._last_with_owner[oid]= now
            else:
                if oid in self._owners:
                    elapsed = now - self._last_with_owner.get(oid, now)
                    if elapsed > Config.ABANDONMENT_SECS:
                        last_alerted = self._alerted.get(oid, 0)
                        if now - last_alerted > 60:
                            events.append((obj["label"], self._owners[oid]))
                            self._alerted[oid] = now
        return events

# ══════════════════════════════════════════════════════════════════════════════
# YOLO LOADER
# ══════════════════════════════════════════════════════════════════════════════
_yolo_lock = threading.Lock()

def make_camera_yolo():
    if not YOLO_AVAILABLE: return None
    with _yolo_lock:
        app_log.info(f"[YOLO] Loading {Config.MODEL_NAME} on {Config.DEVICE}")
        m     = YOLO(Config.MODEL_NAME)
        dummy = np.zeros((Config.DET_H, Config.DET_W, 3), dtype=np.uint8)
        try: m.predict(source=dummy, device=Config.DEVICE, verbose=False, half=CUDA_AVAILABLE)
        except Exception as e: app_log.warning(f"YOLO warm-up: {e}")
        return m

# ══════════════════════════════════════════════════════════════════════════════
# CAMERA STATE
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class PersonInfo:
    pid:           str
    name:          str
    present:       bool            = False
    absent_cycles: int             = 0
    last_box:      Optional[Tuple] = None

class CameraState:
    def __init__(self, cam_id: int, cfg: dict):
        self.cam_id   = cam_id
        self.source   = cfg["source"]
        self.name     = cfg["name"]
        self.location = cfg.get("location", "Monitored Sector")
        self.enabled  = cfg.get("enabled", True)
        self.cap: Optional[cv2.VideoCapture] = None
        self.online      = False
        self.disconnected= str(self.source).upper() == "NONE"
        self.frame_cnt   = 0
        self.fps_inst    = 0.0
        self._fps_t      = time.perf_counter()
        self._fps_cnt    = 0
        self.latest_frame: Optional[np.ndarray] = None
        self.latest_dets:  List[dict]            = []
        self.frame_lock = threading.Lock()
        self.baseline_saved   = False
        self.startup_time     = time.time()
        self.baseline_counts: Counter = Counter()
        self.before_img = str(Config.LOG_DIR / f"before_cam{cam_id}.jpg")
        self.after_img  = str(Config.LOG_DIR / f"after_cam{cam_id}.jpg")
        self.track_to_pid:    Dict[int, str]        = {}
        self.pid_confidences: Dict[str, float]      = {}
        self.pid_info:        Dict[str, PersonInfo] = {}
        self.present_pids:    set                   = set()
        self.pending_futures: Dict[int, object]     = {}
        self.tid_face_cd:     Dict[int, int]        = {}
        self.tracker     = SpatialTracker()
        self.behavior    = BehaviorEngine()
        self.ownership   = OwnershipEngine()
        self.obj_missing_since: Dict[str, float] = {}
        self.obj_added_since:   Dict[str, float] = {}
        self.motion      = MotionDetector()
        self.last_motion = time.time()
        self.idle_cnt    = 0
        self.warning_msg = ""; self.warning_time = 0.0
        self.tile_dirty  = True
        self.persons_detected = 0
        self.persons_left     = 0
        self.uptime_start     = time.time()
        self.fps_spark: deque = deque([0.0]*Config.SPARKLINE_SAMPLES, maxlen=Config.SPARKLINE_SAMPLES)
        self.det_flash_t   = 0.0
        self.det_flash_pid = ""
        self.threat_level  = "GREEN"
        self._url_input    = ""
        self._input_mode   = False
        self.zone_intruder_alerted: Dict[str, float] = {}

    def connect(self) -> bool:
        if str(self.source).upper() == "NONE":
            self.disconnected = True; self.online = False; return True
        self.disconnected = False
        try:
            if isinstance(self.source, int):
                backend  = cv2.CAP_V4L2 if IS_LINUX else cv2.CAP_ANY
                self.cap = cv2.VideoCapture(self.source, backend)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  Config.FRAME_W)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.FRAME_H)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
            else:
                os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS","rtsp_transport;tcp|buffer_size;1048576")
                self.cap = cv2.VideoCapture(str(self.source), cv2.CAP_FFMPEG)
            if self.cap:
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.online = self.cap.isOpened()
                if self.online:
                    ret, frame = self.cap.read()
                    if not ret or frame is None: self.online = False
            if not self.online:
                app_log.warning(f"[{self.name}] Could not open source")
            return True
        except Exception as e:
            app_log.error(f"[{self.name}] connect: {e}"); self.online = False; return True

    def reconnect_to(self, new_source):
        if self.cap: self.cap.release(); self.cap = None
        self.source = new_source; self.disconnected = False
        self.online = False; self.baseline_saved = False
        self.startup_time = time.time(); self.connect()

    def release(self):
        if self.cap: self.cap.release(); self.cap = None

    @property
    def uptime_str(self):
        s = int(time.time() - self.uptime_start)
        h, r = divmod(s, 3600); m, s = divmod(r, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

# ══════════════════════════════════════════════════════════════════════════════
# EVENT HANDLERS
# ══════════════════════════════════════════════════════════════════════════════
def _ensure_pid(cs: CameraState, pid: str, name: str) -> PersonInfo:
    if pid not in cs.pid_info: cs.pid_info[pid] = PersonInfo(pid=pid, name=name)
    else: cs.pid_info[pid].name = name
    return cs.pid_info[pid]

def _alarm():
    if IS_WINDOWS and WINSOUND_AVAILABLE and os.path.exists(Config.ALARM_WAV):
        threading.Thread(target=lambda: winsound.PlaySound(Config.ALARM_WAV, winsound.SND_ASYNC), daemon=True).start()

def on_person_arrived(cs: CameraState, pid: str, name: str, frame: np.ndarray, box: Tuple, conf: float):
    with _fdb_lock:
        db = faces_db.get(pid)
        if db is None or db.get("in_scene", False): return
        db["in_scene"]    = True
        db["last_seen"]   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db["visit_count"] = db.get("visit_count", 0) + 1
        visits = db["visit_count"]; known = db.get("known", False)
    now   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    event = "PERSON_ENTERED" if visits == 1 else "PERSON_RETURNED"
    log_event(event, camera=cs.name, person=name, obj="person", detail=f"visits={visits} conf={conf:.2f}")
    cs.persons_detected += 1; cs.det_flash_t = time.time(); cs.det_flash_pid = pid

    x1,y1,x2,y2 = box
    crop = None
    if YUNET_AVAILABLE:
        person_crop = frame[y1:y2, x1:x2]
        if person_crop.size > 0:
            with _yunet_lock:
                h_c, w_c = person_crop.shape[:2]
                _yunet_detector.setInputSize((w_c, h_c))
                _, faces = _yunet_detector.detect(person_crop)
            if faces is not None and len(faces) > 0:
                face = faces[0]
                fx, fy, fw, fh = int(face[0]), int(face[1]), int(face[2]), int(face[3])
                fx_f = x1 + fx
                fy_f = y1 + fy
                pad = int(fh * 0.35)
                sz = max(fw, fh) + 2 * pad
                cx = fx_f + fw // 2
                cy = fy_f + fh // 2
                nx1 = max(0, cx - sz // 2)
                ny1 = max(0, cy - sz // 2)
                nx2 = min(frame.shape[1] - 1, nx1 + sz)
                ny2 = min(frame.shape[0] - 1, ny1 + sz)
                crop = frame[ny1:ny2, nx1:nx2]
    if crop is None or crop.size == 0:
        h_box = y2 - y1
        w_box = x2 - x1
        head_h = int(h_box * 0.28)
        cx = x1 + w_box // 2
        cy = y1 + head_h // 2
        sz = max(head_h, int(w_box * 0.8))
        nx1 = max(0, cx - sz // 2)
        ny1 = max(y1, cy - sz // 2)
        nx2 = min(frame.shape[1] - 1, nx1 + sz)
        ny2 = min(frame.shape[0] - 1, ny1 + sz)
        crop = frame[ny1:ny2, nx1:nx2]
    if crop is None or crop.size == 0:
        crop = frame[y1:y2, x1:x2]
        
    photo_path = None
    if crop is not None and crop.size > 0:
        ts_str     = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_cam_name = cs.name.replace(' ', '_').replace('/', '_')
        rel_path   = f"faces/captured/{pid}_{clean_cam_name}_{ts_str}.jpg"
        abs_path   = str(WORKING_DIR / rel_path)
        cv2.imwrite(abs_path, crop)
        photo_path = rel_path
        app_log.info(f"[CAPTURE] Face crop for {name} captured from camera {cs.name} -> {photo_path}")
        with _fdb_lock:
            if db is not None:
                db["photo"] = photo_path

    _save_db_json()
    is_intruder = "Intruder" in name
    if is_intruder:
        threat_engine.raise_threat("RED", f"INTRUDER: {name}")
        # Silence all unauthorized audio alerts and alarms
        cs.threat_level = "RED"
        db_log_threat(now, "RED", f"INTRUDER: {name}", cs.name)
    else:
        speak(f"Identity confirmed. Welcome, {name}.")
        cs.threat_level = "GREEN"

    db_log_person(pid, name, not is_intruder, now)
    db_log_visit_enter(pid, cs.name, now, conf, cs.threat_level)

    # Silence Telegram alerts for unauthorized (intruder) entries
    if not is_intruder:
        notif_queue.send_alert(_tg_person_enter(cs.name, pid, name, visits, conf, now),
                               photo_path=photo_path,
                               event_type="PERSON_ENTERED",
                               camera=cs.name, person=pid)
    cs.warning_msg  = f"{'INTRUDER' if is_intruder else 'ARRIVED'}: {name}"
    cs.warning_time = time.time(); cs.tile_dirty = True

def on_person_left(cs: CameraState, pid: str, name: str, frame: np.ndarray):
    with _fdb_lock:
        db = faces_db.get(pid)
        if db: db["in_scene"] = False
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.imwrite(cs.after_img, frame)
    log_event("PERSON_LEFT", camera=cs.name, person=name, detail=f"last_seen={now}")
    cs.persons_left += 1
    is_transient = pid.startswith("Unknown-") or name == "Unknown"
    if not is_transient:
        notif_queue.send_message(_tg_person_left(cs.name, pid, name, now),
                                 event_type="PERSON_LEFT", camera=cs.name, person=pid)
        if "Intruder" not in name: speak(f"{name} has left the monitored zone.")
    cs.behavior.remove(pid)
    cs.warning_msg = f"DEPARTED: {name}"; cs.warning_time = time.time()
    if "Intruder" not in name and not is_transient: cs.threat_level = "GREEN"
    cs.tile_dirty = True

def on_obj_event(cs: CameraState, event: str, label: str, before: int, after: int, frame: np.ndarray):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.imwrite(cs.after_img, frame)
    log_event(event, camera=cs.name, obj=label, detail=f"{before}->{after}")
    threat_engine.raise_threat("ORANGE", f"OBJ {event}: {label}")
    db_log_threat(now, "ORANGE", f"OBJ {event}: {label}", cs.name)
    cs.threat_level = "ORANGE"; _alarm()
    notif_queue.send_alert(_tg_obj(cs.name, event, label, before, after, now),
                           photo_path=cs.after_img, event_type=event, camera=cs.name)
    verb = "ADDED" if event == "OBJ_ADDED" else "REMOVED"
    cs.warning_msg = f"OBJ {verb}: {label.upper()}"; cs.warning_time = time.time()
    cs.tile_dirty  = True

def on_zone_intrusion(cs: CameraState, pid: str, name: str, zone_name: str, threat_lv: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    last = cs.zone_intruder_alerted.get(f"{pid}:{zone_name}", 0)
    if time.time() - last < 60: return
    cs.zone_intruder_alerted[f"{pid}:{zone_name}"] = time.time()
    log_event("ZONE_INTRUSION", camera=cs.name, person=pid, obj=zone_name,
              detail=f"zone={zone_name} threat={threat_lv}")
    threat_engine.raise_threat(threat_lv, f"ZONE: {zone_name}")
    if "Intruder" not in name:
        notif_queue.send_message(_tg_zone(cs.name, pid, name, zone_name, now),
                                 event_type="PERSON_ENTERED", camera=cs.name, person=pid)
    cs.warning_msg = f"ZONE BREACH: {zone_name}"; cs.warning_time = time.time()

def on_behavior_anomaly(cs: CameraState, pid: str, name: str, anomaly: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_event("BEHAVIOR", camera=cs.name, person=pid, obj=anomaly,
              detail=f"behavior={anomaly} subject={name}")
    btype = anomaly.split(":")[0]
    if btype in ("STILL", "ACTIVE"):
        status_desc = "STILL (stationary for > 5 mins)" if btype == "STILL" else "ACTIVE (moving)"
        msg = (
            "🏃 OMS STATUS UPDATE\n━━━━━━━━━━━━━━━━━━━\n\n"
            f"📷 CAMERA\n{cs.name}\n\n"
            f"👤 SUBJECT\n{name} ({pid})\n\n"
            f"📊 STATUS\n{status_desc}\n\n"
            f"⏱ TIMESTAMP\n{now}"
        )
        notif_queue.send_message(msg, event_type="STATUS_CHANGE", camera=cs.name, person=pid, priority=5)
        cs.warning_msg = f"STATUS: {btype}"
    else:
        threat_engine.raise_threat("ORANGE", f"BEHAVIOR: {btype}")
        db_log_threat(now, "ORANGE", f"BEHAVIOR {btype} by {name}", cs.name)
        if "Intruder" not in name:
            notif_queue.send_message(_tg_behavior(cs.name, pid, name, btype, now),
                                     event_type="PERSON_ENTERED", camera=cs.name, person=pid)
        cs.warning_msg = f"ANOMALY: {btype}"
    cs.warning_time = time.time()

def camera_thread(cs: CameraState):
    yolo   = make_camera_yolo()
    gc_ctr = 0
    cs.connect()

    while True:
        if cs.disconnected:
            time.sleep(1.0); continue
        if not cs.online:
            time.sleep(3.0); cs.release(); cs.connect()
            if cs.online: log_event("CAM_RECONNECT", camera=cs.name)
            continue

        ret, frame = cs.cap.read()
        if not ret or frame is None: cs.online = False; continue
        frame = cv2.resize(frame, (Config.FRAME_W, Config.FRAME_H), interpolation=cv2.INTER_LINEAR)

        cs.frame_cnt += 1; cs._fps_cnt += 1
        t = time.perf_counter(); e = t - cs._fps_t
        if e >= 1.0:
            cs.fps_inst = cs._fps_cnt / e; cs._fps_cnt = 0; cs._fps_t = t
            cs.fps_spark.append(cs.fps_inst)

        if not cs.baseline_saved and time.time() - cs.startup_time > 5:
            cv2.imwrite(cs.before_img, frame)
            if yolo:
                try:
                    small = cv2.resize(frame, (adaptive.det_w, adaptive.det_h), interpolation=cv2.INTER_LINEAR)
                    results = yolo.predict(source=small, conf=Config.CONFIDENCE, device=Config.DEVICE, verbose=False, half=CUDA_AVAILABLE)
                    base_objs = []
                    for box in results[0].boxes:
                        if float(box.conf[0]) >= Config.CONFIDENCE:
                            cls = int(box.cls[0])
                            label = yolo.names[cls]
                            if label != "person":
                                base_objs.append(label)
                    cs.baseline_counts = Counter(base_objs)
                except Exception as e:
                    app_log.warning(f"Baseline object seeding failed: {e}")
            cs.baseline_saved = True
            log_event("BASELINE", camera=cs.name, detail="scene captured")
            notif_queue.send_message(
                f"🟢 OMS NODE ONLINE\n━━━━━━━━━━━━━━━━━━━\n\nCamera: {_clean_cam_name(cs.name)}\nLocation: {cs.location}\nProfile: {HW_PROFILE}\nBaseline captured.",
                event_type="BASELINE", camera=cs.name)

        has_motion = cs.motion.has_motion(frame)
        if has_motion: cs.last_motion = time.time(); cs.idle_cnt = 0
        else: cs.idle_cnt += 1
        idle   = (time.time() - cs.last_motion) > 3.0 and not has_motion
        skip_n = adaptive.skip_n + (Config.IDLE_SKIP_EXTRA if idle else 0)

        if cs.frame_cnt % skip_n != 0:
            with cs.frame_lock: cs.latest_frame = frame; cs.tile_dirty = has_motion
            continue

        dw, dh   = adaptive.det_w, adaptive.det_h
        new_dets: List[dict] = []
        cur_objs: List[str]  = []
        tid_seen: set        = set()

        # ── YOLO DETECTION + TRACKING ─────────────────────────────────────────
        if yolo:
            try:
                small   = cv2.resize(frame, (dw, dh), interpolation=cv2.INTER_LINEAR)
                results = yolo.track(source=small, conf=Config.CONFIDENCE,
                                     device=Config.DEVICE, persist=Config.TRACK_PERSIST,
                                     verbose=False, half=CUDA_AVAILABLE, imgsz=max(dw, dh))
                boxes = results[0].boxes
                sx = Config.FRAME_W / dw; sy = Config.FRAME_H / dh

                yolo_dets = []
                for box in boxes:
                    cv_val = float(box.conf[0])
                    if cv_val < Config.CONFIDENCE: continue
                    cls   = int(box.cls[0]); label = yolo.names[cls]
                    bx1,by1,bx2,by2 = box.xyxy[0]
                    x1 = int(max(0, bx1*sx)); y1 = int(max(0, by1*sy))
                    x2 = int(min(Config.FRAME_W-1, bx2*sx)); y2 = int(min(Config.FRAME_H-1, by2*sy))
                    w_box = x2 - x1
                    h_box = y2 - y1
                    if label == "person":
                        if w_box < 25 or h_box < 45: continue
                        if h_box / max(1, w_box) > 4.0: continue
                    tid = None
                    if box.id is not None:
                        try: tid = int(box.id[0])
                        except: pass
                    yolo_dets.append({"label":label,"conf":cv_val,"box":(x1,y1,x2,y2),"tid":tid})

                unassigned = [d["box"] for d in yolo_dets if d["label"]=="person" and d["tid"] is None]
                if unassigned:
                    local_tids = cs.tracker.track(unassigned); ui = 0
                    for d in yolo_dets:
                        if d["label"]=="person" and d["tid"] is None:
                            d["tid"] = local_tids[ui]; ui += 1

                person_dets_this_frame = []
                for d in yolo_dets:
                    label = d["label"]; cv_val = d["conf"]
                    x1,y1,x2,y2 = d["box"]; tid = d["tid"]
                    cur_objs.append(label); pid = None; disp = label.upper()

                    if label == "person" and tid is not None:
                        tid_seen.add(tid)
                        fut = cs.pending_futures.get(tid)
                        if not hasattr(cs, "tid_face_votes"):
                            cs.tid_face_votes = {}
                        if not hasattr(cs, "tid_identity_locked"):
                            cs.tid_identity_locked = {}

                        fut = cs.pending_futures.get(tid)
                        if fut and fut.done():
                            res = fut.result()
                            if res and len(res) == 3:
                                np_pid, np_name, conf = res
                            else:
                                np_pid, np_name, conf = res[0], res[1], 0.984
                            del cs.pending_futures[tid]

                            if np_pid:
                                is_locked = cs.tid_identity_locked.get(tid, False)
                                if not is_locked:
                                    np_is_known = False
                                    with _fdb_lock:
                                        if np_pid in faces_db:
                                            np_is_known = faces_db[np_pid].get("known", False)
                                    
                                    if np_is_known:
                                        votes = cs.tid_face_votes.setdefault(tid, {})
                                        votes[np_pid] = votes.get(np_pid, 0.0) + conf
                                        
                                        if votes[np_pid] >= 0.85:
                                            cs.tid_identity_locked[tid] = True
                                            cs.pid_confidences[np_pid] = conf
                                            old = cs.track_to_pid.get(tid)
                                            if old and old != np_pid:
                                                cs.present_pids.discard(old)
                                                with _fdb_lock:
                                                    if old in faces_db:
                                                        faces_db[old]["in_scene"] = False
                                                        if not faces_db[old].get("known") and faces_db[old].get("visit_count", 0) <= 1:
                                                            del faces_db[old]
                                            cs.track_to_pid[tid] = np_pid
                                            _ensure_pid(cs, np_pid, np_name)
                                    else:
                                        curr_pid = cs.track_to_pid.get(tid)
                                        if curr_pid:
                                            cs.pid_confidences[curr_pid] = conf

                        if tid not in cs.track_to_pid:
                            if not Config.DETECT_NEW_IDS:
                                new_p = f"Unknown-{tid}"
                                cs.track_to_pid[tid] = new_p
                            else:
                                new_p = _new_pid()
                                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                with _fdb_lock:
                                    faces_db[new_p] = {
                                        "name": f"Intruder-{new_p}",
                                        "first_seen": now,
                                        "last_seen": now,
                                        "visit_count": 0,
                                        "known": False,
                                        "photo": None,
                                        "in_scene": False
                                    }
                                cs.track_to_pid[tid] = new_p
                                _ensure_pid(cs, new_p, f"Intruder-{new_p}")
                                _save_db_json()

                        pid = cs.track_to_pid[tid]
                        if pid.startswith("Unknown-"):
                            name = "Unknown"
                            disp = "Unknown"
                        else:
                            if pid not in faces_db:
                                del cs.track_to_pid[tid]
                                continue
                            name = faces_db.get(pid, {}).get("name", f"Intruder-{pid}")
                            disp = name.split("-")[0][:12]

                        # Schedule face recognition
                        fr_cd = cs.tid_face_cd.get(tid, 0)
                        if fr_cd <= 0 and tid not in cs.pending_futures:
                            x1f,y1f,x2f,y2f = d["box"]
                            crop = frame[y1f:y2f, x1f:x2f]
                            if crop.size > 0:
                                cs.pending_futures[tid] = face_pool.submit(async_face, crop.copy(), True)
                            cs.tid_face_cd[tid] = Config.FACE_RECHECK_CYCLES
                        else:
                            cs.tid_face_cd[tid] = max(0, fr_cd - 1)

                        # Person arrival
                        if pid not in cs.present_pids:
                            cs.present_pids.add(pid)
                            if not pid.startswith("Unknown-"):
                                on_person_arrived(cs, pid, name, frame, d["box"], cv_val)

                        pi = _ensure_pid(cs, pid, name)
                        person_dets_this_frame.append({"pid": pid, "box": d["box"]})

                        # Zone check
                        cx_p = (x1+x2)//2; cy_p = (y1+y2)//2
                        zones_in = [z.name for z in ZONES if z.contains(cx_p, cy_p, Config.FRAME_W, Config.FRAME_H)]
                        for z in ZONES:
                            if z.name in zones_in and z.threat_level not in ("GREEN",):
                                on_zone_intrusion(cs, pid, name, z.name, z.threat_level)
                        anomalies = cs.behavior.update(pid, cx_p, cy_p, zones_in)
                        for an in anomalies:
                            on_behavior_anomaly(cs, pid, name, an)

                    new_dets.append({"label":label,"conf":cv_val,"box":(x1,y1,x2,y2),"disp":disp,"pid":pid})

                # Object ownership
                obj_dets_frame = [d for d in new_dets if d["label"] != "person"]
                cs.ownership.update(person_dets_this_frame, obj_dets_frame)

                # Absent-person tracking
                for tid_gone in list(cs.track_to_pid.keys()):
                    if tid_gone not in tid_seen:
                        pid_g = cs.track_to_pid[tid_gone]
                        pi_g  = cs.pid_info.get(pid_g)
                        if pi_g:
                            pi_g.absent_cycles += 1
                            if pi_g.absent_cycles > Config.ABSENT_CYCLES_THRESH:
                                if pid_g in cs.present_pids:
                                    cs.present_pids.discard(pid_g)
                                    name_g = faces_db.get(pid_g,{}).get("name","Unknown")
                                    on_person_left(cs, pid_g, name_g, frame)
                                del cs.track_to_pid[tid_gone]
                                if hasattr(cs, "tid_face_votes") and tid_gone in cs.tid_face_votes:
                                    del cs.tid_face_votes[tid_gone]
                                if hasattr(cs, "tid_identity_locked") and tid_gone in cs.tid_identity_locked:
                                    del cs.tid_identity_locked[tid_gone]
                        else:
                            del cs.track_to_pid[tid_gone]
                            if hasattr(cs, "tid_face_votes") and tid_gone in cs.tid_face_votes:
                                del cs.tid_face_votes[tid_gone]
                            if hasattr(cs, "tid_identity_locked") and tid_gone in cs.tid_identity_locked:
                                del cs.tid_identity_locked[tid_gone]

                # Object change detection
                cur_ctr = Counter(o for o in cur_objs if o != "person")
                if cs.baseline_saved:
                    for lbl, cnt in cur_ctr.items():
                        if cnt > cs.baseline_counts.get(lbl, 0):
                            if lbl not in cs.obj_added_since:
                                cs.obj_added_since[lbl] = time.time()
                            elif time.time() - cs.obj_added_since[lbl] > 4.0:
                                on_obj_event(cs, "OBJ_ADDED", lbl, cs.baseline_counts.get(lbl,0), cnt, frame)
                                cs.baseline_counts[lbl] = cnt
                                cs.obj_added_since.pop(lbl, None)
                        else:
                            cs.obj_added_since.pop(lbl, None)
                    for lbl, base_cnt in list(cs.baseline_counts.items()):
                        if cur_ctr.get(lbl, 0) < base_cnt:
                            if lbl not in cs.obj_missing_since:
                                cs.obj_missing_since[lbl] = time.time()
                            elif time.time() - cs.obj_missing_since[lbl] > 4.0:
                                on_obj_event(cs, "OBJ_REMOVED", lbl, base_cnt, cur_ctr.get(lbl,0), frame)
                                cs.baseline_counts[lbl] = cur_ctr.get(lbl, 0)
                                cs.obj_missing_since.pop(lbl, None)
                        else:
                            cs.obj_missing_since.pop(lbl, None)

                with cs.frame_lock:
                    cs.latest_frame = frame; cs.latest_dets = new_dets; cs.tile_dirty = True

            except Exception as e:
                app_log.error(f"[{cs.name}] YOLO error: {e}")
                with cs.frame_lock: cs.latest_frame = frame

        else:
            with cs.frame_lock: cs.latest_frame = frame

        gc_ctr += 1
        if gc_ctr % Config.GC_GEN0_FRAMES == 0: gc.collect(0)

# ══════════════════════════════════════════════════════════════════════════════
# PREMIUM CYBERPUNK MILITARY AI SURVEILLANCE DASHBOARD — CINEMA REBUILD v9.0
# OLED Black & Gold Luxury Command Center
# ══════════════════════════════════════════════════════════════════════════════

UI_HDR_H   = 80          # top header bar height
UI_NAV_H   = 0           # integrated directly into the header bar to save vertical space
UI_FOOT_H  = 28          # bottom ticker strip
UI_LEFT_W  = 280         # Left Panel width (280px)
UI_RIGHT_W = 340         # Right Panel width (340px)
UI_PAD     = 16          # Modern Spacing Padding (16px)

# ── Sparkline history for system graphs ──────────────────────────────────────
_cpu_spark:  deque = deque([0.0]*60, maxlen=60)
_ram_spark:  deque = deque([0.0]*60, maxlen=60)
_disk_spark: deque = deque([0.0]*60, maxlen=60)
_net_spark:  deque = deque([0.0]*60, maxlen=60)
_total_detections = 0  # running counter
_known_persons    = 0
_unknown_persons  = 0
_objs_added       = 0
_objs_removed     = 0
_alerts_generated = 0
_sys_graph_lock   = threading.Lock()

def _update_sys_graphs():
    global _total_detections
    if not PSUTIL_AVAILABLE: return
    with _sys_graph_lock:
        _cpu_spark.append(psutil.cpu_percent(interval=None))
        vm = psutil.virtual_memory()
        _ram_spark.append(vm.percent)
        try: _disk_spark.append(psutil.disk_usage('/').percent)
        except: _disk_spark.append(0.0)
        try:
            nc = psutil.net_io_counters()
            _net_spark.append(min(100, (nc.bytes_sent + nc.bytes_recv) / 1e7))
        except: _net_spark.append(0.0)

# ── Core rendering helpers ────────────────────────────────────────────────────
def _clamp_rect(img, x1, y1, x2, y2):
    H, W = img.shape[:2]
    return max(0,x1), max(0,y1), min(W,x2), min(H,y2)

def _fill_rect(img, x1, y1, x2, y2, color):
    x1,y1,x2,y2 = _clamp_rect(img,x1,y1,x2,y2)
    if x2>x1 and y2>y1:
        img[y1:y2, x1:x2] = color

def _alpha_rect(img, x1, y1, x2, y2, color, a=0.55):
    x1,y1,x2,y2 = _clamp_rect(img,x1,y1,x2,y2)
    if x2>x1 and y2>y1:
        roi = img[y1:y2, x1:x2]
        overlay = np.full_like(roi, color)
        cv2.addWeighted(overlay, a, roi, 1.0-a, 0, roi)
        img[y1:y2, x1:x2] = roi

def _neon_rect(img, x1, y1, x2, y2, color, thick=1):
    """Draw a glowing neon rectangle with realistic soft lighting blur."""
    for offset in range(3, 0, -1):
        alpha = 0.06 * (4 - offset)
        gc = tuple(int(c * alpha) for c in color)
        cv2.rectangle(img, (x1-offset, y1-offset), (x2+offset, y2+offset), gc, thick+2, cv2.LINE_AA)
    cv2.rectangle(img, (x1,y1), (x2,y2), color, thick, cv2.LINE_AA)

def _border_rect(img, x1, y1, x2, y2, color, thick=1):
    cv2.rectangle(img, (x1,y1), (x2,y2), color, thick, cv2.LINE_AA)

def _corner_brackets_static(img, x1, y1, x2, y2, color, L=8, T=1):
    """Draw thin, premium structural corner caps for HUD layout widgets."""
    segs = [
        (x1,y1,1,0),(x1,y1,0,1),
        (x2-1,y1,-1,0),(x2-1,y1,0,1),
        (x1,y2-1,1,0),(x1,y2-1,0,-1),
        (x2-1,y2-1,-1,0),(x2-1,y2-1,0,-1)
    ]
    for px,py,dx,dy in segs:
        cv2.line(img,(px,py),(px+dx*L,py+dy*L),color,T,cv2.LINE_AA)

def _corner_brackets(img, x1, y1, x2, y2, color, L=14, T=2):
    """Animated gold corner targeting brackets."""
    pulse = (math.sin(time.time()*4)+1.0)/2.0
    L2 = int(10 + pulse*5)
    segs = [
        (x1,y1,1,0),(x1,y1,0,1),
        (x2,y1,-1,0),(x2,y1,0,1),
        (x1,y2,1,0),(x1,y2,0,-1),
        (x2,y2,-1,0),(x2,y2,0,-1),
    ]
    for px,py,dx,dy in segs:
        cv2.line(img,(px,py),(px+dx*L2,py+dy*L2),color,T,cv2.LINE_AA)

def _draw_sparkline(img, x, y, w, h, data: deque, color, fill=True):
    """AAA game premium real-time neural sparkline graph with layered neon glow."""
    if len(data) < 2: return
    dlist = list(data)
    max_val = max(max(dlist), 1.0)
    pts = []
    dx  = w / max(len(dlist)-1, 1)
    for i,v in enumerate(dlist):
        pts.append((int(x+i*dx), int(y+h-(v/max_val)*h)))
        
    if fill and len(pts) >= 2:
        # Elegant soft gradient filled polygon
        poly = [pts[0]] + pts + [(pts[-1][0], y+h), (pts[0][0], y+h)]
        # Mix 8% of original color for luxurious subtle fill
        cv2.fillPoly(img, [np.array(poly, dtype=np.int32)],
                     tuple(max(0, int(c * 0.08)) for c in color))
                     
    # Render with glowing double-pass anti-aliased lines
    # Pass 1: Soft broad neon glow (3px thick, 25% opacity)
    glow_col = tuple(int(c * 0.25) for c in color)
    for k in range(len(pts)-1):
        cv2.line(img, pts[k], pts[k+1], glow_col, 3, cv2.LINE_AA)
        
    # Pass 2: Crisp core line (1px thick, 100% opacity)
    for k in range(len(pts)-1):
        cv2.line(img, pts[k], pts[k+1], color, 1, cv2.LINE_AA)
        
    # Pulse dot at the leading telemetry edge
    if pts:
        pulse_col = tuple(int(c * (0.6 + _pulse(2.5)*0.4)) for c in color)
        cv2.circle(img, pts[-1], 3, pulse_col, -1, cv2.LINE_AA)

def _status_dot(img, cx, cy, r, color, animate=True):
    """Holographic glowing status indicator with concentric pulse rings."""
    pulse = _pulse(1.5) if animate else 1.0
    
    # Glowing outer ambient halo ring
    outer_r = int(r * (1.2 + pulse * 0.8))
    halo_col = tuple(int(c * 0.25 * (1.0 - pulse * 0.5)) for c in color)
    cv2.circle(img, (cx, cy), outer_r, halo_col, 1, cv2.LINE_AA)
    
    # Crisp glowing core
    c2 = tuple(int(c * (0.6 + pulse * 0.4)) for c in color)
    cv2.circle(img, (cx, cy), r, c2, -1, cv2.LINE_AA)

def _draw_loading_tile(tile: np.ndarray, cam_name: str):
    """Draws a premium 3D holographic targeting standby reticle for offline streams."""
    H, W = tile.shape[:2]
    
    # Volumetric dark ambient tile background
    tile[:] = (5, 5, 5)
    cx, cy = W // 2, H // 2
    
    # Draw faint cinematic grid background inside the tile
    grid_col = (12, 10, 10)
    for gx in range(0, W, 40):
        cv2.line(tile, (gx, 0), (gx, H), grid_col, 1)
    for gy in range(0, H, 40):
        cv2.line(tile, (0, gy), (W, gy), grid_col, 1)
        
    pulse = _pulse(0.8)
    col = tuple(int(c * (0.3 + pulse * 0.7)) for c in C_GOLD)
    dim_col = tuple(int(c * 0.2) for c in C_GOLD)
    
    # Concentric targeting reticle rings with alpha fading
    for r, a in [(45, 0.08), (28, 0.16), (8, 0.5)]:
        ca = tuple(int(c * a * (0.8 + pulse * 0.2)) for c in C_GOLD)
        cv2.circle(tile, (cx, cy), r, ca, 1, cv2.LINE_AA)
        
    # Crosshair tactical coordinates lines
    cv2.line(tile, (cx - 55, cy), (cx - 15, cy), dim_col, 1, cv2.LINE_AA)
    cv2.line(tile, (cx + 15, cy), (cx + 55, cy), dim_col, 1, cv2.LINE_AA)
    cv2.line(tile, (cx, cy - 55), (cx, cy - 15), dim_col, 1, cv2.LINE_AA)
    cv2.line(tile, (cx, cy + 15), (cx, cy + 55), dim_col, 1, cv2.LINE_AA)
    
    # Glowing center core
    cv2.circle(tile, (cx, cy), 3, col, -1, cv2.LINE_AA)
    
    # Text displays using anti-aliased Segoe UI fonts
    _text_c(tile, f"📡  CHANNEL STATUS: OFFLINE", cx, cy - 65, 0.28, col, bold=True)
    t = time.time()
    dots = '.' * (int(t * 1.5) % 4)
    _text_c(tile, f"AWAITING SECURE FEED{dots}", cx, cy + 70, 0.26, C_DIM)
    _text_c(tile, cam_name.upper(), cx, cy - 80, 0.32, C_TEXT, bold=True)

def draw_gradient_background(img):
    """Cinematic volumetric dark atmospheric background — Iron Man / Tesla command center feel."""
    H, W = img.shape[:2]
    # Base: Deep cinematic near-black
    img[:] = (5, 5, 5)

    # ── 1. Warm volumetric radial glow from bottom center (like stage lighting from below)
    t = time.time()
    glow_pulse = 0.85 + 0.15 * math.sin(t * 0.4)  # Very slow ambient breathing
    glow_x = W // 2
    glow_y = int(H * 1.15)  # Below screen, so light sweeps up from bottom
    max_r = int(W * 0.85)
    for r_idx in range(16, 0, -1):
        r = int(max_r * (r_idx / 16))
        alpha = glow_pulse * 0.0025 * (17 - r_idx)
        # Warm gold glow: BGR = (20, 80, 120) range
        gc = (int(20 * alpha * 8), int(80 * alpha * 8), int(120 * alpha * 8))
        cv2.circle(img, (glow_x, glow_y), r, gc, -1, cv2.LINE_AA)

    # ── 2. Secondary top-center subtle cool glow for depth layering
    for r_idx in range(10, 0, -1):
        r = int(W * 0.35 * (r_idx / 10))
        alpha = 0.001 * (11 - r_idx)
        gc = (int(60 * alpha * 10), int(30 * alpha * 10), int(15 * alpha * 10))
        cv2.circle(img, (W // 2, -int(H * 0.1)), r, gc, -1, cv2.LINE_AA)

    # ── 3. Subtle horizontal scan line texture (very faint, premium feel)
    scan_speed = 18.0
    scan_spacing = 40
    scan_offset = int(t * scan_speed) % scan_spacing
    for sy in range(scan_offset, H, scan_spacing):
        alpha = 0.008 + 0.003 * math.sin(sy / 200.0 + t * 0.3)
        sc = (int(25 * alpha * 12), int(20 * alpha * 12), int(15 * alpha * 12))
        cv2.line(img, (0, sy), (W, sy), sc, 1, cv2.LINE_AA)

    # ── 4. Animated golden diagonal energy streak (very faint)
    streak_t = t * 0.12
    for s in range(3):
        sx_off = int((streak_t + s * 0.33) % 1.0 * W * 2) - W // 2
        streak_alpha = 0.018 * math.sin(math.pi * ((streak_t + s * 0.33) % 1.0))
        sc2 = (int(30 * streak_alpha * 12), int(100 * streak_alpha * 12), int(180 * streak_alpha * 12))
        if streak_alpha > 0.001:
            cv2.line(img, (sx_off, 0), (sx_off + W // 3, H), sc2, 2, cv2.LINE_AA)

def _aspect_crop_to_fill(feed, dets, target_w, target_h):
    """Crops the feed to match the exact aspect ratio of target_w / target_h and resizes it to fill, adjusting det boxes."""
    ch, cw = feed.shape[:2]
    r_target = target_w / target_h
    r_feed = cw / ch
    
    if r_target > r_feed:
        # Target is wider than feed -> crop height
        crop_w = cw
        crop_h = int(cw / r_target)
        crop_x0 = 0
        crop_y0 = (ch - crop_h) // 2
    else:
        # Target is taller than feed -> crop width
        crop_h = ch
        crop_w = int(ch * r_target)
        crop_y0 = 0
        crop_x0 = (cw - crop_w) // 2
        
    crop = feed[crop_y0 : crop_y0 + crop_h, crop_x0 : crop_x0 + crop_w]
    resized = cv2.resize(crop, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
    
    # Adjust detection coordinate system to cropped and scaled space
    new_dets = []
    for d in dets:
        bx1, by1, bx2, by2 = d["box"]
        # Map original coords back to actual ch, cw
        bx1_act = bx1 * (cw / Config.FRAME_W)
        bx2_act = bx2 * (cw / Config.FRAME_W)
        by1_act = by1 * (ch / Config.FRAME_H)
        by2_act = by2 * (ch / Config.FRAME_H)
        
        # Shift to crop coordinates and scale
        x1_c = bx1_act - crop_x0
        x2_c = bx2_act - crop_x0
        y1_c = by1_act - crop_y0
        y2_c = by2_act - crop_y0
        
        scale_x = target_w / crop_w
        scale_y = target_h / crop_h
        
        new_box = (
            max(0, min(target_w, int(x1_c * scale_x))),
            max(0, min(target_h, int(y1_c * scale_y))),
            max(0, min(target_w, int(x2_c * scale_x))),
            max(0, min(target_h, int(y2_c * scale_y)))
        )
        new_dets.append({
            "box": new_box,
            "label": d["label"],
            "conf": d["conf"],
            "disp": d["disp"],
            "pid": d.get("pid")
        })
        
    return resized, new_dets

def _draw_cam_hud(img, cs, tx1, ty1, tx2, ty2, c_border, large=False):
    """Draw camera HUD overlay: LIVE badge, cam name, time, FPS, subject count with high-end sci-fi layout."""
    s = 0.28 if not large else 0.34
    
    # 1. LIVE / OFFLINE Badge with pulsing status dot
    pulse = _pulse(2.0)
    lc = tuple(int(c * (0.4 + pulse * 0.6)) for c in C_GREEN) if cs.online else C_DIM
    
    # Holographic pill for status
    _panel(img, tx1 + 8, ty1 + 8, tx1 + 80, ty1 + 30, a=0.65, border_color=lc)
    _status_dot(img, tx1 + 20, ty1 + 19, 4, lc, animate=cs.online)
    _text(img, "LIVE" if cs.online else "OFFLINE", tx1 + 32, ty1 + 22, s, lc, bold=cs.online)

    # 2. Camera ID & Name with glassy backdrop
    cam_lbl = f"CAM {cs.cam_id+1} : {cs.name.upper()}"
    font = get_pil_font("segoe_bold", 12)
    try:
        bbox = font.getbbox(cam_lbl)
        nw = bbox[2] - bbox[0]
    except AttributeError:
        nw, _ = font.getsize(cam_lbl)
        
    nx = tx1 + 88
    _panel(img, nx, ty1 + 8, nx + nw + 24, ty1 + 30, a=0.65, border_color=C_BORDER)
    _text(img, cam_lbl, nx + 12, ty1 + 22, s, C_TEXT, bold=True)

    # 3. Dynamic Timestamp on top-right
    ts_str = datetime.now().strftime("%H:%M:%S")
    font_ts = get_pil_font("segoe", 12)
    try:
        bbox_ts = font_ts.getbbox(ts_str)
        tw2 = bbox_ts[2] - bbox_ts[0]
    except AttributeError:
        tw2, _ = font_ts.getsize(ts_str)
        
    _panel(img, tx2 - tw2 - 24, ty1 + 8, tx2 - 8, ty1 + 30, a=0.65, border_color=C_BORDER)
    _text(img, ts_str, tx2 - tw2 - 12, ty1 + 22, s, C_GOLD)

    # 4. Floating Bottom Bar: FPS + Subjects + Alerts
    p_cnt = len(cs.present_pids)
    det_cnt = len(cs.latest_dets)
    
    # Semi-transparent glass bottom panel
    _panel(img, tx1 + 8, ty2 - 32, tx2 - 8, ty2 - 8, a=0.6, border_color=C_BORDER)
    
    # Tactical information segments
    _text(img, f"📊  FPS: {cs.fps_inst:.1f}", tx1 + 20, ty2 - 16, 0.26, C_GOLD)
    _text_c(img, f"👤  SUBJECTS: {p_cnt}", (tx1 + tx2) // 2, ty2 - 16, 0.26, C_TEXT, bold=True)
    _text_r(img, f"🔍  DETECTION TARGETS: {det_cnt}", tx2 - 20, ty2 - 16, 0.26, C_DIM)
    
    # Volumetric danger alarm warning overlay directly in center-bottom of feed
    if cs.warning_msg and time.time() - cs.warning_time < 6.0:
        pw = _pulse(3.0)
        wc = tuple(int(c * (0.3 + pw * 0.7)) for c in C_RED)
        _panel(img, tx1 + 16, ty2 - 58, tx2 - 16, ty2 - 38, a=0.75, border_color=wc)
        _text_c(img, "🚨  " + cs.warning_msg[:45].upper(), (tx1 + tx2) // 2, ty2 - 45, 0.28, wc, bold=True)

def _draw_detection_overlays(tile, dets, sx_s, sy_s):
    """Draw gold targeting brackets + labels for all detections with high-end holographic outline."""
    for det in dets:
        bx1, by1, bx2, by2 = det["box"]
        bx1 = int(bx1 * sx_s)
        bx2 = int(bx2 * sx_s)
        by1 = int(by1 * sy_s)
        by2 = int(by2 * sy_s)
        
        with _fdb_lock:
            is_known = faces_db.get(det.get("pid"), {}).get("known", False)
            
        if det["label"] == "person":
            d_col = C_GREEN if is_known else C_RED
        else:
            d_col = C_GOLD
            
        p_col = tuple(int(c * (0.6 + _pulse(2.0) * 0.4)) for c in d_col)
        
        # 1. Subtle glowing semi-transparent bounding box outline
        for offset in range(2, 0, -1):
            alpha = 0.04 * (3 - offset)
            gc = tuple(int(c * alpha) for c in d_col)
            cv2.rectangle(tile, (bx1 - offset, by1 - offset), (bx2 + offset, by2 + offset), gc, 1, cv2.LINE_AA)
        cv2.rectangle(tile, (bx1, by1), (bx2, by2), p_col, 1, cv2.LINE_AA)
        
        # 2. Holographic target corner brackets
        _corner_brackets(tile, bx1, by1, bx2, by2, p_col, L=12, T=2)
        
        # 3. Floating glass chip label
        pid_str = det.get('disp', '')[:12]
        conf_str = f"{det['conf']:.0%}"
        chip = f"🎯 {pid_str.upper()} ({conf_str})"
        
        font = get_pil_font("segoe_bold", 10)
        try:
            bbox = font.getbbox(chip)
            tw2 = bbox[2] - bbox[0]
            th2 = bbox[3] - bbox[1]
        except AttributeError:
            tw2, th2 = font.getsize(chip)
            
        chy = max(4, by1 - 22)
        
        # Floating rounded glass label background
        _panel(tile, bx1, chy, bx1 + tw2 + 16, chy + 20, a=0.72, border_color=p_col)
        _text(tile, chip, bx1 + 8, chy + 14, 0.26, p_col, bold=True)

def _draw_hbar(img, x, y, w, h, pct, color):
    """Futuristic horizontal telemetry progress bar with soft glow and clean rounded track."""
    # Rounded container track (graphite gray)
    _fill_rounded_rect(img, x, y, x + w, y + h, h // 2, (20, 20, 20))
    _rounded_rect(img, x, y, x + w, y + h, h // 2, C_BORDER, 1)
    
    # Calculate fill width
    fill_w = int(w * max(0.0, min(1.0, pct / 100.0)))
    if fill_w > 4:
        # Draw glowing filled rounded rect
        _fill_rounded_rect(img, x, y, x + fill_w, y + h, h // 2, color)
        
        # Soft outer bloom glow for the progress fill
        for offset in range(2, 0, -1):
            alpha = 0.12 * (3 - offset)
            gc = tuple(int(c * alpha) for c in color)
            _rounded_rect(img, x - offset, y - offset, x + fill_w + offset, y + h + offset, h // 2 + offset, gc, 1)

def draw_nav_tabs(img: np.ndarray):
    """Integrated into header — no separate nav bar needed (UI_NAV_H=0)"""
    pass  # Navigation is part of the header now

def _rounded_rect(img, x1, y1, x2, y2, r, color, thick=1):
    """Draws a smooth anti-aliased rounded rectangle outline."""
    cv2.line(img, (x1 + r, y1), (x2 - r, y1), color, thick, cv2.LINE_AA)
    cv2.line(img, (x1 + r, y2), (x2 - r, y2), color, thick, cv2.LINE_AA)
    cv2.line(img, (x1, y1 + r), (x1, y2 - r), color, thick, cv2.LINE_AA)
    cv2.line(img, (x2, y1 + r), (x2, y2 - r), color, thick, cv2.LINE_AA)
    cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thick, cv2.LINE_AA)
    cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thick, cv2.LINE_AA)
    cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thick, cv2.LINE_AA)
    cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thick, cv2.LINE_AA)

def _fill_rounded_rect(img, x1, y1, x2, y2, r, color):
    """Fills a smooth anti-aliased rounded rectangle."""
    cv2.rectangle(img, (x1 + r, y1), (x2 - r, y2), color, -1)
    cv2.rectangle(img, (x1, y1 + r), (x2, y2 - r), color, -1)
    cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, -1, cv2.LINE_AA)
    cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, -1, cv2.LINE_AA)
    cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, -1, cv2.LINE_AA)
    cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, -1, cv2.LINE_AA)

def _panel(img, x1, y1, x2, y2, a=0.72, border=True, border_color=None):
    """Futuristic holographic glassmorphic panel: true backdrop blur + double ambient glowing gold rims."""
    x1, y1, x2, y2 = _clamp_rect(img, x1, y1, x2, y2)
    if x2 <= x1 or y2 <= y1: return
    r = 20  # AAA cinematic 20px rounded corners
    
    # 1. Extract background ROI
    roi = img[y1:y2, x1:x2].copy()
    
    # 2. Apply real-time backdrop blur (fluent glassmorphism)
    blurred = cv2.blur(roi, (21, 21))
    
    # 3. Blend transparent surface overlay: BGR (20, 20, 20) with alpha a=0.72
    overlay = np.zeros_like(roi)
    _fill_rounded_rect(overlay, 0, 0, x2 - x1, y2 - y1, r, (20, 20, 20))
    
    # Create mask for rounded panel region to only blur and overlay inside the rounded panel
    mask = np.zeros((y2 - y1, x2 - x1), dtype=np.uint8)
    _fill_rounded_rect(mask, 0, 0, x2 - x1, y2 - y1, r, 255)
    
    # Blend blurred + transparent surface onto roi inside mask
    glass = cv2.addWeighted(overlay, a, blurred, 1.0 - a, 0)
    
    # Apply masked copy
    idx = (mask > 0)
    roi[idx] = glass[idx]
    img[y1:y2, x1:x2] = roi
    
    # 4. Premium cinematic border rim lighting
    if border:
        col = border_color or (55, 175, 212) # Soft gold BGR
        # Soft outer border glow (3px, low alpha)
        for offset in range(2, 0, -1):
            alpha = 0.05 * (3 - offset)
            gc = tuple(int(c * alpha) for c in col)
            _rounded_rect(img, x1 - offset, y1 - offset, x2 + offset, y2 + offset, r + offset, gc, 1)
            
        # Crisp solid inner border (1px, BGR Gold)
        _rounded_rect(img, x1, y1, x2, y2, r, col, 1)
        
        # Soft inner reflection rim (1px, offset by 2px, graphite/silver tint)
        inner_col = tuple(max(0, int(c * 0.45)) for c in col)
        _rounded_rect(img, x1 + 2, y1 + 2, x2 - 2, y2 - 2, max(0, r - 2), inner_col, 1)

def _gold_line(img, x1, y, x2, alpha=0.7):
    """Thin gold separator line with adjustable opacity."""
    gc = tuple(int(c * alpha) for c in C_GOLD)
    cv2.line(img, (x1,y), (x2,y), gc, 1, cv2.LINE_AA)

def _pulse(hz=1.2): return (math.sin(time.time()*2*math.pi*hz)+1.0)/2.0

_font_cache = {}

def get_pil_font(font_name, size):
    from PIL import ImageFont
    key = (font_name, size)
    if key not in _font_cache:
        # Standard fonts on Windows
        font_path = "C:\\Windows\\Fonts\\segoeui.ttf"  # Default Segoe UI
        if font_name == "segoe_bold":
            font_path = "C:\\Windows\\Fonts\\seguisb.ttf"  # Segoe UI Semibold
        elif font_name == "segoe_light":
            font_path = "C:\\Windows\\Fonts\\segoeuil.ttf"  # Segoe UI Light
        elif font_name == "consolas":
            font_path = "C:\\Windows\\Fonts\\consola.ttf"  # Consolas for telemetry
            
        try:
            _font_cache[key] = ImageFont.truetype(font_path, size)
        except Exception:
            try:
                _font_cache[key] = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", size)
            except Exception:
                _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]

def _text_pil(img, s, x, y, font_size=14, color=(245, 245, 245), font_name="segoe"):
    from PIL import Image, ImageDraw
    s_str = str(s)
    if not s_str:
        return
        
    font = get_pil_font(font_name, font_size)
    
    try:
        bbox = font.getbbox(s_str)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
    except AttributeError:
        tw, th = font.getsize(s_str)
        
    H, W = img.shape[:2]
    # Clamp coordinates
    x1 = max(0, min(W - 1, x))
    y1 = max(0, min(H - 1, y - th - 8))
    x2 = max(0, min(W - 1, x + tw + 10))
    y2 = max(0, min(H - 1, y + th + 10))
    
    if x2 <= x1 or y2 <= y1:
        return
        
    # Crop ROI and blend PIL text
    roi = img[y1:y2, x1:x2]
    roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(roi_rgb)
    draw = ImageDraw.Draw(pil_img)
    
    # Convert color (BGR to RGB)
    color_rgb = (color[2], color[1], color[0])
    draw.text((x - x1, y - y1 - th), s_str, font=font, fill=color_rgb)
    
    # Paste back
    roi_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    img[y1:y2, x1:x2] = roi_bgr

def _text(img, s, x, y, scale=0.35, color=None, bold=False):
    color = color or C_TEXT
    font_name = "segoe_bold" if bold else "segoe"
    if scale >= 0.45:
        font_name = "segoe_bold"
    elif scale <= 0.28:
        font_name = "segoe"
    
    font_size = max(12, int(scale * 40))
    _text_pil(img, s, x, y, font_size, color, font_name)

def _text_c(img, s, cx, y, scale=0.35, color=None, bold=False):
    color = color or C_TEXT
    font_name = "segoe_bold" if bold else "segoe"
    if scale >= 0.45:
        font_name = "segoe_bold"
    font_size = max(12, int(scale * 40))
    
    font = get_pil_font(font_name, font_size)
    s_str = str(s)
    try:
        bbox = font.getbbox(s_str)
        tw = bbox[2] - bbox[0]
    except AttributeError:
        tw, _ = font.getsize(s_str)
        
    _text_pil(img, s, cx - tw // 2, y, font_size, color, font_name)

def _text_r(img, s, rx, y, scale=0.35, color=None, bold=False):
    color = color or C_TEXT
    font_name = "segoe_bold" if bold else "segoe"
    if scale >= 0.45:
        font_name = "segoe_bold"
    font_size = max(12, int(scale * 40))
    
    font = get_pil_font(font_name, font_size)
    s_str = str(s)
    try:
        bbox = font.getbbox(s_str)
        tw = bbox[2] - bbox[0]
    except AttributeError:
        tw, _ = font.getsize(s_str)
        
    _text_pil(img, s, rx - tw, y, font_size, color, font_name)

# ── TOP HEADER — Cinematic Floating Command Bar ────────────────────────────────
def draw_header(img: np.ndarray, cameras):
    W = img.shape[1]
    pad = UI_PAD

    # ── MAIN FLOATING TOPBAR GLASS PANEL ──
    _panel(img, pad, pad, W - pad, pad + UI_HDR_H, a=0.88)

    # Logo hex badge left
    cx_logo = pad + 44; cy_logo = pad + 40
    pts_hex = np.array([
        [cx_logo, cy_logo - 24],
        [cx_logo + 20, cy_logo - 12],
        [cx_logo + 20, cy_logo + 12],
        [cx_logo, cy_logo + 24],
        [cx_logo - 20, cy_logo + 12],
        [cx_logo - 20, cy_logo - 12]
    ], np.int32)
    cv2.fillPoly(img, [pts_hex], (18, 60, 90))  # Dark gold fill
    cv2.polylines(img, [pts_hex], True, C_GOLD, 2, cv2.LINE_AA)
    _text_c(img, "AT", cx_logo, cy_logo + 6, 0.42, C_GOLD, bold=True)

    # Title block
    _text(img, "OMS  v9.0", pad + 82, pad + 34, 0.72, C_GOLD, bold=True)
    _text(img, "OBJECT MONITORING SYSTEM", pad + 82, pad + 57, 0.30, C_TEXT)
    _text(img, "AUTONOMOUS AI SURVEILLANCE SUPERCOMPUTER", pad + 82, pad + 74, 0.24, C_DIM)

    # Center: Clock & Date
    now_dt = datetime.now()
    _text_c(img, now_dt.strftime("%H:%M:%S"), W // 2, pad + 46, 0.75, C_GOLD, bold=True)
    _text_c(img, now_dt.strftime("%d %b %Y  —  %A").upper(), W // 2, pad + 68, 0.26, C_DIM)

    # Right: HW stats capsules
    cap_w = 74; cap_h = 56; cap_y = pad + 12
    rx = W - pad - 6 * cap_w - 5 * 6  # start x of capsule row

    cpu_pct = psutil.cpu_percent(interval=None) if PSUTIL_AVAILABLE else 0.0
    ram_pct = psutil.virtual_memory().percent if PSUTIL_AVAILABLE else 0.0
    cpu_col = C_RED if cpu_pct > 80 else (C_ORANGE if cpu_pct > 60 else C_GREEN)
    ram_col = C_RED if ram_pct > 85 else (C_ORANGE if ram_pct > 70 else C_TEXT)
    cuda_col = C_GREEN if CUDA_AVAILABLE else C_RED

    caps = [
        ("PROFILE",   HW_PROFILE,                      C_GOLD,   C_BORDER),
        ("CUDA",      "ON" if CUDA_AVAILABLE else "OFF", cuda_col, cuda_col),
        ("CPU MODE",  "CUDA" if CUDA_AVAILABLE else "CPU", C_TEXT, C_BORDER),
        ("CPU LOAD",  f"{cpu_pct:.0f}%",                cpu_col,  C_BORDER),
        ("RAM USAGE", f"{ram_pct:.0f}%",                ram_col,  C_BORDER),
    ]
    for label, val, vcol, bcol in caps:
        _panel(img, rx, cap_y, rx + cap_w, cap_y + cap_h, a=0.9, border_color=bcol)
        _text_c(img, label,  rx + cap_w // 2, cap_y + 20, 0.22, C_DIM)
        _text_c(img, val,    rx + cap_w // 2, cap_y + 44, 0.36, vcol, bold=True)
        rx += cap_w + 6

    # Animated radar disc
    radar_cx = W - pad - 36; radar_cy = pad + 40; radar_r = 28
    # Radar rings
    cv2.circle(img, (radar_cx, radar_cy), radar_r,     (20, 55, 75), 1, cv2.LINE_AA)
    cv2.circle(img, (radar_cx, radar_cy), radar_r//2,  (15, 40, 55), 1, cv2.LINE_AA)
    cv2.circle(img, (radar_cx, radar_cy), radar_r//4,  (10, 30, 40), 1, cv2.LINE_AA)
    # Rotating sweep
    angle = (time.time() * 150) % 360
    rad_a = math.radians(angle)
    ex_r = int(radar_cx + radar_r * math.cos(rad_a))
    ey_r = int(radar_cy + radar_r * math.sin(rad_a))
    cv2.line(img, (radar_cx, radar_cy), (ex_r, ey_r), C_GOLD, 2, cv2.LINE_AA)
    # Sweep trail
    for tr in range(1, 8):
        a2 = math.radians(angle - tr * 10)
        ex2 = int(radar_cx + radar_r * math.cos(a2))
        ey2 = int(radar_cy + radar_r * math.sin(a2))
        fade = max(0, int(180 - tr * 26))
        gcol = (int(C_GOLD[0] * fade / 255), int(C_GOLD[1] * fade / 255), int(C_GOLD[2] * fade / 255))
        cv2.line(img, (radar_cx, radar_cy), (ex2, ey2), gcol, 1, cv2.LINE_AA)
    # Center dot
    cv2.circle(img, (radar_cx, radar_cy), 3, C_GOLD_BRIGHT, -1, cv2.LINE_AA)
    # Blip dots
    pulse_r = _pulse(1.2)
    for bx, by in [(radar_cx + 8, radar_cy - 10), (radar_cx - 12, radar_cy + 6)]:
        bc = tuple(int(c * (0.5 + pulse_r * 0.5)) for c in C_GREEN)
        cv2.circle(img, (bx, by), 2, bc, -1, cv2.LINE_AA)

    # Operator label + system online pill
    op_x = W - pad - 6 * cap_w - 5 * 6 - 200
    _text_r(img, f"OPERATOR: {Config.USERNAME.upper()}", op_x, pad + 30, 0.30, C_TEXT)
    # System online pill
    pill_x1 = op_x - 150; pill_x2 = op_x - 10
    pill_y1 = pad + 38; pill_y2 = pad + 62
    live_cnt = sum(1 for c in cameras if c.online)
    _fill_rounded_rect(img, pill_x1, pill_y1, pill_x2, pill_y2, 8, (8, 40, 15))
    _rounded_rect(img, pill_x1, pill_y1, pill_x2, pill_y2, 8, C_GREEN, 1)
    pulse_v = _pulse(1.5)
    dot_c = tuple(int(c * (0.5 + pulse_v * 0.5)) for c in C_GREEN)
    cv2.circle(img, (pill_x1 + 16, (pill_y1 + pill_y2) // 2), 4, dot_c, -1, cv2.LINE_AA)
    _text_c(img, "SYSTEM ONLINE", (pill_x1 + pill_x2) // 2 + 6, pill_y1 + 17, 0.26, C_GREEN, bold=True)

# ── LEFT SIDEBAR — Floating Glass Navigation Rail ─────────────────────────────
def draw_side_panel(img: np.ndarray, cameras):
    global selected_cam_idx
    W = img.shape[1]; H = img.shape[0]
    pad = UI_PAD

    # Floating left glass panel
    x1 = pad; y1 = pad * 2 + UI_HDR_H
    x2 = x1 + UI_LEFT_W; y2 = H - pad - UI_FOOT_H
    _panel(img, x1, y1, x2, y2, a=0.82)

    px1 = x1 + 18; px2 = x2 - 18
    cx = (px1 + px2) // 2
    y = y1 + 22

    # ── 1. SYSTEM STATUS ────────────────────────────────────────────────────
    _text(img, "SYSTEM STATUS", px1, y, 0.46, C_GOLD, bold=True)
    y += 24

    statuses = [
        ("YOLO ENGINE",  "ONLINE",    True),
        ("FACE RECOG",   "ONLINE",    True),
        ("DATABASE",     "CONNECTED", True),
        ("TELEGRAM BOT", "CONNECTED", True),
        ("SYSTEM MON",   "ONLINE",    True),
    ]
    for label, val, ok in statuses:
        col = C_GREEN if ok else C_RED
        _status_dot(img, px1 + 8, y + 9, 4, col)
        _text(img, label, px1 + 20, y + 13, 0.34, C_DIM)
        _text_r(img, val, px2 - 4, y + 13, 0.30, col, bold=True)
        y += 22

    y += 10
    _gold_line(img, px1, y, px2, 0.25)
    y += 16

    # ── 2. ACTIVE CAMERAS ───────────────────────────────────────────────────
    live_cnt = sum(1 for c in cameras if c.online)
    _text(img, f"ACTIVE CAMERAS ({live_cnt}/{len(cameras)})", px1, y, 0.46, C_GOLD, bold=True)
    y += 22

    for i, cs in enumerate(cameras):
        is_sel = (i == selected_cam_idx)
        row_h = 30
        if is_sel:
            _fill_rounded_rect(img, px1, y, px2, y + row_h, 6, (15, 45, 55))
            _rounded_rect(img, px1, y, px2, y + row_h, 6, C_GOLD, 1)
        dot_col = C_GREEN if cs.online else (C_RED if cs.disconnected else C_DIM)
        _status_dot(img, px1 + 10, y + row_h // 2, 4, dot_col, animate=cs.online)
        _text(img, cs.name[:16].upper(), px1 + 24, y + row_h - 8, 0.34,
              C_GOLD if is_sel else C_TEXT, bold=is_sel)
        stat = "LIVE" if cs.online else ("OFFLINE" if cs.disconnected else "STANDBY")
        _text_r(img, stat, px2 - 6, y + row_h - 8, 0.28, dot_col, bold=is_sel)
        y += row_h + 4

    y += 6
    _gold_line(img, px1, y, px2, 0.25)
    y += 16

    # ── 4. TODAY'S SUMMARY ──────────────────────────────────────────────────
    _text(img, "TODAY'S SUMMARY", px1, y, 0.46, C_GOLD, bold=True)
    y += 22

    total_det = sum(cs.persons_detected for cs in cameras)
    with _fdb_lock:
        known_p = sum(1 for d in faces_db.values() if d.get("known"))
        unknown_p = sum(1 for d in faces_db.values() if not d.get("known"))

    summary_rows = [
        ("Total Detections",  total_det),
        ("Persons Detected",  total_det),
        ("Known Persons",     known_p),
        ("Unknown Persons",   unknown_p),
        ("Objects Added",     _objs_added),
        ("Objects Removed",   _objs_removed),
        ("Alerts Generated",  _alerts_generated),
    ]
    for label, val in summary_rows:
        if y > y2 - 60: break
        _text(img, label, px1 + 4, y + 13, 0.30, C_DIM)
        _text_r(img, str(val), px2 - 4, y + 13, 0.32, C_GOLD if val > 0 else C_DIM, bold=bool(val))
        y += 20

    # Bottom logo
    logo_y = y2 - 50
    if logo_y > y + 10:
        _gold_line(img, px1, logo_y, px2, 0.20)
        _text_c(img, "OMS v9.0.0", cx, logo_y + 24, 0.30, C_GOLD, bold=True)

# ── RIGHT PANEL — Analytics & System Monitor ──────────────────────────────────
def draw_event_panel(img: np.ndarray):
    W = img.shape[1]; H = img.shape[0]
    pad = UI_PAD

    # Floating right glass panel
    x1 = W - pad - UI_RIGHT_W; y1 = pad * 2 + UI_HDR_H
    x2 = W - pad;               y2 = H - pad - UI_FOOT_H
    _panel(img, x1, y1, x2, y2, a=0.82)

    px1 = x1 + 18; px2 = x2 - 18
    cx = (px1 + px2) // 2
    spark_w = px2 - px1
    y = y1 + 22

    # ── 1. RECENT EVENTS ────────────────────────────────────────────────────
    _text(img, "RECENT EVENTS", px1, y, 0.46, C_GOLD, bold=True)
    # View all link
    _text_r(img, "View all", px2, y, 0.26, C_DIM)
    y += 26

    with _event_ring_lock:
        items = list(_event_ring)[-8:]

    for log_str, ev, ts in reversed(items):
        if y > y1 + 280: break
        if "ENTERED" in ev or "RETURN" in ev:
            col = C_GREEN; cat = "PERSON ARRIVED"
        elif "INTRUDER" in ev:
            col = C_RED; cat = "INTRUDER ALERT"
        elif "LEFT" in ev:
            col = C_CYAN; cat = "PERSON LEFT"
        elif "OBJ_ADDED" in ev:
            col = C_GOLD; cat = "OBJECT ADDED"
        elif "OBJ_REMOVED" in ev:
            col = C_ORANGE; cat = "OBJECT REMOVED"
        elif "ZONE" in ev:
            col = C_RED; cat = "ZONE BREACH"
        elif "BEHAVIOR" in ev:
            col = C_ORANGE; cat = "BEHAVIOR"
        else:
            col = C_DIM; cat = ev[:14].upper()

        age = time.time() - ts
        fade = max(0.35, 1.0 - age / 90.0)
        dc = tuple(int(c * fade) for c in col)
        ts_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S")

        # Event row with colored left accent bar
        _fill_rect(img, px1, y + 2, px1 + 3, y + 16, dc)
        _text(img, ts_str, px1 + 8, y + 13, 0.26, C_DIM)
        _text(img, cat, px1 + 70, y + 13, 0.30, dc, bold=True)
        y += 20

    y += 8
    _gold_line(img, px1, y, px2, 0.22)
    y += 16

    # ── 2. SYSTEM MONITOR ───────────────────────────────────────────────────
    _text(img, "SYSTEM MONITOR", px1, y, 0.46, C_GOLD, bold=True)
    y += 26

    cpu_pct  = list(_cpu_spark)[-1]  if _cpu_spark  else 0.0
    ram_pct  = list(_ram_spark)[-1]  if _ram_spark  else 0.0
    disk_pct = list(_disk_spark)[-1] if _disk_spark else 0.0

    monitors = [
        ("CPU USAGE",    _cpu_spark,  cpu_pct,  C_GREEN),
        ("RAM USAGE",    _ram_spark,  ram_pct,  C_GOLD),
        ("DISK USAGE",   _disk_spark, disk_pct, C_ORANGE),
    ]
    for label, spark, pct, col in monitors:
        if y > y2 - 200: break
        _text(img, label, px1, y + 12, 0.30, C_DIM)
        pct_col = C_RED if pct > 85 else col
        _text_r(img, f"{pct:.0f}%", px2, y + 12, 0.32, pct_col, bold=True)
        y += 18
        _draw_hbar(img, px1, y, spark_w, 7, pct, col)
        y += 14
        _draw_sparkline(img, px1, y, spark_w, 22, spark, col)
        y += 30

    # Network bandwidth
    if y < y2 - 80:
        _text(img, "NETWORK BANDWIDTH", px1, y + 12, 0.30, C_DIM)
        try:
            nc = psutil.net_io_counters() if PSUTIL_AVAILABLE else None
            if nc:
                sent_kb = nc.bytes_sent / 1024
                recv_kb = nc.bytes_recv / 1024
                net_str = f"↑{sent_kb:.0f} KB/s  ↓{recv_kb:.0f} KB/s"
            else:
                net_str = "OFFLINE"
        except:
            net_str = "OFFLINE"
        _text_r(img, net_str, px2, y + 12, 0.26, C_CYAN, bold=True)
        y += 20
        _draw_sparkline(img, px1, y, spark_w, 20, _net_spark, C_CYAN)
        y += 30

    _gold_line(img, px1, y, px2, 0.22)
    y += 16

    # ── 3. TELEGRAM STATUS ──────────────────────────────────────────────────
    if y < y2 - 110:
        _text(img, "TELEGRAM STATUS", px1, y, 0.46, C_GOLD, bold=True)
        y += 24

        tg_ok = REQUESTS_AVAILABLE and bool(Config.BOT_TOKEN)
        tg_col = C_GREEN if tg_ok else C_RED

        # Telegram card
        tg_card_h = 80
        _fill_rounded_rect(img, px1, y, px2, y + tg_card_h, 10, (8, 25, 12) if tg_ok else (25, 8, 8))
        _rounded_rect(img, px1, y, px2, y + tg_card_h, 10, tg_col, 1)

        _status_dot(img, px1 + 16, y + 22, 5, tg_col, animate=tg_ok)
        _text(img, "STATUS", px1 + 30, y + 18, 0.28, C_DIM)
        _text_r(img, "CONNECTED" if tg_ok else "OFFLINE", px2 - 8, y + 18, 0.30, tg_col, bold=True)
        _text(img, f"BOT: OMS Surveillance Bot", px1 + 8, y + 36, 0.26, C_DIM)
        _text(img, f"CHAT ID: {Config.CHAT_ID}", px1 + 8, y + 52, 0.26, C_DIM)
        _text(img, f"QUEUED: 0 / 128", px1 + 8, y + 68, 0.26, C_DIM)
        y += tg_card_h + 14

        # Test message button
        if y < y2 - 40:
            btn_y1 = y; btn_y2 = y + 36
            _fill_rounded_rect(img, px1, btn_y1, px2, btn_y2, 8, (15, 60, 25) if tg_ok else (25, 15, 8))
            _rounded_rect(img, px1, btn_y1, px2, btn_y2, 8, tg_col, 1)
            _text_c(img, "TEST MESSAGE", cx, btn_y1 + 23, 0.34, tg_col, bold=True)

# ── DYNAMIC HUD GLASS OVERLAY ─────────────────────────────────────────────────
def _draw_hud_glass_overlay(img: np.ndarray, cs, tx1: int, ty1: int, tx2: int, ty2: int, dets):
    """Draws premium, highly transparent glass panels carrying diagnostic telemetry directly over the camera feed."""
    fx1, fy1, fx2, fy2 = tx1 + 10, ty1 + 10, tx2 - 10, ty2 - 10
    tw = fx2 - fx1
    th = fy2 - fy1
    
    # Left and Right subpanel widths
    lm_w = 160 if tw < 800 else 230
    lm_x1 = fx1 + 12
    lm_x2 = lm_x1 + lm_w
    lm_y1 = fy1 + 32
    lm_y2 = fy2 - 32
    
    rm_w = 160 if tw < 800 else 230
    rm_x2 = fx2 - 12
    rm_x1 = rm_x2 - rm_w
    rm_y1 = fy1 + 32
    rm_y2 = fy2 - 32
    
    # Semi-transparent glassy panels (alpha = 0.55 for perfect balance of readability & transparency)
    _panel(img, lm_x1, lm_y1, lm_x2, lm_y2, a=0.55, border_color=C_BORDER)
    _panel(img, rm_x1, rm_y1, rm_x2, rm_y2, a=0.55, border_color=C_BORDER)
    
    # Typography scales
    s1 = 0.28 if tw < 800 else 0.36
    s2 = 0.24 if tw < 800 else 0.30
    gap = 16 if tw < 800 else 22
    
    # ── LEFT GLASS PANEL (Stream Telemetry) ──
    ly = lm_y1 + 18
    _text(img, "STREAM TELEMETRY", lm_x1 + 12, ly, s1, C_GOLD, bold=True)
    ly += gap + 2
    
    # Signal Strength Bars
    _text(img, "SIGNAL", lm_x1 + 12, ly, s2, C_DIM)
    sig_x = lm_x1 + 65 if tw < 800 else lm_x1 + 90
    for b in range(5):
        bx = sig_x + b * 6
        by = ly + 2
        bar_h = 2 + b * 2
        color = C_GREEN if (cs.online and b < 4) else (C_RED if not cs.online else C_DIM)
        _fill_rect(img, bx, by - bar_h, bx + 4, by, color)
    ly += gap
    
    _text(img, "CODEC: H.264 SECURE", lm_x1 + 12, ly, s2, C_DIM)
    ly += gap
    _text(img, f"BITRATE: {4.8 if cs.online else 0.0:.1f} MBPS", lm_x1 + 12, ly, s2, C_TEXT)
    ly += gap
    _text(img, f"LATENCY: {12 if cs.online else 0:.0f} MS", lm_x1 + 12, ly, s2, C_TEXT)
    
    # Extra stats for larger cards
    if th > 280:
        ly += gap
        _text(img, "LOSS: 0.00%", lm_x1 + 12, ly, s2, C_DIM)
        ly += gap
        _text(img, "ENCODE: HW_NVENC", lm_x1 + 12, ly, s2, C_DIM)
        
    # ── RIGHT GLASS PANEL (AI Target Matrix) ──
    ry = rm_y1 + 18
    _text(img, "AI CORE STATUS", rm_x1 + 12, ry, s1, C_GOLD, bold=True)
    ry += gap + 2
    
    act_lbls = list(set(d["label"] for d in dets))
    if act_lbls:
        targets_str = f"TARGETS: {', '.join(act_lbls).upper()[:16]}"
        _text(img, targets_str, rm_x1 + 12, ry, s2, C_GOLD, bold=True)
    else:
        _text(img, "TARGETS: SECURE", rm_x1 + 12, ry, s2, C_GREEN)
    ry += gap
    
    _text(img, "PERIMETER STATUS: SECURE", rm_x1 + 12, ry, s2, C_GREEN)
    ry += gap
    _text(img, "LOITER DETECT: ARMED", rm_x1 + 12, ry, s2, C_TEXT)
    ry += gap
    _text(img, f"UPTIME: {cs.uptime_str}", rm_x1 + 12, ry, s2, C_TEXT)
    
    if th > 280:
        ry += gap
        _text(img, "SAFETY LEVEL: MAX", rm_x1 + 12, ry, s2, C_GREEN)
        ry += gap
        _text(img, "RECORD STATE: SYNC", rm_x1 + 12, ry, s2, C_DIM)

# ── CAMERA GRID — Cinematic AI Vision Modules ─────────────────────────────────
def draw_camera_grid(img: np.ndarray, cameras):
    global selected_cam_idx, hud_overlay_active, cam_area_pct, is_fs_state
    W = img.shape[1]; H = img.shape[0]
    pad = UI_PAD
    _now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ticker = (
        f"  >>>  AUTONOMOUS AI EXECUTIVE ASSISTANT SYSTEM ONLINE  >>>  24/7 OPERATION  >>>  "
        f"CORE SYSTEM INTEGRITY SECURE  >>>  OPERATOR: {Config.USERNAME.upper()}  >>>  "
        f"HW PROFILE: {HW_PROFILE}  >>>  CUDA: {'ENABLED' if CUDA_AVAILABLE else 'DISABLED'}  >>>  "
        f"LIVE CHANNELS: {sum(1 for c in cameras if c.online)}/{len(cameras)}  >>>  {_now}  >>>  "
    )

    if is_fs_state:
        sx, top, ex, info_area_y = 0, 0, W, H
        gw, gh = W, H
    else:
        # Camera grid area: between left/right panels, below header
        sx  = pad * 2 + UI_LEFT_W
        ex  = W - pad * 2 - UI_RIGHT_W
        top = pad * 2 + UI_HDR_H
        # Bottom of cameras: leave room for bottom analytics
        bottom_analytics_h = 280
        info_area_y = H - pad - UI_FOOT_H - bottom_analytics_h

        gw = ex - sx
        gh = info_area_y - top

    f_idx = getattr(Config, "focused_cam_idx", -1)

    def _render_cam_tile(img, cs, tx1, ty1, tx2, ty2, is_large=False, is_sel=False):
        """Render a single camera tile with cinematic glass panel and AI HUD."""
        c_border = C_GOLD if is_sel else (THREAT_COLORS.get(cs.threat_level, C_GREEN) if cs.online else C_DIM)

        # Outer cinematic glass panel
        _panel(img, tx1, ty1, tx2, ty2, a=0.80, border_color=c_border)

        # Inner feed bounds (tight padding)
        feed_x1 = tx1 + 8; feed_y1 = ty1 + 8
        feed_x2 = tx2 - 8; feed_y2 = ty2 - 8
        fw_w = max(1, feed_x2 - feed_x1)
        fw_h = max(1, feed_y2 - feed_y1)

        feed = None; dets = []
        if not cs.disconnected and cs.online:
            with cs.frame_lock:
                if cs.latest_frame is not None:
                    feed = cs.latest_frame.copy()
                    dets = list(cs.latest_dets)

        if feed is None:
            tile_full = np.zeros((fw_h, fw_w, 3), dtype=np.uint8)
            _draw_loading_tile(tile_full, cs.name)
            img[feed_y1:feed_y2, feed_x1:feed_x2] = tile_full
        else:
            tile_full, new_dets = _aspect_crop_to_fill(feed, dets, fw_w, fw_h)
            _draw_detection_overlays(tile_full, new_dets, 1.0, 1.0)

            # Animated scanning reticle on active/selected cam
            if cs.online and (is_large or is_sel):
                sc_cy = fw_h // 2; sc_cx = fw_w // 2
                sweep_angle = (time.time() * 110) % 360
                r_size = 40 if is_large else 26
                cv2.ellipse(tile_full, (sc_cx, sc_cy), (r_size, r_size),
                            sweep_angle, 0, 70, C_GOLD, 1, cv2.LINE_AA)
                # Cross hairs
                for dx, dy in [(-r_size-10, 0), (r_size+10, 0), (0, -r_size-10), (0, r_size+10)]:
                    cv2.circle(tile_full, (sc_cx + dx, sc_cy + dy), 2, C_GOLD, -1, cv2.LINE_AA)

            # Corner scan lines — cinematic targeting feel
            L = 18
            for (cx_c, cy_c, dx, dy) in [
                (0, 0, 1, 1), (fw_w, 0, -1, 1), (0, fw_h, 1, -1), (fw_w, fw_h, -1, -1)
            ]:
                gold_a = tuple(int(c * 0.6) for c in C_GOLD)
                cv2.line(tile_full, (cx_c, cy_c), (cx_c + dx*L, cy_c), gold_a, 2, cv2.LINE_AA)
                cv2.line(tile_full, (cx_c, cy_c), (cx_c, cy_c + dy*L), gold_a, 2, cv2.LINE_AA)

            # Threat flash border
            flash = time.time() - cs.det_flash_t
            if flash < 1.5:
                fc = C_RED if "Intruder" in cs.det_flash_pid else C_GOLD
                thickness = max(1, int((1.5 - flash) * 6))
                cv2.rectangle(tile_full, (0, 0), (fw_w - 1, fw_h - 1), fc, thickness)

            img[feed_y1:feed_y2, feed_x1:feed_x2] = tile_full

            # HUD glass overlay
            if hud_overlay_active:
                _draw_hud_glass_overlay(img, cs, tx1, ty1, tx2, ty2, new_dets)

        # Camera HUD (status, name, time, FPS)
        _draw_cam_hud(img, cs, tx1, ty1, tx2, ty2, c_border, large=is_large)

    if f_idx >= 0 and f_idx < len(cameras):
        # ── SINGLE FOCUS MODE ───────────────────────────────────────────────
        cs = cameras[f_idx]
        _render_cam_tile(img, cs, sx, top, ex, info_area_y, is_large=True, is_sel=True)
        cs.tile_rect = (sx, top, ex, info_area_y)
        for i, c in enumerate(cameras):
            if i != f_idx:
                c.tile_rect = (-1, -1, -1, -1)
        return info_area_y

    # ── DYNAMIC GRID MODE ───────────────────────────────────────────────────
    num_cams = len(cameras)
    if num_cams <= 1:
        cols, rows = 1, 1
    elif num_cams <= 2:
        cols, rows = 2, 1
    elif num_cams <= 4:
        cols, rows = 2, 2
    elif num_cams <= 6:
        cols, rows = 3, 2
    elif num_cams <= 8:
        cols, rows = 4, 2
    elif num_cams <= 9:
        cols, rows = 3, 3
    else:
        import math
        cols = int(math.ceil(math.sqrt(num_cams)))
        rows = int(math.ceil(num_cams / cols))
    
    gap = 14
    tile_w = (gw - gap * (cols - 1)) // cols
    tile_h = (gh - gap * (rows - 1)) // rows

    for idx, cs in enumerate(cameras):
        c_row = idx // cols; c_col = idx % cols
        tx1 = sx + c_col * (tile_w + gap)
        ty1 = top + c_row * (tile_h + gap)
        tx2 = tx1 + tile_w
        ty2 = ty1 + tile_h
        is_sel = (idx == selected_cam_idx)
        _render_cam_tile(img, cs, tx1, ty1, tx2, ty2, is_large=False, is_sel=is_sel)
        cs.tile_rect = (tx1, ty1, tx2, ty2)

    return info_area_y

# ── CENTER-BOTTOM ANALYTICS ROW — 3 Premium Cards ────────────────────────────
def draw_center_bottom(img: np.ndarray, cameras, info_area_y: int):
    W = img.shape[1]; H = img.shape[0]
    pad = UI_PAD

    sx  = pad * 2 + UI_LEFT_W
    ex  = W - pad * 2 - UI_RIGHT_W
    y0  = info_area_y + pad
    y1  = H - pad - UI_FOOT_H

    if y1 - y0 < 80: return  # not enough space

    gw  = ex - sx
    gap = pad
    col_w = (gw - 2 * gap) // 3

    col_pads = [
        (sx,                     sx + col_w),
        (sx + col_w + gap,       sx + col_w * 2 + gap),
        (sx + (col_w + gap) * 2, ex),
    ]

    # ── 1. OBJECT DETECTIONS (LIVE) ──────────────────────────────────────────
    ox0, ox1 = col_pads[0]
    _panel(img, ox0, y0, ox1, y1, a=0.82)
    _text(img, "OBJECT DETECTIONS (LIVE)", ox0 + 18, y0 + 28, 0.42, C_GOLD, bold=True)

    obj_counts = Counter()
    total_det = 0
    for cs in cameras:
        with cs.frame_lock:
            for d in cs.latest_dets:
                obj_counts[d["label"]] += 1
                total_det += 1

    oy = y0 + 50
    for label, cnt in sorted(obj_counts.items(), key=lambda x: -x[1])[:7]:
        if oy > y1 - 22: break
        bpct = min(1.0, cnt / max(total_det, 1))
        # Colored indicator dot
        dot_c = C_GREEN if label == "person" else C_GOLD
        cv2.circle(img, (ox0 + 20, oy + 6), 4, dot_c, -1, cv2.LINE_AA)
        _text(img, label.upper(), ox0 + 34, oy + 10, 0.30, C_DIM)
        _text_r(img, str(cnt), ox0 + col_w - 90, oy + 10, 0.32, C_GOLD, bold=True)
        _draw_hbar(img, ox0 + col_w - 76, oy + 2, 54, 8, bpct * 100, dot_c)
        oy += 22

    # Animated gauge ring
    tc_cx = ox1 - 44; tc_cy = (y0 + y1) // 2; tc_r = 34
    # Background ring
    cv2.circle(img, (tc_cx, tc_cy), tc_r, (20, 18, 12), 2, cv2.LINE_AA)
    # Sweep
    sweep_angle = (time.time() * 80) % 360
    cv2.ellipse(img, (tc_cx, tc_cy), (tc_r, tc_r), int(sweep_angle), 0, 100, C_GOLD, 2, cv2.LINE_AA)
    cv2.ellipse(img, (tc_cx, tc_cy), (tc_r, tc_r), int(sweep_angle + 180), 0, 100, C_GOLD, 2, cv2.LINE_AA)
    # Inner circle
    _fill_rounded_rect(img, tc_cx - tc_r + 6, tc_cy - tc_r + 6,
                       tc_cx + tc_r - 6, tc_cy + tc_r - 6, tc_r - 8, C_BG)
    _text_c(img, str(total_det), tc_cx, tc_cy + 8, 0.58, C_GOLD, bold=True)
    _text_c(img, "TOTAL",        tc_cx, tc_cy + 24, 0.24, C_DIM)

    # ── 2. RECENT ALERTS ──────────────────────────────────────────────────────
    ax0, ax1 = col_pads[1]
    _panel(img, ax0, y0, ax1, y1, a=0.82)
    _text(img, "RECENT ALERTS", ax0 + 18, y0 + 28, 0.42, C_GOLD, bold=True)
    _text_r(img, "View all alerts", ax1 - 12, y0 + 28, 0.24, C_DIM)

    with _event_ring_lock:
        alert_items = [(l, e, t) for l, e, t in list(_event_ring)]

    ay = y0 + 52
    for log_str, ev, ts in reversed(alert_items[-8:]):
        if ay > y1 - 20: break
        ts_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
        if "INTRUDER" in ev:     col = C_RED;    cat = "INTRUDER"
        elif "OBJ_ADDED" in ev:  col = C_GOLD;   cat = "OBJECT ADDED"
        elif "OBJ_REM" in ev:    col = C_ORANGE; cat = "OBJECT REMOVED"
        elif "LEFT" in ev:       col = C_CYAN;   cat = "PERSON LEFT"
        elif "ZONE" in ev:       col = C_RED;    cat = "ZONE BREACH"
        elif "ENTERED" in ev:    col = C_GREEN;  cat = "PERSON DETECTED"
        elif "RETURN" in ev:     col = C_GREEN;  cat = "PERSON DETECTED"
        elif "BEHAVIOR" in ev:   col = C_ORANGE; cat = "BEHAVIOR"
        else:                    col = C_DIM;    cat = ev[:10].upper()

        # Status indicator circle
        cv2.circle(img, (ax0 + 14, ay + 6), 4, col, -1, cv2.LINE_AA)
        _text(img, ts_str,        ax0 + 26, ay + 10, 0.26, C_DIM)
        _text(img, cat,           ax0 + 88, ay + 10, 0.28, col, bold=True)
        ay += 20

    # ── 3. SYSTEM DIAGNOSTIC LOGS ─────────────────────────────────────────────
    lx0, lx1 = col_pads[2]
    _panel(img, lx0, y0, lx1, y1, a=0.82)
    _text(img, "SYSTEM DIAGNOSTIC LOGS", lx0 + 18, y0 + 28, 0.42, C_GOLD, bold=True)
    _text_r(img, "View full logs", lx1 - 12, y0 + 28, 0.24, C_DIM)

    with _event_ring_lock:
        log_items = list(_event_ring)[-12:]

    ly = y0 + 52
    for log_str, ev, ts in reversed(log_items):
        if ly > y1 - 20: break
        ts_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
        if "INTRUDER" in ev or "ZONE" in ev:
            sev = "WARN"; sc = C_ORANGE
        elif "OBJ" in ev:
            sev = "INFO"; sc = C_GOLD
        elif "ENTERED" in ev or "RETURN" in ev:
            sev = "INFO"; sc = C_GREEN
        elif "LEFT" in ev:
            sev = "INFO"; sc = C_CYAN
        else:
            sev = "LOGB"; sc = C_DIM

        _text(img, ts_str, lx0 + 14, ly + 10, 0.24, C_DIM)
        # Small badge
        bx1_b = lx0 + 74; bx2_b = lx0 + 106
        _fill_rounded_rect(img, bx1_b, ly + 1, bx2_b, ly + 14, 3, tuple(max(0, c//6) for c in sc))
        _rounded_rect(img, bx1_b, ly + 1, bx2_b, ly + 14, 3, sc, 1)
        _text_c(img, sev, (bx1_b + bx2_b) // 2, ly + 11, 0.22, sc, bold=True)
        _text(img, log_str[:24].upper(), lx0 + 112, ly + 10, 0.26, C_DIM)
        ly += 18

# ── BOTTOM STATUS TICKER — Premium Scrolling Intelligence Feed ────────────────
def draw_footer_capsule(img: np.ndarray, cameras):
    W = img.shape[1]; H = img.shape[0]
    fy = H - UI_FOOT_H

    # Glass footer panel
    _panel(img, 0, fy, W, H, a=0.92)
    # Gold separator line at top of footer
    gold_sep = tuple(int(c * 0.5) for c in C_GOLD)
    cv2.line(img, (0, fy), (W, fy), gold_sep, 1, cv2.LINE_AA)

    _ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ticker = (
        f"  |  AUTONOMOUS AI EXECUTIVE ASSISTANT SYSTEM ONLINE  |  24/7 OPERATION  |  "
        f"CORE SYSTEM INTEGRITY SECURE  |  OPERATOR: {Config.USERNAME.upper()}  |  "
        f"HW PROFILE: {HW_PROFILE}  |  CUDA: {'ENABLED' if CUDA_AVAILABLE else 'DISABLED'}  |  "
        f"LIVE CHANNELS: {sum(1 for c in cameras if c.online)}/{len(cameras)}  |  {_ts}  |  "
    )
    # Smooth pixel-level scrolling
    char_px = 8
    total_px = len(ticker) * char_px
    t_offset = int(time.time() * 55) % max(1, total_px)
    gc = tuple(int(c * 0.85) for c in C_GOLD)
    _text(img, ticker, -t_offset + 10, fy + 20, 0.28, gc)
    if W - t_offset + total_px < W + 50:
        _text(img, ticker, W - t_offset + total_px + 20, fy + 20, 0.28, gc)

def draw_url_input_overlay(img: np.ndarray, cam_idx: int, url_so_far: str):
    W = img.shape[1]; H = img.shape[0]
    overlay = img.copy()
    cv2.rectangle(overlay,(0,0),(W,H),(0,0,0),-1)
    cv2.addWeighted(overlay,0.72,img,0.28,0,img)
    
    bw,bh = min(600,W*3//4), 220
    bx1=(W-bw)//2; by1=(H-bh)//2; bx2=bx1+bw; by2=by1+bh
    _panel(img,bx1,by1,bx2,by2,a=0.94)
    _neon_rect(img,bx1,by1,bx2,by2,C_GOLD,2)
    _corner_brackets(img,bx1,by1,bx2,by2,C_GOLD,L=18,T=2)
    
    if cam_idx == -2:
        title = "ADD NEW CAMERA CHANNEL"
    else:
        title = f"CONFIGURE CAMERA {cam_idx+1}"
    _text_c(img,title,bx1+bw//2,by1+28,0.52,C_GOLD,bold=True)
    cv2.line(img,(bx1+10,by1+36),(bx2-10,by1+36),C_BORDER,1)
    
    if cam_idx == -2:
        prompt = "ENTER NEW CAMERA SOURCE (0 OR RTSP/HTTP URL):"
    else:
        prompt = "ENTER SOURCE URL or 'name:New Name' TO RENAME:"
    _text(img,prompt,bx1+16,by1+58,0.30,C_TEXT,bold=True)
    _text(img,"Android: http://192.168.x.x:8080/video",bx1+16,by1+76,0.26,C_DIM)
    _text(img,"CCTV:    rtsp://user:pass@IP:554/stream", bx1+16,by1+92,0.26,C_DIM)
    
    ibx1=bx1+16; iby1=by1+116; ibx2=bx2-16; iby2=iby1+28
    _fill_rect(img,ibx1,iby1,ibx2,iby2,(5,5,5))
    _neon_rect(img,ibx1,iby1,ibx2,iby2,C_GOLD,1)
    
    blink=int(time.time()*2)%2; cursor="|" if blink else ""
    _text(img,f"  {url_so_far}{cursor}",ibx1+6,iby1+20,0.40,C_GOLD,bold=True)
    _text_c(img,"[Enter] CONFIRM   [Esc] CANCEL",bx1+bw//2,by2-12,0.28,C_DIM)



# ══════════════════════════════════════════════════════════════════════════════
# CINEMATIC BOOT SEQUENCE
# ══════════════════════════════════════════════════════════════════════════════
def run_startup_sequence(win_name: str):
    W, H = Config.WINDOW_W, Config.WINDOW_H
    canvas = np.zeros((H,W,3),dtype=np.uint8)
    boot_lines = [
        (0.0, "OMS // OBJECT MONITORING SYSTEM v9.0"),
        (0.3, f"HARDWARE PROFILE: [{HW_PROFILE}]"),
        (0.6, f"NEURAL GPU: {CUDA_DEVICE}"),
        (0.9, f"YOLO ENGINE: {'ONLINE' if YOLO_AVAILABLE else 'OFFLINE'}"),
        (1.2, f"FACE RECOGNITION: {'dlib ONLINE' if FACE_RECOG_AVAILABLE else ('YuNet/SFace ONLINE' if YUNET_AVAILABLE else 'OFFLINE')}"),
        (1.5, "PERIMETER SECURITY ENGINE: ONLINE"),
        (1.8, "BEHAVIOR ANOMALY ENGINE: ONLINE"),
        (2.1, "OBJECT OWNERSHIP ENGINE: ONLINE"),
        (2.4, f"SQLITE DATABASE: {Config.SQLITE_DB.name}"),
        (2.7, "THREAT INTELLIGENCE ENGINE: ARMED"),
        (3.0, "LOADING TELEGRAM DISPATCHER..."),
        (3.3, "ALL SYSTEMS NOMINAL. SENTINEL NETWORK ACTIVE."),
    ]
    # Gold matrix rain
    rain_chars = list("0123456789ABCDEF"); rain_cols = [random.randint(0,W//10) for _ in range(55)]
    rain_rows  = [random.randint(0,H//16) for _ in range(55)]
    start = time.time(); total_dur = 4.2
    while True:
        elapsed = time.time()-start
        if elapsed > total_dur: break
        canvas.fill(0)
        for i in range(55):
            rain_rows[i] = (rain_rows[i]+1)%(H//16)
            gv = random.randint(10,80)
            # Gold/amber matrix rain
            cv2.putText(canvas,random.choice(rain_chars),
                        (rain_cols[i]*10,rain_rows[i]*16+14),
                        cv2.FONT_HERSHEY_SIMPLEX,0.42,(0,gv,gv*2),1,cv2.LINE_AA)
        overlay = canvas.copy()
        cv2.rectangle(overlay,(0,0),(W,H),(0,0,0),-1)
        cv2.addWeighted(overlay,0.65,canvas,0.35,0,canvas)
        # Main boot panel
        bx1,by1,bx2,by2 = W//4,H//5,3*W//4,4*H//5
        cv2.rectangle(canvas,(bx1,by1),(bx2,by2),(10,8,8),-1)
        _neon_rect(canvas,bx1,by1,bx2,by2,C_GOLD,2)
        _corner_brackets(canvas,bx1,by1,bx2,by2,C_GOLD,L=20,T=2)
        cv2.putText(canvas,"OMS  //  NEURAL BOOT SEQUENCE",(bx1+20,by1+32),
                    cv2.FONT_HERSHEY_SIMPLEX,0.62,C_GOLD,2,cv2.LINE_AA)
        cv2.line(canvas,(bx1+10,by1+42),(bx2-10,by1+42),C_BORDER,1)
        ly = by1+62
        for delay,line in boot_lines:
            if elapsed >= delay:
                alpha = min(1.0,(elapsed-delay)*4)
                col   = tuple(int(c*alpha) for c in (C_GOLD if line==boot_lines[-1][1] else C_GREEN))
                cv2.putText(canvas,f">> {line}",(bx1+20,ly),cv2.FONT_HERSHEY_SIMPLEX,0.37,col,1,cv2.LINE_AA)
            ly += 22
        prog     = min(1.0,elapsed/total_dur)
        bar_x1   = bx1+20; bar_x2 = bx2-20; bar_y = by2-32
        bar_fill = int((bar_x2-bar_x1)*prog)
        cv2.rectangle(canvas,(bar_x1,bar_y),(bar_x2,bar_y+12),(30,28,8),-1)
        cv2.rectangle(canvas,(bar_x1,bar_y),(bar_x1+bar_fill,bar_y+12),C_GOLD,-1)
        cv2.rectangle(canvas,(bar_x1,bar_y),(bar_x2,bar_y+12),C_GOLD,1)
        cv2.putText(canvas,f"{int(prog*100)}%",(bar_x1,bar_y-5),cv2.FONT_HERSHEY_SIMPLEX,0.32,C_DIM,1,cv2.LINE_AA)
        # Radar top-right
        rc_x,rc_y,rc_r = W-100,90,65
        cv2.circle(canvas,(rc_x,rc_y),rc_r,(0,40,60),1)
        cv2.circle(canvas,(rc_x,rc_y),rc_r//2,(0,30,45),1)
        angle = (elapsed*200)%360; rad = math.radians(angle)
        ex = int(rc_x+rc_r*math.cos(rad)); ey = int(rc_y+rc_r*math.sin(rad))
        cv2.line(canvas,(rc_x,rc_y),(ex,ey),C_GOLD,2,cv2.LINE_AA)
        for tr in range(1,10):
            a2  = math.radians(angle-tr*10)
            ex2 = int(rc_x+rc_r*math.cos(a2)); ey2 = int(rc_y+rc_r*math.sin(a2))
            gfade = max(0, int((0,215,255)[2]-tr*25))
            cv2.line(canvas,(rc_x,rc_y),(ex2,ey2),(0,gfade//3,gfade),1)
        cv2.imshow(win_name,canvas)
        if cv2.waitKey(16) & 0xFF == ord('q'): break

# ══════════════════════════════════════════════════════════════════════════════
# MOUSE CALLBACK
# ══════════════════════════════════════════════════════════════════════════════
_active_cameras = []

def on_mouse(event, x, y, flags, param):
    global selected_cam_idx
    if event != cv2.EVENT_LBUTTONDOWN:
        return
    if Config.focused_cam_idx >= 0:
        return  # in focus mode, ignore tile clicks
    for idx, cs in enumerate(_active_cameras):
        if hasattr(cs, "tile_rect"):
            tx1, ty1, tx2, ty2 = cs.tile_rect
            if tx1 <= x <= tx2 and ty1 <= y <= ty2:
                selected_cam_idx = idx
                break

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    global UI_LEFT_W, UI_RIGHT_W, UI_HDR_H, UI_NAV_H, UI_FOOT_H, hud_overlay_active, cam_area_pct

    _init_db()
    _init_yunet()
    preload_known()

    app_log.info("OMS Object Monitoring System v9.0 starting...")
    log_event("SYSTEM_START", detail=f"HW:{HW_PROFILE} CUDA:{CUDA_AVAILABLE} YOLO:{YOLO_AVAILABLE}")
    speak("O M S Object Monitoring System online. Neural grid initializing.")

    global _active_cameras
    cameras: List[CameraState] = [CameraState(cam_id=i, cfg=cfg)
                                   for i, cfg in enumerate(Config.CAMERA_CONFIGS)]
    _active_cameras = cameras

    for cs in cameras:
        threading.Thread(target=camera_thread, args=(cs,),
                         daemon=True, name=f"Cam-{cs.cam_id}").start()

    threading.Thread(target=_diag_worker, args=(cameras,), daemon=True, name="Diag").start()

    # ── Start Web Dashboard (FastAPI) ──────────────────────────────────────────
    try:
        import web_integration as wi
        import web_server as ws
        wi.inject(cameras, threat_engine)
        ws.init_web_server(
            cameras,
            wi.get_telemetry,
            wi.get_events,
            wi.get_summary,
            wi.get_control_handlers(cameras, threat_engine),
        )
        ws.start_server(port=8000, open_browser=True)
        app_log.info("OMS Web Dashboard started on http://localhost:8000")
    except Exception as _web_err:
        app_log.warning(f"Web server not started: {_web_err}")

    win_name = "OMS — OBJECT MONITORING SYSTEM v9.0"
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(win_name, on_mouse)
    cv2.resizeWindow(win_name, Config.WINDOW_W, Config.WINDOW_H)

    run_startup_sequence(win_name)

    dashboard    = np.zeros((Config.WINDOW_H, Config.WINDOW_W, 3), dtype=np.uint8)
    last_db_save = time.time()
    last_gc_time = time.time()
    last_threat_tick = time.time()
    global selected_cam_idx, is_fs_state
    selected_cam_idx = 0
    is_fs_state = False
    input_mode   = False; input_cam = -1; input_buf = ""

    app_log.info("OMS dashboard live.")

    while True:
        loop_start = time.time()
        adaptive.update()

        if time.time()-last_threat_tick > 5.0:
            threat_engine.tick(); last_threat_tick = time.time()

        # Dynamically query window size to support true, seamless fullscreen scaling
        queried = False
        if WIN32_AVAILABLE:
            try:
                hwnd = win32gui.FindWindow(None, win_name)
                if hwnd:
                    rect_win = win32gui.GetClientRect(hwnd)
                    w_win = rect_win[2] - rect_win[0]
                    h_win = rect_win[3] - rect_win[1]
                    if w_win > 100 and h_win > 100:
                        Config.WINDOW_W, Config.WINDOW_H = w_win, h_win
                        queried = True
            except Exception:
                pass
        
        if not queried:
            try:
                rect = cv2.getWindowImageRect(win_name)
                if rect is not None and rect[2] > 100 and rect[3] > 100:
                    Config.WINDOW_W, Config.WINDOW_H = rect[2], rect[3]
            except Exception:
                pass

        # Reallocate canvas on size change
        if dashboard.shape[1] != Config.WINDOW_W or dashboard.shape[0] != Config.WINDOW_H:
            dashboard = np.zeros((Config.WINDOW_H, Config.WINDOW_W, 3), dtype=np.uint8)

        draw_gradient_background(dashboard)
        
        if not is_fs_state:
            draw_header(dashboard, cameras)
            draw_nav_tabs(dashboard)
            draw_side_panel(dashboard, cameras)
            draw_event_panel(dashboard)
            
        info_area_y = draw_camera_grid(dashboard, cameras)
        
        if not is_fs_state:
            if info_area_y is not None:
                draw_center_bottom(dashboard, cameras, info_area_y)
            draw_footer_capsule(dashboard, cameras)

        # Update system graphs every 2s
        if int(time.time()*2) % 4 == 0:
            _update_sys_graphs()

        if input_mode:
            draw_url_input_overlay(dashboard, input_cam, input_buf)

        cv2.imshow(win_name, dashboard)

        now = time.time()
        if now-last_db_save > Config.DB_SAVE_SECS:
            last_db_save = now
            threading.Thread(target=_save_db_json, daemon=True).start()
        if now-last_gc_time > Config.GC_GEN1_SECS:
            last_gc_time = now; gc.collect(1)

        key = cv2.waitKey(1) & 0xFF

        if input_mode:
            if key in (13,10):   # ENTER
                url = input_buf.strip()
                if url:
                    if input_cam == -2:
                        new_source = int(url) if url.isdigit() else url
                        new_id = len(cameras)
                        new_name = f"CCTV NODE-{new_id+1}"
                        new_cfg = {"source": new_source, "name": new_name, "enabled": True, "location": f"Sector {chr(65+new_id)}"}
                        new_cs = CameraState(cam_id=new_id, cfg=new_cfg)
                        cameras.append(new_cs)
                        threading.Thread(target=camera_thread, args=(new_cs,), daemon=True, name=f"Cam-{new_id}").start()
                        save_config_cameras(cameras)
                        speak(f"Camera {new_id+1} added.")
                        log_event("CAM_ADD", camera=new_name, detail=f"source={url}")
                    else:
                        cs = cameras[input_cam]
                        if url.lower().startswith("name:"):
                            new_name = url[5:].strip()
                            if new_name:
                                cs.name = new_name
                                save_config_cameras(cameras)
                                speak(f"Camera {input_cam+1} renamed to {new_name}.")
                                log_event("CAM_RENAME", camera=new_name, detail=f"cam_id={input_cam}")
                        else:
                            source = int(url) if url.isdigit() else url
                            threading.Thread(target=lambda c=cs,s=source: c.reconnect_to(s), daemon=True).start()
                            log_event("CAM_CONFIG", camera=cs.name, detail=f"source={url}")
                            speak(f"Connecting camera {input_cam+1}.")
                input_mode = False; input_buf = ""; input_cam = -1
            elif key == 27:      # ESC
                input_mode = False; input_buf = ""; input_cam = -1
            elif key in (8,127): # Backspace
                input_buf = input_buf[:-1]
            elif 32 <= key < 127:
                input_buf += chr(key)
            continue

        if key in (ord('f'), ord('F')):
            if Config.focused_cam_idx == selected_cam_idx:
                Config.focused_cam_idx = -1
                speak("Grid view.")
            else:
                Config.focused_cam_idx = selected_cam_idx
                speak(f"Focusing camera {selected_cam_idx+1}.")
        elif key in (ord('h'), ord('H')):
            hud_overlay_active = not hud_overlay_active
            speak("HUD diagnostics enabled." if hud_overlay_active else "HUD diagnostics disabled.")
        elif key == ord('['):
            UI_LEFT_W = max(50, UI_LEFT_W - 10)
            speak(f"Sidebar width {UI_LEFT_W} pixels.")
        elif key == ord(']'):
            UI_LEFT_W = min(400, UI_LEFT_W + 10)
            speak(f"Sidebar width {UI_LEFT_W} pixels.")
        elif key == ord('{'):
            UI_RIGHT_W = max(50, UI_RIGHT_W - 10)
            speak(f"Right panel width {UI_RIGHT_W} pixels.")
        elif key == ord('}'):
            UI_RIGHT_W = min(500, UI_RIGHT_W + 10)
            speak(f"Right panel width {UI_RIGHT_W} pixels.")
        elif key in (ord('='), ord('+')):
            cam_area_pct = min(0.85, cam_area_pct + 0.02)
            speak(f"Camera grid height {int(cam_area_pct*100)} percent.")
        elif key in (ord('-'), ord('_')):
            cam_area_pct = max(0.25, cam_area_pct - 0.02)
            speak(f"Camera grid height {int(cam_area_pct*100)} percent.")
        elif key == ord(','):
            UI_HDR_H = max(40, UI_HDR_H - 4)
            speak(f"Header height {UI_HDR_H} pixels.")
        elif key == ord('.'):
            UI_HDR_H = min(150, UI_HDR_H + 4)
            speak(f"Header height {UI_HDR_H} pixels.")
        elif key in (9, ord('s'), ord('S'), 81, 83):  # TAB, 'S' key, or Arrow keys for robust OS compatibility
            selected_cam_idx = (selected_cam_idx + 1) % len(cameras)
            speak(f"Camera {selected_cam_idx+1} selected.")
            if Config.focused_cam_idx >= 0:
                Config.focused_cam_idx = selected_cam_idx
        elif key in (ord('z'), ord('Z')):  # Dedicated 'Z' key to toggle true fullscreen mode
            is_fs_state = not is_fs_state
            if is_fs_state:
                cv2.setWindowProperty(win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                if Config.focused_cam_idx == -1:
                    Config.focused_cam_idx = selected_cam_idx
            else:
                cv2.setWindowProperty(win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
                Config.focused_cam_idx = -1
        elif key == ord('q'):
            app_log.info("Shutdown command.")
            speak("Initiating O S M shutdown.")
            log_event("SYSTEM_SHUTDOWN", detail="user command")
            break
        elif key == ord('c'):
            export_csv(); speak("Event log exported.")
        elif key == ord('l'):
            reset_log_files(cameras)
        elif key == ord('r'):
            register_user_face(cameras, username=Config.USERNAME)
        elif key == ord(' '):
            log_event("MANUAL_ALARM", detail="user triggered")
            threat_engine.raise_threat("RED","MANUAL ALARM")
            _alarm(); speak("Warning. Manual alarm activated.")
        elif key in (ord('a'), ord('A')):
            input_mode = True; input_cam = -2; input_buf = ""
            speak("Add new camera channel.")
        elif key in (ord('e'), ord('E')):
            input_mode = True; input_cam = selected_cam_idx; input_buf = ""
            speak(f"Configure camera {selected_cam_idx+1}.")
        elif key in (ord('i'), ord('I')):
            Config.DETECT_NEW_IDS = not Config.DETECT_NEW_IDS
            if Config.DETECT_NEW_IDS:
                speak("Intruder detection activated.")
            else:
                speak("Intruder detection suspended. Saved IDs only.")
        elif key == ord('p'):
            phone_idx = next((i for i,c in enumerate(cameras)
                              if "PHONE" in c.name.upper() or "IP" in c.name.upper()), len(cameras)-1)
            input_mode = True; input_cam = phone_idx; input_buf = ""
        elif ord('1') <= key <= ord('9'):
            cam_idx = key - ord('1')
            if cam_idx < len(cameras):
                input_mode = True; input_cam = cam_idx; input_buf = ""

        elapsed = time.time()-loop_start
        time.sleep(max(0.001, (adaptive.frame_ms/1000.0)-elapsed))

    for cs in cameras: cs.release()
    _save_db_json()
    if _db_conn: _db_conn.close()
    time.sleep(0.5)
    _lq.put(None)
    cv2.destroyAllWindows()
    app_log.info("OMS fully terminated.")

if __name__ == "__main__":
    main()