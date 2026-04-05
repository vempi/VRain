# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['../src/VRainPrep.py'],
    pathex=[],
    binaries=[],
    datas=[('../demo', 'demo')],
    hiddenimports=['secrets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'scipy', 'shapely', 'shapefile', 'pyshp', 'pyproj',
        'lmoments3', 'cv2', 'skimage',
        'IPython', 'jupyter', 'notebook', 'nbformat', 'nbconvert',
        'seaborn', 'plotly', 'bokeh', 'altair',
    ],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='VRainPrep',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_dir='..',
    upx_exclude=['vcruntime140.dll', 'ucrtbase.dll'],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../assets/VRainPrep.ico',
)
