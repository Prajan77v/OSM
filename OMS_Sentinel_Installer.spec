# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['create_installer.py'],
    pathex=[],
    binaries=[],
    datas=[('main.py', '.'), ('web_server.py', '.'), ('web_integration.py', '.'), ('requirements.txt', '.'), ('faces', 'faces'), ('config.yaml', '.'), ('frontend/out', 'frontend/out')],
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
    name='OMS_Sentinel_Installer',
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
