# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\Prajan\\.gemini\\antigravity\\scratch\\smart_surveillance\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('frontend/out', 'frontend/out'), ('models', 'models'), ('yolov8n.pt', '.'), ('yolov8s.pt', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='OMS_Sentinel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
