"""Pytest fixtures for the Playwright e2e suite.

Boots the Flask app on a free local port via Werkzeug's built-in server in a
background thread for the duration of the test session. Hermetic — no real
city APIs are ever called (tests intercept the API routes via Playwright).
"""

from __future__ import annotations

import socket
import sys
import threading
import time
from pathlib import Path
from typing import Iterator

import pytest
from werkzeug.serving import make_server

# Make the project root importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app as flask_app  # noqa: E402


def _find_free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class _BackgroundServer:
    def __init__(self, app, port: int) -> None:
        self.port = port
        self._srv = make_server("127.0.0.1", port, app, threaded=True)
        self._thread = threading.Thread(target=self._srv.serve_forever, daemon=True)

    def __enter__(self):
        self._thread.start()
        # Wait until socket accepts
        for _ in range(50):
            try:
                with socket.create_connection(("127.0.0.1", self.port), timeout=0.2):
                    return self
            except OSError:
                time.sleep(0.05)
        raise RuntimeError(f"server did not start on port {self.port}")

    def __exit__(self, *exc):
        self._srv.shutdown()


@pytest.fixture(scope="session")
def base_url() -> Iterator[str]:
    port = _find_free_port()
    with _BackgroundServer(flask_app, port):
        yield f"http://127.0.0.1:{port}"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    # Slightly larger viewport than the Playwright default so the wizard layout
    # renders in its desktop form.
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 900},
    }
