# -*- mode: python ; coding: utf-8 -*-
import os
import shutil
import sys

block_cipher = None

datas = [
    ("templates", "templates"),
    ("static", "static"),
    ("StarlinkMonitor.icns", "."),
]

# Resolve the grpcurl binary to bundle: env STARLINK_GRPCURL, then PATH.
# Prerequisite: `brew install grpcurl` (or `go install ...`).
grpcurl_path = os.environ.get("STARLINK_GRPCURL") or shutil.which("grpcurl")
if not grpcurl_path or not os.path.isfile(grpcurl_path):
    print(
        "ERROR: grpcurl is required to build the app. "
        "Install it: brew install grpcurl  (or export STARLINK_GRPCURL=/path)",
        file=sys.stderr,
    )
    sys.exit(1)
binaries = [
    (grpcurl_path, "."),
]

hiddenimports = [
    # Flask stack
    "flask", "jinja2", "jinja2.ext", "werkzeug", "werkzeug.serving",
    "werkzeug.middleware", "click", "itsdangerous", "markupsafe", "blinker",
    # pywebview macOS
    "webview", "webview.platforms.cocoa",
    "webview", "webview.platforms.cocoa",
    "Foundation", "AppKit", "WebKit", "Quartz", "Cocoa",
]

a = Analysis(
    ["launcher.py"],
    pathex=[os.path.abspath(".")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "PySide6", "PyQt6", "PyQt5"],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="StarlinkMonitor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon="StarlinkMonitor.icns",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="StarlinkMonitor",
)

app = BUNDLE(
    coll,
    name="StarlinkMonitor.app",
    icon="StarlinkMonitor.icns",
    bundle_identifier="com.earendil.starlink-monitor",
    info_plist={
        "CFBundleName": "Starlink Monitor",
        "CFBundleDisplayName": "Starlink Monitor",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "12.0",
        "NSAppTransportSecurity": {
            "NSAllowsArbitraryLoads": True,
            "NSAllowsLocalNetworking": True,
        },
        "LSEnvironment": {"STARLINK_DEMO": "0"},
    },
)