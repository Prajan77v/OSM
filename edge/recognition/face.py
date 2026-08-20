"""
OMS Edge — CPU-Optimized On-Demand Face Recognition Engine
Uses YuNet & SFace ONNX neural models. Only processes confirmed faces to preserve CPU.
"""

from __future__ import annotations
import os
import logging
from typing import Dict, List, Tuple, Optional, Any
import cv2
import numpy as np

log = logging.getLogger("OMS.FaceRecog")


class OnDemandFaceEngine:
    """
    Evaluates face identity strictly on demand.
    Maintains temporal confidence voting to prevent name flickering.
    """

    def __init__(
        self,
        yunet_path: str = "models/face_detection_yunet_2023mar.onnx",
        sface_path: str = "models/face_recognition_sface_2021dec.onnx",
        match_threshold: float = 0.42,
        min_face_size: int = 40
    ):
        self.match_threshold = match_threshold
        self.min_face_size = min_face_size
        self.known_db: Dict[str, np.ndarray] = {}  # name -> 128-dim embedding
        self.track_votes: Dict[int, Dict[str, int]] = {} # track_id -> {name: vote_count}
        self.track_locked_names: Dict[int, str] = {}

        self.yunet = None
        self.sface = None

        if os.path.exists(yunet_path) and os.path.exists(sface_path):
            try:
                self.yunet = cv2.FaceDetectorYN.create(yunet_path, "", (320, 320), 0.6, 0.3, 500)
                self.sface = cv2.FaceRecognizerSF.create(sface_path, "")
                log.info("[FACE RECOGNITION] Initialized YuNet + SFace ONNX engine.")
            except Exception as e:
                log.warning(f"[FACE RECOGNITION] Initialization warning: {e}")

    def enroll_face(self, name: str, face_img: np.ndarray) -> bool:
        """Enrolls a known face embedding into local memory."""
        if self.yunet is None or self.sface is None or face_img is None:
            return False

        h, w = face_img.shape[:2]
        self.yunet.setInputSize((w, h))
        _, faces = self.yunet.detect(face_img)

        if faces is not None and len(faces) > 0:
            aligned = self.sface.alignCrop(face_img, faces[0])
            feature = self.sface.feature(aligned)
            self.known_db[name] = feature
            log.info(f"[FACE ENROLL] Enrolled identity: {name}")
            return True
        return False

    def identify_person_crop(self, person_crop: np.ndarray, track_id: Optional[int] = None) -> Tuple[str, float]:
        """
        Identifies person from cropped image.
        Returns (name, confidence). If unrecognized, returns ("Unknown", 0.0).
        """
        # If identity is already locked and confirmed for this track, return locked name
        if track_id is not None and track_id in self.track_locked_names:
            return self.track_locked_names[track_id], 0.95

        if self.yunet is None or self.sface is None or person_crop is None:
            return "Unknown", 0.0

        ph, pw = person_crop.shape[:2]
        if ph < self.min_face_size or pw < self.min_face_size:
            return "Unknown", 0.0

        self.yunet.setInputSize((pw, ph))
        _, faces = self.yunet.detect(person_crop)

        if faces is None or len(faces) == 0:
            return "Unknown", 0.0

        # Extract features for best detected face
        best_face = faces[0]
        aligned = self.sface.alignCrop(person_crop, best_face)
        feature = self.sface.feature(aligned)

        best_name = "Unknown"
        best_score = -1.0

        for name, known_feat in self.known_db.items():
            score = self.sface.match(feature, known_feat, cv2.FaceRecognizerSF_FR_COSINE)
            if score > best_score:
                best_score = float(score)
                best_name = name

        if best_score < self.match_threshold:
            return "Unknown", max(0.0, best_score)

        # Apply temporal voting if track_id is provided
        if track_id is not None:
            if track_id not in self.track_votes:
                self.track_votes[track_id] = {}
            votes = self.track_votes[track_id]
            votes[best_name] = votes.get(best_name, 0) + 1

            # Require 3 consecutive votes before locking identity
            if votes[best_name] >= 3:
                self.track_locked_names[track_id] = best_name
                log.info(f"[IDENTITY CONFIRMED] Track #{track_id} locked to '{best_name}' (conf: {best_score:.2f})")

        return best_name, best_score
