import sys


def test_concurrency_overlap(make_runner):
    python = sys.executable
    steps = [
        {
            "name": "x",
            "source": {
                "type": "process",
                "configuration": {
                    "command": [
                        python,
                        "-c",
                        "import time; time.sleep(0.2); print('x')",
                    ]
                },
            },
            "input": {"type": "parameter", "value": ""},
        },
        {
            "name": "y",
            "source": {
                "type": "process",
                "configuration": {
                    "command": [
                        python,
                        "-c",
                        "import time; time.sleep(0.2); print('y')",
                    ]
                },
            },
            "input": {"type": "parameter", "value": ""},
        },
    ]

    r = make_runner(steps, runner_conf={"max_workers": 4})
    r.run()

    sx = r.status.steps.get("x")
    sy = r.status.steps.get("y")
    assert sx is not None and sy is not None
    # timestamps should be present
    assert sx.started_at is not None and sx.ended_at is not None
    assert sy.started_at is not None and sy.ended_at is not None
    # they should overlap: x started before y ended and y started before x ended
    assert sx.started_at < sy.ended_at
    assert sy.started_at < sx.ended_at
