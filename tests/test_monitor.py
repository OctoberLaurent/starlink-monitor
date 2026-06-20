"""Tests for incident detection and persistence (``MonitorState``)."""

from __future__ import annotations

import json
from typing import Any

import app
from app import MonitorState, Sample, Severity


def make_sample(**overrides) -> Sample:
    defaults: dict[str, Any] = {
        "ts": 0.0,
        "down_mbps": 100.0,
        "up_mbps": 10.0,
        "latency_ms": 30.0,
        "drop_rate": 0.0,
        "obstruction_pct": 0.0,
        "currently_obstructed": False,
        "uptime_s": 3600,
        "state": "CONNECTED",
        "alerts": [],
        "snr_persistently_low": False,
    }
    defaults.update(overrides)
    return Sample(**defaults)


def fresh_state() -> MonitorState:
    return MonitorState()


def add_samples(st: MonitorState, count: int, **overrides) -> None:
    for _ in range(count):
        st.add_sample(make_sample(**overrides), demo=False, dish_info={})


# --------------------------------------------------------------------------- #
#  Detection
# --------------------------------------------------------------------------- #
def test_normal_sample_no_incident():
    st = fresh_state()
    st.add_sample(make_sample(), demo=False, dish_info={})
    assert st.incidents == []
    assert st.connected is True
    assert st.last_sample is not None


def test_packet_loss_open_then_close():
    st = fresh_state()
    add_samples(st, app.INCIDENT_OPEN_SAMPLES - 1, drop_rate=0.3)
    assert "packet_loss" not in st.open  # transient spike is ignored

    add_samples(st, 1, drop_rate=0.3)
    assert "packet_loss" in st.open
    assert st.open["packet_loss"].severity is Severity.WARNING

    add_samples(st, app.INCIDENT_CLOSE_SAMPLES - 1, drop_rate=0.0)
    assert "packet_loss" in st.open  # transient recovery is ignored

    add_samples(st, 1, drop_rate=0.0)
    assert "packet_loss" not in st.open
    closed = [i for i in st.incidents if i.kind == "packet_loss"][0]
    assert closed.ongoing is False
    assert closed.ts_end is not None


def test_packet_loss_critical_threshold():
    st = fresh_state()
    add_samples(st, app.INCIDENT_OPEN_SAMPLES, drop_rate=0.6)
    assert st.open["packet_loss"].severity is Severity.CRITICAL


def test_latency_incident():
    st = fresh_state()
    add_samples(st, app.INCIDENT_OPEN_SAMPLES, latency_ms=200.0)
    assert "latency" in st.open
    assert st.open["latency"].severity is Severity.WARNING
    st.add_sample(make_sample(latency_ms=500.0), demo=False, dish_info={})
    assert st.open["latency"].severity is Severity.CRITICAL


def test_obstruction_incident():
    st = fresh_state()
    add_samples(st, app.INCIDENT_OPEN_SAMPLES, obstruction_pct=10.0)
    assert "obstruction" in st.open
    # currently_obstructed also triggers even with a low %
    st2 = fresh_state()
    add_samples(
        st2,
        app.INCIDENT_OPEN_SAMPLES,
        obstruction_pct=0.0,
        currently_obstructed=True,
    )
    assert "obstruction" in st2.open


def test_snr_incident():
    st = fresh_state()
    add_samples(st, app.INCIDENT_OPEN_SAMPLES, snr_persistently_low=True)
    assert "snr" in st.open
    add_samples(st, app.INCIDENT_CLOSE_SAMPLES, snr_persistently_low=False)
    assert "snr" not in st.open


def test_hardware_alert_open_and_close():
    st = fresh_state()
    st.add_sample(make_sample(alerts=["motorsStuck"]), demo=False, dish_info={})
    assert "alert_motorsStuck" in st.open
    assert st.open["alert_motorsStuck"].severity is Severity.CRITICAL
    st.add_sample(make_sample(alerts=[]), demo=False, dish_info={})
    assert "alert_motorsStuck" not in st.open


