import sys


def test_on_error_policies(make_runner):
    python = sys.executable
    cmd_fail = "import sys; sys.exit(2)"
    cmd_noop = "print('noop')"
    cmd_ok = "print('ok')"
    steps = [
        {
            "name": "will_fail",
            "source": {
                "type": "process",
                "configuration": {"command": [python, "-c", cmd_fail]},
            },
            "input": {"type": "parameter", "value": ""},
        },
        {
            "name": "skipped_dep",
            "depends_on": ["will_fail"],
            "on_error": "skip",
            "source": {
                "type": "process",
                "configuration": {"command": [python, "-c", cmd_noop]},
            },
            "input": {"type": "parameter", "value": ""},
        },
        {
            "name": "continued",
            "on_error": "continue",
            "source": {
                "type": "process",
                "configuration": {"command": [python, "-c", cmd_ok]},
            },
            "input": {"type": "parameter", "value": ""},
        },
    ]

    r = make_runner(steps, runner_conf={"max_workers": 2, "on_error": "fail"})
    r.run()

    assert r.status.steps["will_fail"].state == "failed"
    # skipped_dep should be marked skipped because will_fail failed and
    # its on_error is skip
    assert r.status.steps["skipped_dep"].state == "skipped"
    # continued should run despite failure since its policy is continue
    assert r.status.steps["continued"].state == "succeeded"
