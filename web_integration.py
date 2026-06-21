"""
OMS Web Integration Module
Provides data extraction functions that read main.py's runtime state
and expose it via the web_server FastAPI endpoints.
"""
from __future__ import annotations
import time
import threading
from datetime import datetime
from typing import List

def _get_sv():
    import sys
    main_mod = sys.modules.get('__main__')
    if main_mod and hasattr(main_mod, 'faces_db'):
        return main_mod
    try:
        import main as sv
        return sv
    except Exception:
        return None

# ─── psutil for system metrics ────────────────────────────────────────────────
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# ─── State that gets injected by main.py main() ──────────────────────
_cameras = []
_events_db = []
_events_lock = threading.Lock()
_threat_engine = None
_start_time = time.time()
_net_bytes_prev = 0
_net_bytes_time = time.time()


def inject(cameras, threat_engine):
    """Called by main.py main() to inject camera list and threat engine."""
    global _cameras, _threat_engine
    _cameras = cameras
    _threat_engine = threat_engine


def record_event(ts: str, event: str, camera: str = "", person: str = "", detail: str = ""):
    """Called by main.py log_event() to capture events for the web dashboard."""
    with _events_lock:
        _events_db.append({
            "ts": ts, "event": event, "camera": camera,
            "person": person, "detail": detail,
        })
        if len(_events_db) > 500:
            _events_db.pop(0)

def clear_events():
    """Clear memory events cache."""
    with _events_lock:
        _events_db.clear()

def rename_camera_in_events(old_name: str, new_name: str):
    """Rename camera name in in-memory event cache."""
    with _events_lock:
        for ev in _events_db:
            if ev.get("camera") == old_name:
                ev["camera"] = new_name
            if ev.get("detail") and f"cam={old_name}" in ev["detail"]:
                ev["detail"] = ev["detail"].replace(f"cam={old_name}", f"cam={new_name}")
            elif ev.get("detail") and f"camera={old_name}" in ev["detail"]:
                ev["detail"] = ev["detail"].replace(f"camera={old_name}", f"camera={new_name}")


def _get_net_kb() -> float:
    global _net_bytes_prev, _net_bytes_time
    if not PSUTIL_AVAILABLE:
        return 0.0
    try:
        ctr = psutil.net_io_counters()
        now = time.time()
        dt = max(now - _net_bytes_time, 0.1)
        total = ctr.bytes_sent + ctr.bytes_recv
        kb = (total - _net_bytes_prev) / 1024.0 / dt
        _net_bytes_prev = total
        _net_bytes_time = now
        return round(kb, 1)
    except Exception:
        return 0.0


def get_telemetry() -> dict:
    """Returns a dict of system + AI telemetry for /api/telemetry."""
    # Import these at call-time to get the runtime values
    try:
        sv = _get_sv()
        CUDA_AVAILABLE = sv.CUDA_AVAILABLE if sv else False
        CUDA_DEVICE    = sv.CUDA_DEVICE if sv else "CPU"
        YOLO_AVAILABLE = sv.YOLO_AVAILABLE if sv else False
        FACE_RECOG_AVAILABLE = sv.FACE_RECOG_AVAILABLE if sv else False
        HW_PROFILE = sv.HW_PROFILE if sv else "LOW"
    except Exception:
        CUDA_AVAILABLE = False
        CUDA_DEVICE = "CPU"
        YOLO_AVAILABLE = False
        FACE_RECOG_AVAILABLE = False
        HW_PROFILE = "LOW"

    cpu = 0; ram = 0; disk = 0; gpu_pct = 0; gpu_name = CUDA_DEVICE

    if PSUTIL_AVAILABLE:
        try:
            cpu  = round(psutil.cpu_percent(interval=None), 1)
            vm   = psutil.virtual_memory()
            ram  = round(vm.percent, 1)
            di   = psutil.disk_usage(".")
            disk = round(di.percent, 1)
        except Exception:
            pass

    # GPU utilization via pynvml if available
    if CUDA_AVAILABLE:
        try:
            import pynvml
            pynvml.nvmlInit()
            h = pynvml.nvmlDeviceGetHandleByIndex(0)
            gpu_pct = pynvml.nvmlDeviceGetUtilizationRates(h).gpu
            gpu_name_raw = pynvml.nvmlDeviceGetName(h)
            if isinstance(gpu_name_raw, bytes):
                gpu_name = gpu_name_raw.decode()
            else:
                gpu_name = gpu_name_raw
        except Exception:
            pass

    # Check Telegram queue
    tg_ok = False
    try:
        sv = _get_sv()
        tg_ok = sv is not None and hasattr(sv, "notif_queue") and sv.notif_queue is not None
    except Exception:
        pass

    # Check DB connection
    db_ok = False
    try:
        sv = _get_sv()
        db_ok = sv is not None and sv._db_conn is not None
    except Exception:
        pass

    fps_all = []
    for c in _cameras:
        try:
            fps_all.append(round(c.fps_inst, 1))
        except Exception:
            fps_all.append(0.0)

    threat = "GREEN"
    if _threat_engine:
        try:
            threat = _threat_engine.level
        except Exception:
            pass

    # Get detect_new_ids state
    detect_new_ids = True
    try:
        sv2 = _get_sv()
        detect_new_ids = getattr(sv2.Config, "DETECT_NEW_IDS", True) if sv2 else True
    except Exception:
        pass

    return {
        "cpu": cpu, "ram": ram, "disk": disk,
        "net_kb": _get_net_kb(),
        "gpu": gpu_pct, "gpu_name": gpu_name,
        "cuda": CUDA_AVAILABLE,
        "hw_profile": HW_PROFILE,
        "yolo": YOLO_AVAILABLE,
        "face_recog": FACE_RECOG_AVAILABLE,
        "db": db_ok,
        "telegram": tg_ok,
        "threat_level": threat,
        "fps_all": fps_all,
        "uptime_secs": round(time.time() - _start_time),
        "detect_new_ids": detect_new_ids,
    }


