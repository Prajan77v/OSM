# -*- mode: python ; coding: utf-8 -*-
# OMS Sentinel v9.0 — PyInstaller Spec
# Bundles: main.py + web_server.py + web_integration.py
#          + frontend/out (Next.js static export)
#          + models/ + YOLO weights + config.yaml

import os
from pathlib import Path

ROOT = Path(SPECPATH)

# ── Collect data files ────────────────────────────────────────────────────────
datas = []

# Next.js static export (served by FastAPI)
frontend_out = ROOT / "frontend" / "out"
if frontend_out.exists():
    datas.append((str(frontend_out), "frontend/out"))

# config.yaml (runtime config — user-editable, placed next to exe)
config_yaml = ROOT / "config.yaml"
if config_yaml.exists():
    datas.append((str(config_yaml), "."))

# Alarm sound
alarm_wav = ROOT / "alarm.wav"
if alarm_wav.exists():
    datas.append((str(alarm_wav), "."))

# faces/ directory (known faces, captured, etc.)
faces_dir = ROOT / "faces"
if faces_dir.exists():
    datas.append((str(faces_dir), "faces"))

# objects/ directory (known objects, etc.)
objects_dir = ROOT / "objects"
if objects_dir.exists():
    datas.append((str(objects_dir), "objects"))

# models/ directory (includes InsightFace buffalo_sc, YuNet, SFace, ResNet50)
models_dir = ROOT / "models"
if models_dir.exists():
    datas.append((str(models_dir), "models"))

# YOLO model weights
yolo_pt = ROOT / "yolov8n.pt"
if yolo_pt.exists():
    datas.append((str(yolo_pt), "."))

# ── Hidden imports needed by FastAPI / uvicorn / OpenCV / InsightFace / pynvml ─────────────
hidden_imports = [
    # OMS Face Engine & InsightFace
    "face_engine",
    "insightface",
    "insightface.app",
    "insightface.app.face_analysis",
    "insightface.model_zoo",
    "insightface.utils",
    "onnxruntime",
    # FastAPI / Starlette / uvicorn
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "fastapi",
    "fastapi.staticfiles",
    "fastapi.middleware.cors",
    "starlette",
    "starlette.middleware",
    "starlette.middleware.cors",
    "starlette.responses",
    "starlette.routing",
    "starlette.staticfiles",
    "anyio",
    "anyio.from_thread",
    # OpenCV
    "cv2",
    # Imaging
    "PIL",
    "PIL.Image",
    "PIL.ImageFont",
    "PIL.ImageDraw",
    # Ultralytics / YOLO
    "ultralytics",
    "ultralytics.models",
    "ultralytics.models.yolo",
    "ultralytics.models.yolo.detect",
    "ultralytics.nn",
    "ultralytics.nn.tasks",
    "ultralytics.utils",
    "torchvision",
    "sympy",
    # PyWin32
    "win32gui",
    "win32con",
    "pywintypes",
    # psutil / pynvml
    "psutil",
    "pynvml",
    # Other stdlib / third-party
    "json",
    "logging",
    "threading",
    "email.mime.text",
    "email.mime.multipart",
    "dotenv",
]

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pandas", "h5py", "IPython", "notebook", "jinja2", "sklearn", "scikit-learn", "tensorflow", "tensorboard", "keras", "PyQt5", "PySide2", "PySide6", "boto3", "botocore", "cryptography", "sqlalchemy", "numpy.tests"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="OMS_Sentinel",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=["vcruntime140.dll", "python3*.dll"],
    runtime_tmpdir=None,
    console=True,        # keep console so logs are visible; set False for silent background mode
    icon=None,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
