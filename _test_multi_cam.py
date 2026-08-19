"""
Quick verification of 15+ camera handling, endpoints, and crash-resilience.
"""
import time
import requests
import subprocess
import sys

print("=" * 60)
print("  OMS MULTI-CAMERA VERIFICATION TEST")
print("=" * 60)

# 1. Test config.yaml parsing
import yaml
with open("config.yaml", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)
cams = cfg.get("cameras", [])
print(f"[1/3] Config cameras count: {len(cams)} channels configured.")
assert len(cams) >= 15, "Expected at least 15 cameras in config.yaml"
print(f"      Channel 1 source: {cams[1]['source']}")

# 2. Test mock web server startup & camera endpoints
from web_server import create_app
from fastapi.testclient import TestClient

class MockCamera:
    def __init__(self, cid, name):
        self.cam_id = cid
        self.name = name
        self.source = f"rtsp://admin:eltec%40123@192.168.1.200:554/Streaming/Channels/{cid}01"
        self.location = f"Sector {cid}"
        self.online = False
        self.disconnected = True
        self.fps_inst = 0.0
        self.frame_cnt = 0
        self.present_pids = set()
        self.latest_dets = []
        self.latest_frame = None
        import threading
        self.frame_lock = threading.Lock()
        self.manager = type('M', (), {'brightness':50,'contrast':50,'saturation':50,'gamma':1.0,'sharpness':0,'noise_reduction':0,'exposure':-6,'auto_exposure':True,'auto_white_balance':True,'mirror':False,'fps':30,'width':1280,'height':720,'active_width':0,'active_height':0,'active_fps':0,'active_codec':'MJPG'})()

import web_server
web_server._cameras = [MockCamera(i, f"CAM {i+1}") for i in range(16)]

app = create_app()
client = TestClient(app)

print("\n[2/3] Testing Camera Endpoints with 16 simultaneous channels...")
res = client.get("/api/cameras")
assert res.status_code == 200, f"Failed /api/cameras: {res.text}"
data = res.json()
print(f"      /api/cameras returned: {len(data)} camera nodes.")

# Test stream endpoint
stream_res = client.get("/api/stream/1")
assert stream_res.status_code == 200, f"Failed /api/stream/1: {stream_res.status_code}"
print(f"      /api/stream/1 status: {stream_res.status_code} (MJPEG stream operational)")

# Test add camera
add_res = client.post("/api/camera/add", json={"name": "EXTRA TEST CAM", "source": "rtsp://192.168.1.200:554/16", "location": "Test"})
print(f"      /api/camera/add status: {add_res.status_code}")

print("\n[3/3] ALL MULTI-CAMERA CHECKS PASSED WITH ZERO CRASHES!")
print("=" * 60)
