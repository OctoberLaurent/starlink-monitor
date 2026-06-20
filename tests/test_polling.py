"""Tests for automatic demo fallback and real-dish reconnection."""

from __future__ import annotations

from typing import Any

import app


def sample() -> app.Sample:
    return app.Sample(
        ts=1.0,
        down_mbps=100.0,
        up_mbps=10.0,
        latency_ms=30.0,
        drop_rate=0.0,
        obstruction_pct=0.0,
        currently_obstructed=False,
        uptime_s=3600,
        state="CONNECTED",
    )


class FakeSimulator:
    def next(self) -> tuple[app.Sample, dict[str, Any]]:
        return sample(), {"id": "DEMO", "software": "demo"}


REAL_PAYLOAD = {
    "dishGetStatus": {
        "deviceInfo": {"id": "REAL", "softwareVersion": "real"},
        "deviceState": {"uptimeS": 7200},
        "popPingLatencyMs": 25,
    }
}


def test_fallback_keeps_outage_open_and_retries_real_dish(monkeypatch):
    state = app.MonitorState()
    for _ in range(app.INCIDENT_OPEN_SAMPLES):
        degraded = sample()
        degraded.latency_ms = 250.0
        state.add_sample(degraded, demo=False, dish_info={"id": "REAL"})
    assert "latency" in state.open

    responses = iter([None, REAL_PAYLOAD])
    calls = 0

    def fetch() -> dict[str, Any] | None:
        nonlocal calls
        calls += 1
        return next(responses)

    monkeypatch.setattr(app, "STATE", state)
    monkeypatch.setattr(app, "SIM", FakeSimulator())
    monkeypatch.setattr(app, "_try_grpcurl", fetch)
    monkeypatch.setattr(app, "REAL_RETRY_INTERVAL", 10.0)
    controller = app.PollController(forced_demo=False)

    controller.step(now=0.0)
    assert calls == 1
    assert state.demo is True
    assert state.connected is False
    assert state.last_sample is not None
    assert "outage" in state.open
    assert "latency" in state.open  # simulated data cannot resolve a real incident

    controller.step(now=9.0)
    assert calls == 1  # simulated samples do not hammer the unreachable dish
    assert state.connected is False
    assert "outage" in state.open
    assert "latency" in state.open

    controller.step(now=10.0)
    assert calls == 2
    assert state.demo is False
    assert state.connected is True
    assert state.dish_info["id"] == "REAL"
    assert "outage" not in state.open


def test_forced_demo_never_queries_the_dish(monkeypatch):
    state = app.MonitorState()

    def unexpected_fetch() -> None:
        raise AssertionError("forced demo must not query grpcurl")

    monkeypatch.setattr(app, "STATE", state)
    monkeypatch.setattr(app, "SIM", FakeSimulator())
    monkeypatch.setattr(app, "_try_grpcurl", unexpected_fetch)

    app.PollController(forced_demo=True).step(now=0.0)

    assert state.demo is True
    assert state.connected is True
    assert state.last_sample is not None
