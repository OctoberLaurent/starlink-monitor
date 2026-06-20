"""Tests for parsing the gRPC response (``_parse_status``)."""

from __future__ import annotations

import app

# Response mimicking grpcurl output (uptimeS as str, state absent = CONNECTED).
PAYLOAD = {
    "dishGetStatus": {
        "deviceInfo": {
            "id": "ut01000000-00000000-00abcd",
            "hardwareVersion": "rev3_proto2",
            "softwareVersion": "2026.06.04.cr80926",
            "countryCode": "BE",
            "bootcount": "561",
        },
        "deviceState": {"uptimeS": "27822"},
        "downlinkThroughputBps": 15000000,
        "uplinkThroughputBps": 2000000,
        "popPingLatencyMs": 31.5,
        "popPingDropRate": 0.0,
        "obstructionStats": {
            "fractionObstructed": 0.0,
            "currentlyObstructed": False,
        },
        "alerts": {"motorsStuck": False, "thermalThrottle": False},
        "boresightAzimuthDeg": -48.5,
        "boresightElevationDeg": 71.2,
    }
}


def test_parse_status_basic_fields():
    sample, info = app._parse_status(PAYLOAD)
    assert sample.down_mbps == 15.0
    assert sample.up_mbps == 2.0
    assert sample.latency_ms == 31.5
    assert sample.drop_rate == 0.0
    assert sample.obstruction_pct == 0.0
    assert sample.state == "CONNECTED"  # state field absent => CONNECTED
    assert sample.uptime_s == 27822  # str -> int


def test_parse_status_dish_info():
    _, info = app._parse_status(PAYLOAD)
    assert info["id"] == "ut01000000-00000000-00abcd"
    assert info["hardware"] == "rev3_proto2"
    assert info["country"] == "BE"
    assert info["boresight_az"] == -48.5
    assert info["boresight_el"] == 71.2


def test_parse_status_obstruction_percent():
    payload = {
        "dishGetStatus": {
            "deviceInfo": {},
            "deviceState": {"uptimeS": 0},
            "obstructionStats": {
                "fractionObstructed": 0.12,
                "currentlyObstructed": True,
            },
            "alerts": {"motorsStuck": True},
        }
    }
    sample, _ = app._parse_status(payload)
    assert sample.obstruction_pct == 12.0
    assert sample.currently_obstructed is True
    assert "motorsStuck" in sample.alerts


def test_parse_status_state_enum_numeric():
    payload = {"dishGetStatus": {"deviceInfo": {}, "deviceState": {}, "state": 1}}
    sample, _ = app._parse_status(payload)
    assert sample.state == "SEARCHING"


def test_parse_status_handles_missing_fields():
    sample, info = app._parse_status({"dishGetStatus": {}})
    assert sample.down_mbps == 0.0
    assert sample.latency_ms == 0.0
    assert sample.state == "CONNECTED"
    assert info["id"] == "?"
