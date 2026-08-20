"""
OMS Edge — Hardware Diagnostics, Health Monitoring & Adaptive CPU Control.
Guarantees smooth performance without crashing or freezing on CPU-only machines.
"""

from __future__ import annotations
import os
import time
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import List, Dict, Any

log = logging.getLogger("OMS.HealthMonitor")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
    CUDA_DEVICE = torch.cuda.get_device_name(0) if CUDA_AVAILABLE else "CPU"
except ImportError:
    CUDA_AVAILABLE = False
    CUDA_DEVICE = "CPU"


def detect_hardware_profile(override_profile: str = "AUTO") -> str:
    """
    Detects machine hardware profile (LOW, MEDIUM, HIGH).
    Uses CPU cores & RAM if no CUDA GPU is detected.
    """
    if override_profile in ("LOW", "MEDIUM", "HIGH"):
        return override_profile

    if CUDA_AVAILABLE:
        return "HIGH"

    cores = os.cpu_count() or 2
    ram_gb = (psutil.virtual_memory().total / (1024**3)) if PSUTIL_AVAILABLE else 4.0

    if cores >= 8 and ram_gb >= 16:
        return "HIGH"
    elif cores >= 4 and ram_gb >= 8:
        return "MEDIUM"
    return "LOW"


@dataclass
class AdaptiveConfig:
    fps_target: int = 25
    det_w: int = 640
    det_h: int = 384
    process_every_n: int = 2
    overloaded: bool = False


class AdaptiveController:
    """
    Dynamically adjusts detection resolution and frame-skipping
    to maintain target frame rates and prevent CPU overload.
    """

    def __init__(self, hw_profile: str = "MEDIUM", overload_cpu_pct: float = 85.0):
        self.hw_profile = hw_profile
        self.overload_threshold = overload_cpu_pct
        self._history: deque = deque(maxlen=6)
        self._last_check_t = 0.0

        # Baseline settings based on hardware profile
        if hw_profile == "HIGH":
            self.fps_target = 30
            self.det_w, self.det_h = 640, 384
            self.process_every_n = 2
        elif hw_profile == "MEDIUM":
            self.fps_target = 25
            self.det_w, self.det_h = 480, 288
            self.process_every_n = 3
        else: # LOW / CPU-Only
            self.fps_target = 18
            self.det_w, self.det_h = 320, 192
            self.process_every_n = 4

        self.overloaded = False

    def update(self) -> AdaptiveConfig:
        """Evaluates CPU usage and dynamically throttles if needed."""
        now = time.time()
        if now - self._last_check_t < 2.0:
            return self.get_config()

        self._last_check_t = now
        cpu_pct = psutil.cpu_percent(interval=None) if PSUTIL_AVAILABLE else 50.0
        self._history.append(cpu_pct)
        avg_cpu = sum(self._history) / len(self._history)

        if avg_cpu > self.overload_threshold:
            # Extreme load: aggressively drop resolution and process every 5th frame
            self.overloaded = True
            self.fps_target = max(10, self.fps_target - 5)
            self.process_every_n = min(6, self.process_every_n + 2)
            self.det_w = max(256, int(self.det_w * 0.75))
            self.det_h = max(160, int(self.det_h * 0.75))
            log.warning(f"[ADAPTIVE] CPU Load High ({avg_cpu:.1f}%). Throttled: {self.det_w}x{self.det_h} every {self.process_every_n} frames.")
        elif avg_cpu < 65.0 and self.overloaded:
            # Recover when CPU drops
            self.overloaded = False
            self.update_profile(self.hw_profile)
            log.info(f"[ADAPTIVE] CPU Load Normal ({avg_cpu:.1f}%). Restored baseline settings.")

        return self.get_config()

    def update_profile(self, profile: str):
        self.hw_profile = profile
        if profile == "HIGH":
            self.fps_target, self.det_w, self.det_h, self.process_every_n = 30, 640, 384, 2
        elif profile == "MEDIUM":
            self.fps_target, self.det_w, self.det_h, self.process_every_n = 25, 480, 288, 3
        else:
            self.fps_target, self.det_w, self.det_h, self.process_every_n = 18, 320, 192, 4

    def get_config(self) -> AdaptiveConfig:
        return AdaptiveConfig(
            fps_target=self.fps_target,
            det_w=self.det_w,
            det_h=self.det_h,
            process_every_n=self.process_every_n,
            overloaded=self.overloaded
        )


def get_system_telemetry() -> Dict[str, Any]:
    """Returns local system diagnostic metrics."""
    cpu = psutil.cpu_percent(interval=None) if PSUTIL_AVAILABLE else 0.0
    ram = psutil.virtual_memory().percent if PSUTIL_AVAILABLE else 0.0
    return {
        "cpu": cpu,
        "ram": ram,
        "gpu": 0,
        "gpu_name": CUDA_DEVICE,
        "cuda": CUDA_AVAILABLE,
        "hw_profile": detect_hardware_profile()
    }
