#!/usr/bin/env bash
# Launch the Starlink monitor in the local venv.
set -euo pipefail
cd "$(dirname "$0")"

PYTHON=".venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "Virtual environment missing. Create it with: python3 -m venv .venv" >&2
  echo "Then install dependencies with: .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

if ! "$PYTHON" -c "import flask" >/dev/null 2>&1; then
  echo "Runtime dependencies are missing. Run: .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

exec "$PYTHON" app.py "$@"
