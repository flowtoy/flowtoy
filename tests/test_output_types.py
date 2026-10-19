"""Test output extraction types: raw, jmespath, and the deprecated json alias."""

import sys

import pytest

from flowtoy.runner import LocalRunner


def _env_flow(monkeypatch, output):
    monkeypatch.setenv("OUT_TEST", "hello")
    return {
        "sources": {"e": {"type": "env", "configuration": {"vars": ["OUT_TEST"]}}},
        "flow": [{"name": "s", "source": "e", "output": output}],
    }


def test_raw_returns_data(monkeypatch):
    runner = LocalRunner(_env_flow(monkeypatch, [{"name": "v", "type": "raw"}]))
    runner.run()
    assert runner.flows["s"]["v"] == {"OUT_TEST": "hello"}


def test_omitted_type_defaults_to_raw(monkeypatch):
    runner = LocalRunner(_env_flow(monkeypatch, [{"name": "v"}]))
    runner.run()
    assert runner.flows["s"]["v"] == {"OUT_TEST": "hello"}


def test_json_alias_behaves_like_raw(monkeypatch, caplog):
    runner = LocalRunner(_env_flow(monkeypatch, [{"name": "v", "type": "json"}]))
    runner.run()
    assert runner.flows["s"]["v"] == {"OUT_TEST": "hello"}
    assert "deprecated" in caplog.text


def test_unknown_type_raises(monkeypatch):
    runner = LocalRunner(_env_flow(monkeypatch, [{"name": "v", "type": "jsonpath"}]))
    with pytest.raises(ValueError) as exc_info:
        runner.run()
    msg = str(exc_info.value)
    assert "invalid output types" in msg
    assert "'jsonpath'" in msg


def test_process_parsed_stdout_via_jmespath():
    cfg = {
        "sources": {
            "p": {
                "type": "process",
                "configuration": {
                    "command": [sys.executable, "-c", "print('{\"a\": 1}')"]
                },
            }
        },
        "flow": [
            {
                "name": "s",
                "source": "p",
                "output": [
                    {"name": "parsed", "type": "jmespath", "value": "json"},
                    {"name": "whole", "type": "raw"},
                ],
            }
        ],
    }
    runner = LocalRunner(cfg)
    runner.run()
    assert runner.flows["s"]["parsed"] == {"a": 1}
    assert runner.flows["s"]["whole"]["json"] == {"a": 1}
    assert "stdout" in runner.flows["s"]["whole"]
