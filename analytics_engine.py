import cv2
import numpy as np
from typing import List, Tuple, Dict, Any

def generate_occupancy_heatmap(width: int, height: int, centers: List[Tuple[int, int]]) -> np.ndarray:
    heatmap = np.zeros((height, width), dtype=np.float32)
    for (cx, cy) in centers:
        if 0 <= cx < width and 0 <= cy < height:
            heatmap[cy, cx] += 1.0
    if heatmap.max() > 0:
        heatmap = (heatmap / heatmap.max() * 255).astype(np.uint8)
    else:
        heatmap = heatmap.astype(np.uint8)
    return cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

def estimate_distance(height_px: int, frame_height: int = 1080, focal_length_factor: float = 800.0) -> float:
    if height_px <= 0:
        return 0.0
    average_human_height_m = 1.7
    return round((average_human_height_m * focal_length_factor) / height_px, 2)

def enhance_low_light(frame: np.ndarray) -> np.ndarray:
    if frame is None or frame.size == 0:
        return frame
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)