def test_outage_on_disconnect_then_resolved():
    st = fresh_state()
    st.mark_disconnected("test")
    assert "outage" in st.open
    assert st.connected is False
    assert st.last_sample is None

    st.add_sample(make_sample(), demo=False, dish_info={})
    assert "outage" not in st.open
    assert st.connected is True


def test_snapshot_structure():
    st = fresh_state()
    st.add_sample(make_sample(), demo=False, dish_info={"id": "X"})
    snap = st.snapshot()
    for key in (
        "connected",
        "demo",
        "poll_count",
        "dish_info",
        "last_sample",
        "samples",
        "incidents",
        "open_incidents",
        "total_incidents",
        "thresholds",
    ):
        assert key in snap
    assert snap["dish_info"]["id"] == "X"
    assert snap["target"] == app.DISH_TARGET
    assert snap["open_incidents"] == 0
    assert snap["thresholds"]["latency_ms"] == app.TH_LATENCY


# --------------------------------------------------------------------------- #
#  Persistence
# --------------------------------------------------------------------------- #
def test_persistence_writes_open_and_close(tmp_path, monkeypatch):
    log = tmp_path / "incidents.jsonl"
    monkeypatch.setattr(app, "INCIDENT_FILE", str(log))

    st = fresh_state()
    add_samples(st, app.INCIDENT_OPEN_SAMPLES, drop_rate=0.3)
    add_samples(st, app.INCIDENT_CLOSE_SAMPLES, drop_rate=0.0)

    lines = [json.loads(line) for line in log.read_text().splitlines() if line]
    assert len(lines) == 2  # 1 open + 1 close
    assert lines[0]["kind"] == "packet_loss"
    assert lines[0]["ongoing"] is True
    assert lines[1]["ongoing"] is False


def test_load_persisted_ignores_ongoing(tmp_path, monkeypatch):
    log = tmp_path / "incidents.jsonl"
    log.write_text(
        json.dumps(
            {
                "ts_start": 1,
                "ts_end": 2,
                "kind": "latency",
                "severity": "warning",
                "title": "t",
                "detail": "d",
                "ongoing": False,
            }
        )
        + "\n"
        + json.dumps(
            {
                "ts_start": 3,
                "ts_end": None,
                "kind": "outage",
                "severity": "critical",
                "title": "t",
                "detail": "d",
                "ongoing": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(app, "INCIDENT_FILE", str(log))
    fresh = MonitorState()
    monkeypatch.setattr(app, "STATE", fresh)

    app._load_persisted_incidents()

    kinds = [i.kind for i in fresh.incidents]
    assert kinds == ["latency"]  # the ongoing incident is ignored
    assert fresh.incidents[0].severity is Severity.WARNING


def test_incident_history_is_bounded_without_evicting_open_incidents(monkeypatch):
    monkeypatch.setattr(app, "MAX_INCIDENTS", 2)
    st = fresh_state()
    old_closed = app.Incident(1, 2, "old", Severity.WARNING, "old", "", False)
    open_incident = app.Incident(3, None, "open", Severity.CRITICAL, "open", "")
    recent_closed = app.Incident(4, 5, "recent", Severity.WARNING, "recent", "", False)

    st._remember(old_closed)
    st._remember(open_incident)
    st._remember(recent_closed)

    assert st.incidents == [open_incident, recent_closed]


def test_incident_log_is_compacted(tmp_path, monkeypatch):
    log = tmp_path / "incidents.jsonl"
    monkeypatch.setattr(app, "INCIDENT_FILE", str(log))
    monkeypatch.setattr(app, "MAX_INCIDENT_LOG_BYTES", 1)
    st = fresh_state()

    add_samples(st, app.INCIDENT_OPEN_SAMPLES, drop_rate=0.3)
    add_samples(st, app.INCIDENT_CLOSE_SAMPLES, drop_rate=0.0)

    lines = [json.loads(line) for line in log.read_text().splitlines() if line]
    assert len(lines) == 1
    assert lines[0]["kind"] == "packet_loss"
    assert lines[0]["ongoing"] is False
