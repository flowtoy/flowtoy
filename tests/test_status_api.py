import sys
import time

import requests

from flowtoy.runner_api import serve_runner_api_in_thread


def test_status_api(make_runner):
    python = sys.executable
    steps = [
        {
            "name": "one",
            "source": {
                "type": "process",
                "configuration": {"command": [python, "-c", "print('ok')"]},
            },
            "input": {"type": "parameter", "value": ""},
        },
    ]

    r = make_runner(steps)
    # serve api
    serve_runner_api_in_thread(r, host="127.0.0.1", port=8010)

    # run the flow
    r.run()

    # allow API a moment
    time.sleep(0.1)
    resp = requests.get("http://127.0.0.1:8010/status", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("total_steps") == 1
    assert data.get("completed_steps") == 1
