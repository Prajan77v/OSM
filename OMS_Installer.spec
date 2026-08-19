# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['installer_wizard.py'],
    pathex=[],
    binaries=[],
    datas=[('main.py', '.'), ('web_server.py', '.'), ('web_integration.py', '.'), ('config.yaml', '.'), ('identity_engine.py', '.'), ('haae_engine.py', '.'), ('face_engine.py', '.'), ('db_engine.py', '.'), ('auth_engine.py', '.'), ('analytics_engine.py', '.'), ('cloud_sync.py', '.'), ('cloud_api.py', '.'), ('hikvision_connection_guide.txt', '.'), ('rtsp_10_cameras.txt', '.'), ('yolov8n.pt', '.'), ('models', 'models'), ('frontend/out', 'frontend/out')],
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
    name='OMS_Installer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
