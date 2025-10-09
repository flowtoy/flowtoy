import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

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
