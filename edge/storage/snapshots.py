"""
OMS Edge — Snapshot & Thumbnail Processing
Encodes lightweight JPEG base64 thumbnails for cloud event transmission.
"""

import base64
from typing import Optional, Tuple
import cv2
import numpy as np


def create_event_snapshot(
    frame: np.ndarray,
    box: Optional[Tuple[int, int, int, int]] = None,
    max_dim: int = 640,
    jpeg_quality: int = 75
) -> Optional[str]:
    """
    Downscales and encodes a frame (or cropped region of interest) to base64 JPEG string.
    Keeps snapshot payload sizes small (< 40 KB) for free-tier cloud bandwidth.
    """
    if frame is None or frame.size == 0:
        return None

    img_to_encode = frame

    # Crop to bounding box with 15% padding if provided
    if box is not None:
        x1, y1, x2, y2 = box
        h, w = frame.shape[:2]
        pad_x = int((x2 - x1) * 0.15)
        pad_y = int((y2 - y1) * 0.15)
        cx1 = max(0, x1 - pad_x)
        cy1 = max(0, y1 - pad_y)
        cx2 = min(w, x2 + pad_x)
        cy2 = min(h, y2 + pad_y)
        if cx2 > cx1 and cy2 > cy1:
            img_to_encode = frame[cy1:cy2, cx1:cx2]

    # Resize if larger than max_dim
    ih, iw = img_to_encode.shape[:2]
    if max(ih, iw) > max_dim:
        scale = max_dim / float(max(ih, iw))
        new_w, new_h = int(iw * scale), int(ih * scale)
        img_to_encode = cv2.resize(img_to_encode, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Encode as JPEG
    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality]
    success, buffer = cv2.imencode(".jpg", img_to_encode, encode_params)
    if not success:
        return None

    return base64.b64encode(buffer).decode("utf-8")
