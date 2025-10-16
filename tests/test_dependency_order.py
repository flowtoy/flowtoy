import sys


def test_dependency_order(make_runner):
    python = sys.executable
    cmd_a = "import time,json;time.sleep(0.08);print(json.dumps({'v':1}))"
    cmd_b = "import json;print(json.dumps({'v':2}))"

    steps = [
        {
            "name": "a",
            "source": {
                "type": "process",
                "configuration": {
                    "command": [
                        python,
                        "-c",
                        cmd_a,
                    ]
                },
            },
            "input": {"type": "parameter", "value": ""},
            "output": [{"name": "v", "type": "json"}],
        },
        {
            "name": "b",
            "depends_on": ["a"],
            "source": {
                "type": "process",
                "configuration": {
                    "command": [
                        python,
                        "-c",
                        cmd_b,
                    ]
                },
            },
            "input": {"type": "parameter", "value": ""},
            "output": [{"name": "v", "type": "json"}],
        },
    ]

    r = make_runner(steps)
    r.run()

    s_a = r.status.steps["a"]
    s_b = r.status.steps["b"]

    # b should start after a ended
    assert s_a.ended_at is not None
    assert s_b.started_at is not None
    assert s_b.started_at >= s_a.ended_at
