#!/usr/bin/env python3
"""
Starlink Incident Monitor
=========================
Continuously monitors a Starlink dish via its local gRPC API
(``192.168.100.1:9200``), detects incidents (micro-outages, obstructions,
high latency, hardware alerts...) and exposes them through a real-time web
dashboard.

If the dish is unreachable (or ``grpcurl`` is missing), a realistic simulator
takes over so the interface remains demonstrable.

Direct run:
    python app.py
Then open http://127.0.0.1:5050

Environment variables:
    STARLINK_TARGET  gRPC target (default 192.168.100.1:9200)
    STARLINK_POLL    polling interval in seconds (default 1.0)
    STARLINK_RETRY   real-dish retry interval in seconds (default 15.0)
    STARLINK_DEMO    "1" to force demo mode
    STARLINK_GRPCURL path to the grpcurl binary
    HOST             listen host (default 127.0.0.1)
    PORT             listen port (default 5050)
"""

from __future__ import annotations

import json
import logging
import os
import random
import subprocess
import sys
import threading
import time
from collections import deque
from contextlib import suppress
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

from flask import Flask, Response, jsonify, render_template

logger = logging.getLogger("starlink")


# --------------------------------------------------------------------------- #
#  Environment detection (script vs PyInstaller bundle)
# --------------------------------------------------------------------------- #
def _is_frozen() -> bool:
    """True when running from a PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def _resource_dir() -> str:
    """Directory holding resources (templates, static, grpcurl).

    In a ``.app`` bundle: ``Contents/Resources``. As a script: the source dir.
    """
    if _is_frozen():
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        resources = os.path.abspath(os.path.join(exe_dir, "..", "Resources"))
        return resources if os.path.isdir(resources) else exe_dir
    return os.path.dirname(os.path.abspath(__file__))


def _writable_data_dir() -> str:
    """Writable directory for the incident log (the bundle is read-only)."""
    if _is_frozen():
        base = os.path.expanduser("~/Library/Application Support/StarlinkMonitor")
        os.makedirs(base, exist_ok=True)
        return base
    return os.path.dirname(os.path.abspath(__file__))


def _resolve_grpcurl() -> str:
    """Resolve the grpcurl binary: env > bundle resources > PATH."""
    env_path = os.environ.get("STARLINK_GRPCURL")
    if env_path and os.path.isfile(env_path):
        return env_path
    for base in (_resource_dir(), getattr(sys, "_MEIPASS", "")):
        if not base:
            continue
        cand = os.path.join(base, "grpcurl")
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return "grpcurl"


def _validate_target(target: str) -> str:
    """Validate a gRPC target as ``host:port`` to prevent argument injection.

    Returns the target if valid, otherwise the default target. Only a plain
    ``host:port`` is accepted (no flags, spaces, or shell metacharacters).
    """
    import re

    if isinstance(target, str) and re.fullmatch(
        r"[A-Za-z0-9._-]+:\d{1,5}", target.strip()
    ):
        return target.strip()
    logger.warning(
        "Invalid STARLINK_TARGET %r, falling back to %s", target, _DEFAULT_TARGET
    )
    return _DEFAULT_TARGET


def _positive_float_env(name: str, default: float) -> float:
    """Read a strictly positive float from the environment."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        logger.warning("Invalid %s=%r, falling back to %s", name, raw, default)
        return default
    if value <= 0:
        logger.warning("Invalid %s=%r, falling back to %s", name, raw, default)
        return default
    return value


# --------------------------------------------------------------------------- #
#  Configuration
# --------------------------------------------------------------------------- #
_DEFAULT_TARGET = "192.168.100.1:9200"
DISH_TARGET = _validate_target(os.environ.get("STARLINK_TARGET", _DEFAULT_TARGET))
POLL_INTERVAL = _positive_float_env("STARLINK_POLL", 1.0)  # seconds
REAL_RETRY_INTERVAL = _positive_float_env("STARLINK_RETRY", 15.0)
HISTORY_SAMPLES = 600  # live buffer
MAX_INCIDENTS = 2_000
MAX_INCIDENT_LOG_BYTES = 5 * 1024 * 1024
INCIDENT_FILE = os.path.join(_writable_data_dir(), "incidents.jsonl")
DEMO_MODE = os.environ.get("STARLINK_DEMO", "").lower() in ("1", "true", "yes")
GRPCURL_CMD = _resolve_grpcurl()
GRPCURL_TIMEOUT = 6  # seconds
GRPCURL_CONNECT_TIMEOUT = "4"

