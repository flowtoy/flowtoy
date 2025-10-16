from typing import Any, Dict, List

import pytest

from evans.runner import LocalRunner


@pytest.fixture
def make_runner():
    """Return a factory that constructs a LocalRunner from a list of flow steps.

    Usage in tests:
        r = make_runner(steps)
        r.run()
    """

    def _make(
        steps: List[Dict[str, Any]], runner_conf: Dict[str, Any] | None = None
    ) -> LocalRunner:
        cfg: Dict[str, Any] = {"sources": {}, "flow": steps}
        if runner_conf is not None:
            cfg["runner"] = runner_conf
        return LocalRunner(cfg)

    return _make


import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import pytest


class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        uid = qs.get("id", [None])[0]
        path = parsed.path
        resp = {}
        status = 200
        if path.startswith("/hr"):
            resp = {"jobs": [f"job-for-{uid}"]}
        elif path.startswith("/sis/programs"):
            resp = {"programs": [f"program-for-{uid}"]}
        elif path.startswith("/sis/courses"):
            resp = {"courses": [f"course-for-{uid}"]}
        else:
            status = 404
            resp = {"error": "not found"}

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(resp).encode("utf-8"))

    def log_message(self, format, *args):
        # suppress default logging in tests
        pass


def _start_server():
    srv = HTTPServer(("127.0.0.1", 0), SimpleHandler)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    return srv


@pytest.fixture(scope="function")
def http_server():
    """Start a simple HTTP server and yield its base URL for tests.

    The handler serves /hr, /sis/programs and /sis/courses paths.
    """
    srv = _start_server()
    try:
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        yield base
    finally:
        srv.shutdown()
        srv.server_close()