def get_events() -> list:
    """Returns recent event list for /api/events."""
    with _events_lock:
        return list(_events_db)


def get_summary() -> dict:
    """Returns aggregated stats for /api/summary."""
    try:
        sv = _get_sv()
        operator = sv.Config.USERNAME if sv else "Prajan"
    except Exception:
        operator = "Prajan"

    total_det = 0
    persons   = 0
    for c in _cameras:
        try:
            total_det += len(c.latest_dets)
            persons   += len(c.present_pids)
        except Exception:
            pass

    added = 0; removed = 0; alerts = 0; known_p = 0; unknown_p = 0
    with _events_lock:
        for ev in _events_db:
            e = ev["event"]
            if e == "OBJ_ADDED":                              added   += 1
            elif e == "OBJ_REMOVED":                          removed += 1
            elif e in ("INTRUDER","ZONE_INTRUSION","BEHAVIOR","MANUAL_ALARM"): alerts  += 1
            elif e in ("PERSON_ENTERED","PERSON_RETURNED"):   known_p += 1

    elapsed = time.time() - _start_time
    h, rem  = divmod(int(elapsed), 3600)
    m, s    = divmod(rem, 60)

    return {
        "total_detections": total_det,
        "known_persons": known_p,
        "unknown_persons": unknown_p,
        "objects_added": added,
        "objects_removed": removed,
        "alerts": alerts,
        "operator": operator,
        "uptime": f"{h:02d}:{m:02d}:{s:02d}",
    }


def get_control_handlers(cameras, threat_engine) -> dict:
    """Returns a dict of control action -> callable for /api/control/<action>."""

    def do_alarm():
        try:
            sv = _get_sv()
            if sv:
                sv.log_event("MANUAL_ALARM", detail="web triggered")
            threat_engine.raise_threat("RED", "MANUAL ALARM")
            if sv:
                sv._alarm()
                sv.speak("Warning. Manual alarm activated.")
        except Exception as e:
            return f"Error: {e}"
        return "Alarm activated"

    def do_shutdown():
        try:
            sv = _get_sv()
            if sv:
                sv.speak("System shutdown initiated.")
                sv.log_event("SYSTEM_SHUTDOWN", detail="web command")
        except Exception as e:
            return f"Error: {e}"
        return "Shutdown initiated"

    def do_export_csv():
        try:
            sv = _get_sv()
            if sv:
                sv.export_csv()
                sv.speak("Event log exported.")
        except Exception as e:
            return f"Error: {e}"
        return "CSV exported"

    def do_register_face():
        try:
            sv = _get_sv()
            if sv:
                threading.Thread(
                    target=lambda: sv.register_user_face(cameras, sv.Config.USERNAME),
                    daemon=True
                ).start()
        except Exception as e:
            return f"Error: {e}"
        return "Face registration started"

    def do_test_telegram():
        try:
            sv = _get_sv()
            if sv:
                sv.notif_queue.send_message(
                    "🔔 OMS Web Dashboard — Test message. System operational.",
                    event_type="SYSTEM"
                )
        except Exception as e:
            return f"Error: {e}"
        return "Telegram test sent"

    def do_toggle_hud():
        try:
            sv = _get_sv()
            if sv:
                sv.hud_overlay_active = not sv.hud_overlay_active
                state = sv.hud_overlay_active
            else:
                state = False
        except Exception as e:
            return f"Error: {e}"
        return f"HUD {'enabled' if state else 'disabled'}"

    def do_refresh():
        return "Data refreshed"

    def do_reset_logs():
        try:
            sv = _get_sv()
            if sv:
                sv.reset_log_files(_cameras)
        except Exception as e:
            return f"Error: {e}"
        return "Logs cleared successfully"

    def do_toggle_auto_register():
        """Toggle Config.DETECT_NEW_IDS and persist to config.yaml."""
        try:
            sv = _get_sv()
            if not sv:
                return "Error: Main module not running"
            sv.Config.DETECT_NEW_IDS = not sv.Config.DETECT_NEW_IDS
            state = sv.Config.DETECT_NEW_IDS
            state_str = "ON — new faces will be auto-registered" if state else "OFF — known faces only"
            try:
                sv.speak(f"Auto register faces {state_str}.")
            except Exception:
                pass
            try:
                sv.app_log.info(f"[WEB] Auto Register Faces toggled via web: {state}")
            except Exception:
                pass
            # Persist to config.yaml
            try:
                import web_server as ws
                ws._save_config_yaml_and_env(
                    sv.Config.USERNAME,
                    sv.Config.CONFIDENCE,
                    sv.Config.MODEL_NAME,
                    sv.Config.BOT_TOKEN,
                    sv.Config.CHAT_ID,
                    state,
                )
            except Exception:
                pass
            return f"Auto Register Faces {'ON' if state else 'OFF'}"
        except Exception as e:
            return f"Error: {e}"

    return {
        "alarm":                do_alarm,
        "shutdown":             do_shutdown,
        "export_csv":           do_export_csv,
        "register_face":        do_register_face,
        "test_telegram":        do_test_telegram,
        "toggle_hud":           do_toggle_hud,
        "refresh":              do_refresh,
        "reset_logs":           do_reset_logs,
        "toggle_auto_register": do_toggle_auto_register,
    }
