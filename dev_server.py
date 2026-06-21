#!/usr/bin/env python3
"""
OMS Dashboard Dev Server Launcher
Starts just the FastAPI web server with mock data for frontend development.
Usage: python dev_server.py
Then open http://localhost:3000 (Next.js dev) or http://localhost:8000 (FastAPI directly)
"""
import time, threading, random, math
from datetime import datetime

# ─── Mock camera state ────────────────────────────────────────────────────────
class MockCamera:
    def __init__(self, cam_id, name, location, online=True):
        self.cam_id       = cam_id
        self.name         = name
        self.location     = location
        self.online       = online
        self.disconnected = not online
        self.fps_inst     = random.uniform(24, 30)
        self.present_pids = set()
        self.latest_dets  = []
        self.latest_frame = None
        self.frame_lock   = threading.Lock()
        self.uptime_str   = "00:15:32"
        self.threat_level = "GREEN"
        
        # Initialize mock HAAE engine
        from haae_engine import HumanActivityExpressionEngine
        self.haae = HumanActivityExpressionEngine()
        if online and cam_id == 0:
            self.latest_dets = [{"label": "person", "pid": "P1"}]
            rec = self.haae.get("P1")
            rec.emotion = "Happy"
            rec.emotion_score = 0.92
            rec.activity_score = 0.65
            rec.activity_label = "ACTIVE"
            rec.attention_level = "HIGH"

cameras = [
    MockCamera(0, "LOCAL CAM",      "Main Entrance Sector", True),
    MockCamera(1, "CCTV NODE-2",    "Office Sector B",        False),
    MockCamera(2, "CCTV NODE-3",    "Restricted Storage",   False),
    MockCamera(3, "PHONE / IP CAM", "Mobile Sector D",      False),
]

class MockThreatEngine:
    level = "GREEN"
    def tick(self): pass
    def raise_threat(self, level, reason): self.level = level

threat_engine = MockThreatEngine()

# ─── Import and start web server ──────────────────────────────────────────────
import web_integration as wi
import web_server as ws

wi.inject(cameras, threat_engine)
ws.init_web_server(cameras, wi.get_telemetry, wi.get_events, wi.get_summary,
                   wi.get_control_handlers(cameras, threat_engine))

# Seed some mock events
for ev, cam, detail in [
    ("SYSTEM_START",    "LOCAL CAM",   "Dev server started"),
    ("PERSON_ENTERED",  "LOCAL CAM",   "visits=1 conf=0.92"),
    ("OBJ_ADDED",       "CCTV NODE-2", "0 -> 1"),
    ("PERSON_LEFT",     "LOCAL CAM",   "Last seen 09:30:00"),
    ("BASELINE",        "LOCAL CAM",   "Baseline saved"),
]:
    wi.record_event(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ev, cam, "Prajan", detail)

print("\n[OMS DEV] Starting web server at http://localhost:8000")
print("[OMS DEV] API docs at http://localhost:8000/docs")
print("[OMS DEV] Press Ctrl+C to stop\n")

ws.start_server(port=8000, open_browser=True)

# Keep running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[OMS DEV] Stopped.")
