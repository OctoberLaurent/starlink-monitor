#!/usr/bin/env python3
"""
macOS application launcher for "Starlink Incident Monitor".

Starts the Flask backend in the background and displays the dashboard in a
native window (WebKit via pywebview). Falls back to the default browser if
pywebview is not available.
"""

from __future__ import annotations

import logging
import os
import socket
import sys
import threading
import time
import webbrowser
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger("starlink.launcher")


def _is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def _free_port() -> int:
    """Return a free TCP port on 127.0.0.1."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _ensure_grpcurl() -> None:
    """Point ``STARLINK_GRPCURL`` to the bundled binary if present."""
    candidates = [
        os.path.join(getattr(sys, "_MEIPASS", "") or HERE, "grpcurl"),
        os.path.join(HERE, "grpcurl"),
        os.path.join(HERE, "..", "Resources", "grpcurl"),
    ]
    for cand in candidates:
        cand = os.path.abspath(cand)
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            os.environ["STARLINK_GRPCURL"] = cand
            return


def _start_backend(port: int) -> Any:
    """Start the Flask backend on ``port`` (daemon thread). Returns the server."""
    sys.path.insert(0, HERE)
    import app as flaskapp  # noqa: E402

    os.environ["PORT"] = str(port)
    flaskapp.start_monitoring()

    from werkzeug.serving import make_server  # noqa: E402

    server = make_server("127.0.0.1", port, flaskapp.app, threaded=True)
    threading.Thread(
        target=server.serve_forever, name="flask-server", daemon=True
    ).start()
    return server


def _open_window(url: str) -> None:
    """Open the dashboard in a native window, otherwise in the browser."""
    try:
        import webview  # noqa: E402

        webview.create_window(
            "Starlink Incident Monitor",
            url,
            width=1400,
            height=900,
            min_size=(960, 640),
            text_select=False,
        )
        webview.start()
    except Exception as e:  # noqa: BLE001
        logger.warning("pywebview unavailable (%s) — opening browser.", e)
        webbrowser.open(url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    _ensure_grpcurl()

    port = _free_port()
    server = _start_backend(port)

    url = f"http://127.0.0.1:{port}"
    # give the server time to start
    time.sleep(1.0)
    logger.info("Opening dashboard: %s", url)

    _open_window(url)

    server.shutdown()
    sys.exit(0)


if __name__ == "__main__":
    main()
