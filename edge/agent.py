"""
OMS Edge Agent — Master Autonomous Surveillance Orchestrator
Runs 24/7 on normal CPU machines with zero cloud GPU requirement.
"""

from __future__ import annotations
import os
import sys
import time
import signal
import logging
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Load .env file
def _load_env():
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

_load_env()

# Load YAML configuration
try:
    import yaml
    with open(ROOT_DIR / "config.yaml", "r", encoding="utf-8") as f:
        CONFIG = yaml.safe_load(f) or {}
except Exception:
    CONFIG = {}

from edge.health.monitor import AdaptiveController, get_system_telemetry, detect_hardware_profile
from edge.camera.reconnect import CameraWorker
from edge.detection.pipeline import DetectionPipeline
from edge.events.queue import PersistentEventQueue
from edge.events.engine import EventEngine
from edge.transport.cloud_uploader import CloudUploader
from edge.analytics.activity import ActivityAnalytics
from edge.analytics.garbage import ObjectOwnershipAnalytics
from edge.recognition.face import OnDemandFaceEngine
from edge.storage.snapshots import create_event_snapshot

# Setup Structured Logging with Rotation
LOGS_DIR = ROOT_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / "oms-edge.log", encoding="utf-8")
    ]
)
log = logging.getLogger("OMS.EdgeAgent")


