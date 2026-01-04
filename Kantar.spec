# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules
from pathlib import Path
import os

project_root = Path(os.getcwd()).resolve()

hiddenimports = (
    collect_submodules("django")
    + collect_submodules("rest_framework")
    + collect_submodules("PyQt6")
    + ["waitress"]
)

datas = [
    (project_root / "weight_department_schedule", "weight_department_schedule"),
    (project_root / "scheduler", "scheduler"),
    (project_root / "desktop_app", "desktop_app"),
    (project_root / "data", "data"),
    (project_root / "docs", "docs"),
]

a = Analysis(
    ["desktop_app/main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Kantar",
    icon=str(project_root / "assets" / "kantar.icns"),
    debug=False,
    strip=False,
    upx=True,
    console=False,
)

app = BUNDLE(
    exe,
    name="Kantar.app",
    icon=str(project_root / "assets" / "kantar.icns"),
    bundle_identifier="com.kantar.schedule",
)
