"""Global pytest fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def isolate_incident_log(tmp_path, monkeypatch):
    """Prevent tests from polluting the application's real incident history."""
    import app

    monkeypatch.setattr(app, "INCIDENT_FILE", str(tmp_path / "incidents.jsonl"))