class EdgeAgent:
    """Master controller managing camera workers, AI processing, and cloud sync."""

    def __init__(self):
        self.running = False
        self.hw_profile = detect_hardware_profile()
        self.adaptive = AdaptiveController(hw_profile=self.hw_profile)
        self.queue = PersistentEventQueue(str(LOGS_DIR / "oms_event_queue.db"))
        self.event_engine = EventEngine(self.queue)
        
        # Load Analytics & Face engines
        self.activity_engine = ActivityAnalytics(loiter_secs=25.0)
        self.ownership_engine = ObjectOwnershipAnalytics(abandonment_secs=15.0)
        self.face_engine = OnDemandFaceEngine(
            yunet_path=str(ROOT_DIR / "models/face_detection_yunet_2023mar.onnx"),
            sface_path=str(ROOT_DIR / "models/face_recognition_sface_2021dec.onnx")
        )

        # Load YOLO model
        model_name = CONFIG.get("detection", {}).get("model", {}).get(self.hw_profile, "yolov8n.pt")
        if isinstance(model_name, dict):
            model_name = model_name.get(self.hw_profile, "yolov8n.pt")
        device = "cuda" if CONFIG.get("detection", {}).get("use_cuda", True) and self.hw_profile == "HIGH" else "cpu"
        self.detector = DetectionPipeline(model_path=str(ROOT_DIR / model_name), device=device)

        # Initialize Cameras from config.yaml
        self.cameras: List[CameraWorker] = []
        raw_cams = CONFIG.get("cameras", [
            {"id": 0, "source": 0, "name": "LOCAL WEBCAM", "location": "Control Desk"}
        ])
        for c in raw_cams:
            if c.get("enabled", True):
                worker = CameraWorker(
                    cam_id=c.get("id", len(self.cameras)),
                    source=c.get("source", 0),
                    name=c.get("name", f"CAM {len(self.cameras)}"),
                    location=c.get("location", "Monitored Sector")
                )
                self.cameras.append(worker)

        # Initialize Cloud Uploader
        self.uploader = CloudUploader(
            queue=self.queue,
            cloud_url=os.getenv("OMS_CLOUD_API_URL", "https://oms-sentinel-cloud.onrender.com"),
            edge_token=os.getenv("OMS_EDGE_TOKEN", ""),
            engine_id="edge-node-1"
        )
        self.uploader.bind_state_providers(
            get_telemetry_fn=self.get_telemetry,
            get_cameras_fn=lambda: self.cameras
        )

    def get_telemetry(self) -> Dict[str, Any]:
        t = get_system_telemetry()
        t["hw_profile"] = self.hw_profile
        t["cameras_count"] = len(self.cameras)
        t["cameras_online"] = sum(1 for c in self.cameras if c.online)
        return t

    def start(self):
        """Starts all cameras, AI workers, and local/cloud services."""
        self.running = True
        log.info("=" * 70)
        log.info("  OMS EDGE SURVEILLANCE AGENT — STARTING INITIALIZATION")
        log.info(f"  [✦] Hardware Profile: {self.hw_profile}")
        log.info(f"  [✦] Active Cameras  : {len(self.cameras)} Nodes Configured")
        log.info(f"  [✦] Cloud Target    : {self.uploader.cloud_url}")
        log.info("=" * 70)

        # 1. Start camera capture threads
        for cam in self.cameras:
            cam.start()

        # 2. Start Cloud Uploader
        self.uploader.start()

        # 3. Main processing loop
        frame_idx = 0
        try:
            while self.running:
                loop_start = time.time()
                cfg = self.adaptive.update()

                for cam in self.cameras:
                    ok, frame = cam.read_latest()
                    if not ok or frame is None:
                        continue

                    # Frame skipping based on adaptive CPU load
                    if frame_idx % cfg.process_every_n == 0:
                        detections, persons, objects = self.detector.detect_and_track(
                            frame,
                            det_w=cfg.det_w,
                            det_h=cfg.det_h,
                            detect_people=True,
                            detect_objects=True
                        )

                        cam.persons_count = persons
                        cam.objects_count = objects

                        persons_list = [d for d in detections if d.get("class_id") == 0]
                        objects_list = [d for d in detections if d.get("class_id") != 0]

                        # 1. Behavior & Activity Analysis
                        for p in persons_list:
                            tid = p.get("track_id")
                            bx = p.get("box", [0, 0, 0, 0])
                            if tid is not None:
                                anomalies = self.activity_engine.update_track(tid, tuple(bx))
                                for a in anomalies:
                                    snap = create_event_snapshot(frame, tuple(bx))
                                    self.event_engine.trigger_event(
                                        event_type=a["event_type"],
                                        camera_id=cam.name,
                                        severity=a["severity"],
                                        confidence=a["confidence"],
                                        track_ids=[tid],
                                        location=cam.location,
                                        snapshot_base64=snap,
                                        metadata={"detail": a["detail"]}
                                    )

                        # 2. Abandoned Object / Garbage Dumping Analysis
                        if objects_list:
                            obj_anomalies = self.ownership_engine.update(objects_list, persons_list)
                            for oa in obj_anomalies:
                                snap = create_event_snapshot(frame, tuple(oa.get("box", [0, 0, 0, 0])))
                                self.event_engine.trigger_event(
                                    event_type=oa["event_type"],
                                    camera_id=cam.name,
                                    severity=oa["severity"],
                                    confidence=oa["confidence"],
                                    track_ids=[oa.get("track_id", 0)],
                                    location=cam.location,
                                    snapshot_base64=snap,
                                    metadata={"detail": oa.get("detail", "")}
                                )

                        # 3. Person Presence Alert
                        if persons > 0:
                            snap = create_event_snapshot(frame, max_dim=480)
                            self.event_engine.trigger_event(
                                event_type="person_detected",
                                camera_id=cam.name,
                                severity="low" if persons == 1 else "medium",
                                confidence=0.88,
                                track_ids=[d.get("track_id", 0) for d in persons_list if d.get("track_id")],
                                location=cam.location,
                                snapshot_base64=snap,
                                metadata={"persons_count": persons, "objects_count": objects}
                            )

                frame_idx += 1
                elapsed = time.time() - loop_start
                target_frame_time = 1.0 / cfg.fps_target
                if elapsed < target_frame_time:
                    time.sleep(target_frame_time - elapsed)

        except KeyboardInterrupt:
            log.info("[EDGE AGENT] Stopping gracefully...")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        for cam in self.cameras:
            cam.stop()
        self.uploader.stop()
        log.info("[EDGE AGENT] Shutdown complete.")


def main():
    agent = EdgeAgent()
    signal.signal(signal.SIGINT, lambda s, f: agent.stop())
    signal.signal(signal.SIGTERM, lambda s, f: agent.stop())
    agent.start()


if __name__ == "__main__":
    main()
