#!/usr/bin/env bash
# Launch the Starlink monitor in the local venv.
set -e
cd "$(dirname "$0")"
.venv/bin/pip install -q -r requirements.txt 2>/dev/null || true
exec .venv/bin/python app.py "$@"