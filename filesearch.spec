# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

project_root = Path.cwd()
src_root = project_root / "src"
sys.path.insert(0, str(src_root))

icon_path = os.environ.get("FILESEARCH_PYINSTALLER_ICON") or None
bundle_identifier = "dev.filesearch.app"

datas = collect_data_files("filesearch", excludes=["**/__pycache__/*"])

a = Analysis(
    ["src/filesearch/__main__.py"],
    pathex=[str(src_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FileSearch",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="FileSearch",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="FileSearch.app",
        icon=icon_path,
        bundle_identifier=bundle_identifier,
    )