# Incident detection thresholds
TH_DROPRATE = 0.10  # packet loss rate (> 10 %)
TH_LATENCY = 150.0  # latency in ms triggering an alert
TH_OBSTRUCTION = 5.0  # % of time obstructed
TH_LATENCY_CRITICAL = 400.0
TH_DROPRATE_CRITICAL = 0.5
TH_OBSTRUCTION_CRITICAL = 25.0
INCIDENT_OPEN_SAMPLES = 3
INCIDENT_CLOSE_SAMPLES = 3

# Starlink hardware alerts -> human label
ALERT_FIELDS: dict[str, str] = {
    "motorsStuck": "Motors stuck",
    "thermalThrottle": "Thermal throttle",
    "thermalShutdown": "Thermal shutdown",
    "mastNotNearVertical": "Mast not vertical",
    "slowEthernetSpeeds": "Slow ethernet",
}

# Possible dish states (gRPC ``state`` field)
DISH_STATE_MAP = {0: "CONNECTED", 1: "SEARCHING", 2: "BOOTING", 3: "STOWED"}


class Severity(StrEnum):
    """Severity level of an incident."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

    @classmethod
    def for_value(cls, value: float, critical: float) -> Severity:
        return cls.CRITICAL if value >= critical else cls.WARNING


# --------------------------------------------------------------------------- #
#  Data models
# --------------------------------------------------------------------------- #
@dataclass
class Sample:
    """A telemetry sample from the dish."""

    ts: float
    down_mbps: float
    up_mbps: float
    latency_ms: float
    drop_rate: float  # 0..1
    obstruction_pct: float  # 0..100
    currently_obstructed: bool
    uptime_s: int
    state: str
    alerts: list[str] = field(default_factory=list)
    snr_persistently_low: bool = False


# Valid fields for (re)building an Incident from disk.
_INCIDENT_FIELDS = {
    "ts_start",
    "ts_end",
    "kind",
    "severity",
    "title",
    "detail",
    "ongoing",
    "params",
}


@dataclass
class Incident:
    """A detected incident (opened then eventually closed)."""

    ts_start: float
    ts_end: float | None
    kind: str  # outage | packet_loss | latency | obstruction | snr | alert_*
    severity: Severity
    title: str
    detail: str
    ongoing: bool = True
    # Structured parameters letting the frontend localize title + detail.
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Incident:
        """Build an Incident, ignoring unknown keys."""
        kwargs = {k: v for k, v in d.items() if k in _INCIDENT_FIELDS}
        if "severity" in kwargs:
            kwargs["severity"] = Severity(kwargs["severity"])
        return cls(**kwargs)


# --------------------------------------------------------------------------- #
#  Shared global state (thread-safe)
# --------------------------------------------------------------------------- #
class MonitorState:
    """Monitoring state shared between the polling loop and the web API."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.samples: deque[Sample] = deque(maxlen=HISTORY_SAMPLES)
        self.incidents: list[Incident] = []
        self.open: dict[str, Incident] = {}  # kind -> ongoing Incident
        self.last_sample: Sample | None = None
        self.dish_info: dict[str, Any] = {}
        self.last_error: str = ""
        self.connected: bool = False
        self.demo: bool = False
        self.poll_count: int = 0
        self._bad_counts: dict[str, int] = {}
        self._good_counts: dict[str, int] = {}

    # -- Public API (thread-safe) -----------------------------------------
    def add_sample(
        self,
        sample: Sample,
        *,
        demo: bool,
        dish_info: dict[str, Any],
        connected: bool = True,
        detect_incidents: bool = True,
    ) -> None:
        with self._lock:
            self.samples.append(sample)
            self.last_sample = sample
            self.dish_info = dish_info
            self.demo = demo
            self.connected = connected
            if connected:
                self.last_error = ""
            if detect_incidents:
                self._detect(sample, resolve_outage=connected)

    def mark_disconnected(self, err: str) -> None:
        with self._lock:
            self.connected = False
            self.last_error = err
            self.last_sample = None
            self._open(
                "outage",
                Severity.CRITICAL,
                "Dish unreachable",
                f"Could not reach the dish: {err}",
                params={"error": err},
            )

    def increment_poll(self) -> None:
        with self._lock:
            self.poll_count += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            incidents = sorted(self.incidents, key=lambda i: i.ts_start, reverse=True)[
                :200
            ]
            return {
                "connected": self.connected,
                "demo": self.demo,
                "target": DISH_TARGET,
                "last_error": self.last_error,
                "poll_count": self.poll_count,
                "dish_info": self.dish_info,
                "last_sample": asdict(self.last_sample) if self.last_sample else None,
                "samples": [asdict(s) for s in self.samples],
                "incidents": [i.to_dict() for i in incidents],
                "open_incidents": sum(1 for i in self.incidents if i.ongoing),
                "total_incidents": len(self.incidents),
                "thresholds": {
                    "drop_rate": TH_DROPRATE,
                    "latency_ms": TH_LATENCY,
                    "obstruction_pct": TH_OBSTRUCTION,
                },
            }

    # -- Incident detection (under lock) -----------------------------------
    def _detect(self, s: Sample, *, resolve_outage: bool = True) -> None:
        now = time.time()

        # outage resolved
        if resolve_outage and "outage" in self.open:
            self._close("outage", now)

        self._check(
            s.drop_rate > TH_DROPRATE,
            "packet_loss",
            Severity.for_value(s.drop_rate, TH_DROPRATE_CRITICAL),
            "High packet loss",
            f"Loss rate: {s.drop_rate * 100:.1f} %  "
            f"(latency {s.latency_ms:.0f} ms)",
            now,
            params={
                "drop": round(s.drop_rate * 100, 1),
                "latency": round(s.latency_ms),
            },
        )

        self._check(
            s.latency_ms > TH_LATENCY,
            "latency",
            Severity.for_value(s.latency_ms, TH_LATENCY_CRITICAL),
            "Latency spike",
            f"Latency: {s.latency_ms:.0f} ms",
            now,
            params={"latency": round(s.latency_ms)},
        )

        obstructed = s.obstruction_pct > TH_OBSTRUCTION or s.currently_obstructed
        self._check(
            obstructed,
            "obstruction",
            Severity.for_value(s.obstruction_pct, TH_OBSTRUCTION_CRITICAL),
            "Signal obstruction",
            f"Obstructed: {s.obstruction_pct:.1f} % of the time",
            now,
            params={"obs": round(s.obstruction_pct, 1)},
        )

        self._check(
            s.snr_persistently_low,
            "snr",
            Severity.WARNING,
            "Low SNR",
            "SNR below noise floor",
            now,
            params={},
        )

        # Hardware alerts
        for alert in s.alerts:
            label = ALERT_FIELDS.get(alert, alert)
            self._open(
                f"alert_{alert}",
                Severity.CRITICAL,
                f"Alert: {label}",
                f"The dish reports '{alert}'",
                params={"alert": alert, "label": label},
            )
        # close resolved alerts
        for key in list(self.open):
            if key.startswith("alert_") and key.removeprefix("alert_") not in s.alerts:
                self._close(key, now)

    def _check(
        self,
        condition: bool,
        kind: str,
        severity: Severity,
        title: str,
        detail: str,
        now: float,
        params: dict[str, Any] | None = None,
    ) -> None:
        if condition:
            self._good_counts[kind] = 0
            self._bad_counts[kind] = self._bad_counts.get(kind, 0) + 1
            if kind in self.open or self._bad_counts[kind] >= INCIDENT_OPEN_SAMPLES:
                self._open(kind, severity, title, detail, params=params)
        else:
            self._bad_counts[kind] = 0
            self._good_counts[kind] = self._good_counts.get(kind, 0) + 1
            if kind in self.open and self._good_counts[kind] >= INCIDENT_CLOSE_SAMPLES:
                self._close(kind, now)

    def _open(
        self,
        kind: str,
        severity: Severity,
        title: str,
        detail: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> None:
        inc = self.open.get(kind)
        params = params or {}
        if inc is None:
            inc = Incident(
                ts_start=time.time(),
                ts_end=None,
                kind=kind,
                severity=severity,
                title=title,
                detail=detail,
                params=params,
            )
            self.open[kind] = inc
            self._remember(inc)
            self._persist(inc)
            logger.warning("Incident opened [%s] %s — %s", severity, title, detail)
        else:
            if severity is Severity.CRITICAL and inc.severity is not Severity.CRITICAL:
                inc.severity = Severity.CRITICAL
            inc.detail = detail
            inc.params = params

    def _remember(self, inc: Incident) -> None:
        """Keep a bounded in-memory history without evicting active incidents."""
        self.incidents.append(inc)
        while len(self.incidents) > MAX_INCIDENTS:
            closed_index = next(
                (
                    index
                    for index, item in enumerate(self.incidents)
                    if not item.ongoing
                ),
                None,
            )
            if closed_index is None:
                break
            del self.incidents[closed_index]

    def _close(self, kind: str, now: float) -> None:
        inc = self.open.pop(kind, None)
        if inc is not None:
            inc.ts_end = now
            inc.ongoing = False
            self._persist(inc)
            logger.info("Incident resolved [%s] %s", inc.severity, inc.title)

    def _persist(self, inc: Incident) -> None:
        try:
            with open(INCIDENT_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(inc.to_dict(), ensure_ascii=False) + "\n")
            if os.path.getsize(INCIDENT_FILE) > MAX_INCIDENT_LOG_BYTES:
                self._compact_incident_log()
        except OSError as e:
            logger.error("Could not persist incident: %s", e)

    def _compact_incident_log(self) -> None:
        """Atomically rewrite the log with the retained incident history."""
        temporary = f"{INCIDENT_FILE}.tmp"
        try:
            with open(temporary, "w", encoding="utf-8") as f:
                for incident in self.incidents:
                    f.write(json.dumps(incident.to_dict(), ensure_ascii=False) + "\n")
            os.replace(temporary, INCIDENT_FILE)
        except OSError:
            with suppress(OSError):
                os.unlink(temporary)
            raise


STATE = MonitorState()


# --------------------------------------------------------------------------- #
#  Real data source (grpcurl)
# --------------------------------------------------------------------------- #
def _try_grpcurl() -> dict[str, Any] | None:
    """Query the dish via grpcurl. Returns the parsed JSON or ``None``."""
    try:
        out = subprocess.run(  # nosec B603  # nosemgrep  # list call, target validated
            [
                GRPCURL_CMD,
                "-plaintext",
                "-connect-timeout",
                GRPCURL_CONNECT_TIMEOUT,
                "-d",
                '{"get_status":{}}',
                DISH_TARGET,
                "SpaceX.API.Device.Device/Handle",
            ],
            capture_output=True,
            text=True,
            timeout=GRPCURL_TIMEOUT,
            check=False,
        )
    except FileNotFoundError:
        logger.info("grpcurl not found (%s)", GRPCURL_CMD)
        return None
    except subprocess.TimeoutExpired:
        logger.warning("Timed out querying the dish")
        return None
    if out.returncode != 0 or not out.stdout.strip():
        return None
    try:
        data = json.loads(out.stdout)
    except json.JSONDecodeError:
        logger.warning("grpcurl response is not valid JSON")
        return None
    if not isinstance(data, dict):
        logger.warning("Unexpected grpcurl response (not an object)")
        return None
    return data


def _parse_status(payload: dict[str, Any]) -> tuple[Sample, dict[str, Any]]:
    """Convert grpcurl JSON into a ``Sample`` + dish info."""
    st = payload.get("dishGetStatus") or payload.get("dish_get_status") or {}
    info = st.get("deviceInfo", {}) or {}
    dstate = st.get("deviceState", {}) or {}
    obs = st.get("obstructionStats", {}) or {}
    alerts = st.get("alerts", {}) or {}

    state_enum = st.get("state")
    # grpcurl omits proto fields at their default value (0 = CONNECTED).
    if state_enum is None:
        state_name = "CONNECTED"
    elif isinstance(state_enum, int):
        state_name = DISH_STATE_MAP.get(state_enum, str(state_enum))
    else:
        state_name = str(state_enum)

    fired_alerts = [k for k in ALERT_FIELDS if alerts.get(k)]

    sample = Sample(
        ts=time.time(),
        down_mbps=_to_float(st.get("downlinkThroughputBps")) / 1e6,
        up_mbps=_to_float(st.get("uplinkThroughputBps")) / 1e6,
        latency_ms=_to_float(st.get("popPingLatencyMs")),
        drop_rate=_to_float(st.get("popPingDropRate")),
        obstruction_pct=_to_float(obs.get("fractionObstructed")) * 100.0,
        currently_obstructed=bool(obs.get("currentlyObstructed", False)),
        uptime_s=int(_to_float(dstate.get("uptimeS"))),
        state=state_name,
        alerts=fired_alerts,
        snr_persistently_low=bool(
            alerts.get("snrPersistentlyLow", False)
            or st.get("snrPersistentlyLow", False)
        ),
    )
    dish_info = {
        "id": info.get("id", "?"),
        "hardware": info.get("hardwareVersion", "?"),
        "software": info.get("softwareVersion", "?"),
        "country": info.get("countryCode", "?"),
        "bootcount": info.get("bootcount", 0),
        "boresight_az": _to_float(st.get("boresightAzimuthDeg")),
        "boresight_el": _to_float(st.get("boresightElevationDeg")),
    }
    return sample, dish_info


def _to_float(value: Any) -> float:
    """Convert a gRPC value (int, float, numeric str, None) to float."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


# --------------------------------------------------------------------------- #
#  Demo simulator (when the dish is not available)
# --------------------------------------------------------------------------- #
class DemoSimulator:
    """Generates realistic data and simulated incidents cyclically."""

    _DEMO_INFO: dict[str, Any] = {
        "id": "DEMO-UT1234-567890",
        "hardware": "rev3_proto2",
        "software": "demo-2026.06.20",
        "country": "FR",
        "bootcount": 42,
        "boresight_az": 145.0,
        "boresight_el": 32.0,
    }

    def __init__(self) -> None:
        self.phase: str = "normal"
        self.phase_t: float = 0.0
        self.phase_len: float = 30.0
        self.down: float = 180.0
        self.up: float = 18.0
        self.lat: float = 35.0
        self.drop: float = 0.0
        self.obs_pct: float = 0.0
        self.cur_obs: bool = False
        self.uptime: int = 3600 * 27

    def next(self) -> tuple[Sample, dict[str, Any]]:
        self._advance_phase()
        self.uptime += int(POLL_INTERVAL)
        self._step()
        self._clamp()

        sample = Sample(
            ts=time.time(),
            down_mbps=round(self.down, 2),
            up_mbps=round(self.up, 2),
            latency_ms=round(self.lat, 1),
            drop_rate=round(self.drop, 4),
            obstruction_pct=round(self.obs_pct, 2),
            currently_obstructed=self.cur_obs,
            uptime_s=self.uptime,
            state="CONNECTED" if self.phase != "outage" else "SEARCHING",
            alerts=[],
            snr_persistently_low=self._snr_low(),
        )
        return sample, dict(self._DEMO_INFO)

    # -- internal details --
    def _advance_phase(self) -> None:
        self.phase_t += POLL_INTERVAL
        if self.phase_t <= self.phase_len:
            return
        self.phase_t = 0.0
        r = random.random()
        if r < 0.35:
            self.phase, self.phase_len = "normal", random.uniform(18, 38)
        elif r < 0.62:
            self.phase, self.phase_len = "storm", random.uniform(12, 26)
        elif r < 0.85:
            self.phase, self.phase_len = "obstruction", random.uniform(12, 22)
        else:
            self.phase, self.phase_len = "outage", random.uniform(5, 10)

    def _step(self) -> None:
        if self.phase == "normal":
            self.down += random.uniform(-6, 6)
            self.up += random.uniform(-1, 1)
            self.lat += random.uniform(-2, 2)
            self.drop = max(0.0, self.drop + random.uniform(-0.005, 0.005))
            self.obs_pct = max(0.0, self.obs_pct * 0.9 + random.uniform(0, 0.05))
            self.cur_obs = False
        elif self.phase == "storm":
            self.down = max(5, self.down + random.uniform(-25, 10))
            self.up = max(0.5, self.up + random.uniform(-4, 2))
            self.lat += random.uniform(-5, 20)
            self.drop = min(0.6, self.drop + random.uniform(-0.02, 0.06))
            self.obs_pct = max(0.0, self.obs_pct + random.uniform(-0.5, 1.5))
            self.cur_obs = random.random() < 0.3
        elif self.phase == "obstruction":
            self.down = max(5, self.down + random.uniform(-15, 3))
            self.lat += random.uniform(-3, 10)
            self.drop = min(0.35, self.drop + random.uniform(-0.01, 0.03))
            self.obs_pct = min(40, self.obs_pct + random.uniform(1, 4))
            self.cur_obs = True
        else:  # outage
            self.down = 0.0
            self.up = 0.0
            self.lat = 0.0
            self.drop = 1.0
            self.cur_obs = True

    def _snr_low(self) -> bool:
        if self.phase == "storm":
            return random.random() < 0.2
        return self.phase == "outage"

    def _clamp(self) -> None:
        self.down = max(0.0, min(320.0, self.down))
        self.up = max(0.0, min(40.0, self.up))
        self.lat = max(8.0, min(600.0, self.lat))
        self.drop = max(0.0, min(1.0, self.drop))
        self.obs_pct = max(0.0, min(100.0, self.obs_pct))


SIM = DemoSimulator()


# --------------------------------------------------------------------------- #
#  Monitoring loop
# --------------------------------------------------------------------------- #
class PollController:
    """One-step polling state machine with automatic real-dish retries."""

    def __init__(self, *, forced_demo: bool = DEMO_MODE) -> None:
        self.forced_demo = forced_demo
        self.fallback_demo = False
        self.next_real_retry = 0.0

    def step(self, *, now: float | None = None) -> None:
        current_time = time.monotonic() if now is None else now

        if self.forced_demo:
            sample, info = SIM.next()
            STATE.add_sample(sample, demo=True, dish_info=info)
            return

        should_try_real = not self.fallback_demo or current_time >= self.next_real_retry
        if should_try_real:
            payload = _try_grpcurl()
            if payload is not None:
                sample, info = _parse_status(payload)
                STATE.add_sample(sample, demo=False, dish_info=info)
                self.fallback_demo = False
                self.next_real_retry = 0.0
                return

            STATE.mark_disconnected("dish unreachable / grpcurl missing")
            if not self.fallback_demo:
                logger.info("Falling back to demo mode (dish unreachable)")
            self.fallback_demo = True
            self.next_real_retry = current_time + REAL_RETRY_INTERVAL

        sample, info = SIM.next()
        STATE.add_sample(
            sample,
            demo=True,
            dish_info=info,
            connected=False,
            detect_incidents=False,
        )


def poll_loop() -> None:
    """Infinite dish-polling loop (daemon thread)."""
    controller = PollController()
    if controller.forced_demo:
        logger.info("Demo mode forced by STARLINK_DEMO")
    while True:
        try:
            controller.step()
        except Exception as e:  # noqa: BLE001  loop safety net
            logger.exception("Error in the monitoring loop: %s", e)
            STATE.mark_disconnected(str(e))
        finally:
            STATE.increment_poll()
        time.sleep(POLL_INTERVAL)


# --------------------------------------------------------------------------- #
#  Incident persistence
# --------------------------------------------------------------------------- #
def _load_persisted_incidents() -> None:
    """Reload the persisted incident history.

    Incidents still "open" from a previous process are ignored (stale: the
    issue will be reopened if it persists).
    """
    if not os.path.exists(INCIDENT_FILE):
        return
    try:
        with open(INCIDENT_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(d, dict):
                    continue
                if d.get("ongoing"):
                    continue
                try:
                    STATE._remember(Incident.from_dict(d))
                except (TypeError, ValueError):
                    logger.debug("Skipped persisted incident (schema): %s", line)
    except OSError as e:
        logger.error("Could not read the incident log: %s", e)


# --------------------------------------------------------------------------- #
#  Flask application
# --------------------------------------------------------------------------- #
def create_app() -> Flask:
    """Build the Flask application (templates + local static assets)."""
    resources = _resource_dir()
    flask_app = Flask(
        __name__,
        template_folder=os.path.join(resources, "templates"),
        static_folder=os.path.join(resources, "static"),
    )

    @flask_app.route("/")
    def index() -> str:
        return render_template("index.html")

    @flask_app.route("/api/state")
    def api_state() -> Response:
        return jsonify(STATE.snapshot())

    @flask_app.route("/api/incidents")
    def api_incidents() -> Response:
        snap = STATE.snapshot()
        return jsonify(
            {
                "incidents": snap["incidents"],
                "open": snap["open_incidents"],
                "total": snap["total_incidents"],
            }
        )

    return flask_app


app = create_app()


def start_monitoring() -> None:
    """Start the background monitoring loop and reload the history."""
    _load_persisted_incidents()
    thread = threading.Thread(target=poll_loop, name="poll-loop", daemon=True)
    thread.start()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    start_monitoring()
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5050"))
    logger.info("🛰️  Starlink Incident Monitor — http://%s:%s", host, port)
    app.run(host=host, port=port, threaded=True)


if __name__ == "__main__":
    main()
