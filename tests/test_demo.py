"""Tests for the demo simulator (``DemoSimulator``)."""

from __future__ import annotations

import app


def test_demo_returns_sample_and_info():
    sim = app.DemoSimulator()
    sample, info = sim.next()
    assert isinstance(sample, app.Sample)
    assert sample.state in {"CONNECTED", "SEARCHING"}
    for key in (
        "id",
        "hardware",
        "software",
        "country",
        "bootcount",
        "boresight_az",
        "boresight_el",
    ):
        assert key in info


def test_demo_values_within_bounds():
    sim = app.DemoSimulator()
    for _ in range(500):  # exercises several phases
        sample, _ = sim.next()
        assert 0.0 <= sample.down_mbps <= 320.0
        assert 0.0 <= sample.up_mbps <= 40.0
        assert 8.0 <= sample.latency_ms <= 600.0
        assert 0.0 <= sample.drop_rate <= 1.0
        assert 0.0 <= sample.obstruction_pct <= 100.0
        assert sample.uptime_s > 0


def test_demo_outage_phase_zeroes_throughput():
    sim = app.DemoSimulator()
    sim.phase = "outage"
    sim.phase_len = 999.0  # do not change phase during the test
    sample, _ = sim.next()
    assert sample.down_mbps == 0.0
    assert sample.up_mbps == 0.0
    assert sample.drop_rate == 1.0
    assert sample.state == "SEARCHING"
    assert sample.snr_persistently_low is True


def test_demo_runs_without_error_over_many_cycles():
    sim = app.DemoSimulator()
    for _ in range(2000):
        sim.next()
    # no exception raised => test OK
