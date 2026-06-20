"""Integration tests for the Flask routes."""

from __future__ import annotations

import app
from app import MonitorState, Sample


def _client_with_fresh_state(monkeypatch):
    """Return a test client wired to a fresh, empty state."""
    monkeypatch.setattr(app, "STATE", MonitorState())
    return app.app.test_client()


def test_index_serves_html(monkeypatch):
    client = _client_with_fresh_state(monkeypatch)
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Starlink" in resp.data


def test_static_chart_js_served(monkeypatch):
    client = _client_with_fresh_state(monkeypatch)
    resp = client.get("/static/chart.umd.min.js")
    assert resp.status_code == 200
    assert len(resp.data) > 1000  # Chart.js is bundled


def test_api_state_shape(monkeypatch):
    client = _client_with_fresh_state(monkeypatch)
    # inject a sample
    app.STATE.add_sample(
        Sample(
            ts=0.0,
            down_mbps=100.0,
            up_mbps=10.0,
            latency_ms=30.0,
            drop_rate=0.0,
            obstruction_pct=0.0,
            currently_obstructed=False,
            uptime_s=3600,
            state="CONNECTED",
        ),
        demo=False,
        dish_info={"id": "X"},
    )
    resp = client.get("/api/state")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["connected"] is True
    assert data["demo"] is False
    assert data["dish_info"]["id"] == "X"
    assert len(data["samples"]) == 1
    assert data["last_sample"]["down_mbps"] == 100.0


def test_api_incidents_endpoint(monkeypatch):
    client = _client_with_fresh_state(monkeypatch)
    resp = client.get("/api/incidents")
    assert resp.status_code == 200
    data = resp.get_json()
    assert {"incidents", "open", "total"} <= set(data)
    assert data["total"] == 0
