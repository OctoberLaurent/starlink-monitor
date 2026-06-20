"""Tests for helpers: ``_to_float``, ``Severity``, ``Incident.from_dict``."""

from __future__ import annotations

import app


def test_to_float_handles_types():
    assert app._to_float(None) == 0.0
    assert app._to_float(0) == 0.0
    assert app._to_float(1.5) == 1.5
    assert app._to_float("27822") == 27822.0  # uint64 serialized as str
    assert app._to_float("abc") == 0.0
    assert app._to_float([]) == 0.0


def test_severity_for_value():
    assert app.Severity.for_value(0.2, 0.5) is app.Severity.WARNING
    assert app.Severity.for_value(0.6, 0.5) is app.Severity.CRITICAL
    assert app.Severity.for_value(0.5, 0.5) is app.Severity.CRITICAL  # >=


def test_severity_is_string_enum():
    assert app.Severity.CRITICAL == "critical"
    assert app.Severity("warning") is app.Severity.WARNING


def test_incident_from_dict_ignores_unknown_keys():
    inc = app.Incident.from_dict(
        {
            "ts_start": 1.0,
            "ts_end": 2.0,
            "kind": "packet_loss",
            "severity": "critical",
            "title": "Loss",
            "detail": "d",
            "ongoing": False,
            "unknown_field": 42,
        }
    )
    assert inc.kind == "packet_loss"
    assert inc.severity is app.Severity.CRITICAL
    assert inc.ongoing is False
    assert inc.ts_end == 2.0


def test_incident_to_dict_roundtrip():
    inc = app.Incident(
        ts_start=1.0,
        ts_end=None,
        kind="snr",
        severity=app.Severity.WARNING,
        title="SNR",
        detail="d",
    )
    d = inc.to_dict()
    assert d["severity"] == "warning"
    assert d["ongoing"] is True
