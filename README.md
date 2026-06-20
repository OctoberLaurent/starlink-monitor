# 🛰️ Starlink Incident Monitor

![CI](https://github.com/OctoberLaurent/starlink-monitor/actions/workflows/ci.yml/badge.svg)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> 🌐 Languages / Idiomas: **English** (default) · [Français](README.fr.md) · [Español](README.es.md)

A web application that continuously monitors a **Starlink** dish via its local
gRPC API (`192.168.100.1:9200`), detects incidents, and displays a **very
stylish real-time dashboard** (space theme, glassmorphism, live charts, polar
obstruction map, incident timeline).

## Features

- **Live polling** of the dish (1 sample/second) via `grpcurl` (if the dish is unreachable, automatically falls back to **demo mode** with realistic simulated data).
- **Incident detection**:
  - 🛑 `outage` — dish unreachable / disconnection
  - 📉 `packet_loss` — packet loss rate > 10 %
  - 📡 `latency` — latency > 150 ms
  - 🌲 `obstruction` — signal obstruction
  - 🔻 `snr` — SNR below noise floor
  - ⚠️ `alert` — hardware alerts (motors stuck, thermal throttle, mast not vertical, slow ethernet…)
- **Persistence** of incidents in `incidents.jsonl` (reloaded on restart).
- **Stylish UI**: animated starfield, nebula, neon gauges, 2 real-time charts (Chart.js), polar SVG obstruction map, incident timeline with severity levels.
- **Multilingual 🇬🇧 🇫🇷 🇪🇸**: UI and incidents translated into English, French, and Spanish. English is the default; select another language via the flags in the top-right. The choice is remembered.

## Quick start

```bash
cd /Users/laurentleplat/Web/starlink
./run.sh
```

Then open **http://127.0.0.1:5050**

> The default port is `5050` (port `5000` is taken by AirPlay Receiver on macOS).
> To change it: `PORT=8000 ./run.sh`

### Without the script

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt        # runtime
.venv/bin/pip install -r requirements-dev.txt    # build + lint
.venv/bin/python app.py
```

### Code quality

```bash
.venv/bin/ruff check .          # lint
.venv/bin/black --check .       # formatting
.venv/bin/mypy                  # static type analysis (strict, PHPStan equivalent)
```

### Unit tests

```bash
.venv/bin/pytest                # 29 tests (detection, parsing, persistence, simulator, routes)
```

Tests cover: incident detection (open/close, severities), gRPC response parsing,
JSONL persistence, demo-simulator bounds, and Flask routes.

## Connecting to the real dish

The app calls `grpcurl -plaintext 192.168.100.1:9200 SpaceX.API.Device.Device/Handle`.
To use the real dish:

1. Install `grpcurl`: `brew install grpcurl` (or `go install github.com/fullstorydev/grpcurl/cmd/grpcurl@latest`).
2. Be on the Starlink dish Wi-Fi network (the API is only reachable locally).
3. Launch the app. If the dish responds, demo mode is disabled automatically.

Environment variables:

| Variable            | Default               | Role |
|--------------------|------------------------|------|
| `STARLINK_TARGET`  | `192.168.100.1:9200`   | gRPC target of the dish |
| `STARLINK_POLL`    | `1.0`                  | Polling interval (s) |
| `STARLINK_DEMO`    | (auto)                | `1` to force demo mode |
| `STARLINK_GRPCURL` | (auto)                | Path to the grpcurl binary |
| `HOST`             | `127.0.0.1`            | Listen host (localhost by default) |
| `PORT`             | `5050`                 | Web server port |

## Architecture

```
app.py                 → Flask backend + polling thread + incident detection
  ├── _try_grpcurl()       queries the dish via grpcurl (JSON)
  ├── _parse_status()      converts gRPC JSON into a Sample + dish info
  ├── DemoSimulator        realistic simulated data (demo mode)
  ├── MonitorState         samples + incidents + detection (open/closed)
  └── /api/state, /api/incidents, /
templates/index.html   → stylish dashboard (starfield, gauges, charts, radar, timeline)
incidents.jsonl        → persistent incident log
```

## Detection thresholds (configurable at the top of `app.py`)

| Parameter          | Value | Triggered incident |
|--------------------|-------|--------------------|
| `TH_DROPRATE`      | 0.10  | packet loss > 10 % |
| `TH_LATENCY`       | 150 ms| latency spike |
| `TH_OBSTRUCTION`   | 5 %   | signal obstruction |
| `ALERT_FIELDS`     | …     | Starlink hardware alerts |

## macOS packaging (.app + .dmg)

The app can be packaged as a native macOS app (WebKit window via pywebview) and
then into a DMG installer. The DMG is **not** included in the repository (build
artifact, too large): it is compiled locally.

**Prerequisites**: macOS (Apple Silicon preferred), Xcode command line tools,
and `grpcurl` (bundled into the app):

```bash
xcode-select --install
brew install grpcurl
.venv/bin/pip install -r requirements-dev.txt   # pyinstaller, pillow, pywebview…
```

**Build**:

```bash
.venv/bin/python build_icon.py                              # 1. generate .icns icon
.venv/bin/python -m PyInstaller StarlinkMonitor.spec --noconfirm   # 2. build .app
./build_dmg.sh                                              # 3. build .dmg
```

The result is in `dist/StarlinkMonitor.dmg`. The `grpcurl` binary and static
assets (Chart.js) are bundled — the app works offline.

> `StarlinkMonitor.spec` resolves `grpcurl` from the `STARLINK_GRPCURL` env var
> or the `PATH`. To force a binary: `STARLINK_GRPCURL=/path/to/grpcurl`.
>
> The app is *ad-hoc* signed. On first launch macOS may block it:
> right-click the app → **Open** → confirm.
> Current build: **arm64** (Apple Silicon). For Intel, rebuild on an x86_64 machine.

## Notes

- The local Starlink gRPC API is unofficial and unsupported by SpaceX — subject to change.
- Demo mode: activates automatically if `grpcurl` is missing or the dish is unreachable, so the UI remains demonstrable.
- **100 % offline**: Chart.js is bundled locally (`static/`), the dashboard works without Internet.
- The web server only listens on `127.0.0.1` by default (security); override with `HOST=0.0.0.0` for network access.