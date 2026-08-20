"""
OMS Edge — CPU-Optimized Object Detection & Tracking Pipeline
"""

from __future__ import annotations
import os
import time
import logging
from typing import List, Dict, Tuple, Any, Optional
import cv2
import numpy as np

log = logging.getLogger("OMS.Detector")

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except Exception as e:
    YOLO_AVAILABLE = False
    log.warning(f"[YOLO] ultralytics import error: {e}")

try:
    from identity_engine import StableIdentityEngine
    STABLE_ID_AVAILABLE = True
except Exception as e:
    STABLE_ID_AVAILABLE = False
    log.warning(f"[IDENTITY] identity_engine import error: {e}")


class DetectionPipeline:
    """
    High-performance CPU/GPU detection pipeline.
    Runs YOLO inference on key frames and maintains ByteTrack tracking state.
    """

    def __init__(self, model_path: str = "yolov8n.pt", device: str = "cpu", confidence: float = 0.35):
        self.model_path = model_path
        self.device = device
        self.confidence = confidence
        self.model = None

        if YOLO_AVAILABLE:
            try:
                self.model = YOLO(model_path)
                log.info(f"[YOLO] Loaded model {model_path} on {device}")
            except Exception as e:
                log.error(f"[YOLO] Failed to load model {model_path}: {e}")

    def detect_and_track(
        self,
        frame: np.ndarray,
        det_w: int = 480,
        det_h: int = 288,
        detect_people: bool = True,
        detect_objects: bool = True
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """
        Executes YOLO tracking on frame resized to (det_w, det_h) for low CPU overhead.
        Returns: (detections_list, persons_count, objects_count)
        """
        if self.model is None or frame is None:
            return [], 0, 0

        orig_h, orig_w = frame.shape[:2]

        # Target class filters (COCO classes: 0 = person, 2 = car, 3 = motorcycle, 5 = bus, 7 = truck, 24 = backpack, 26 = handbag, 28 = suitcase)
        target_classes = []
        if detect_people:
            target_classes.append(0)
        if detect_objects:
            target_classes.extend([24, 26, 28, 56, 67])  # backpacks, bags, bottles, phones

        try:
            results = self.model.track(
                source=frame,
                imgsz=(det_h, det_w),
                conf=self.confidence,
                classes=target_classes if target_classes else None,
                device=self.device,
                persist=True,
                verbose=False
            )

            detections: List[Dict[str, Any]] = []
            persons = 0
            objects = 0

            if results and len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes
                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    xyxy = box.xyxy[0].cpu().numpy().tolist()
                    track_id = int(box.id[0].item()) if box.id is not None else None

                    label = "person" if cls_id == 0 else results[0].names.get(cls_id, "object")

                    if cls_id == 0:
                        persons += 1
                    else:
                        objects += 1

                    detections.append({
                        "track_id": track_id,
                        "label": label,
                        "class_id": cls_id,
                        "confidence": round(conf, 3),
                        "box": [int(x) for x in xyxy]
                    })

            return detections, persons, objects

        except Exception as e:
            log.debug(f"[DETECTION] Inference error: {e}")
            return [], 0, 0
