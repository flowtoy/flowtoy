import subprocess
import types

import pytest

from flow.connectors.process import ProcessConnector


class DummyCompleted:
    def __init__(self, stdout=b"", stderr=b"", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def test_json_stdout(monkeypatch):
    # simulate subprocess returning JSON on stdout
    def fake_run(cmd, input, stdout, stderr, timeout=None):
        return DummyCompleted(stdout=b'{"ok": true}', stderr=b"", returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    pc = ProcessConnector({"command": ["/bin/echo"], "pass_to": "arg"})
    res = pc.call("anything")
    assert isinstance(res, dict)
    status = res.get("status") or {}
    assert isinstance(status, dict)
    assert status.get("success") is True
    assert res.get("data") == {"ok": True}


def test_nonjson_stdout(monkeypatch):
    def fake_run(cmd, input, stdout, stderr, timeout=None):
        return DummyCompleted(stdout=b"hello\n", stderr=b"err", returncode=2)

    monkeypatch.setattr(subprocess, "run", fake_run)
    pc = ProcessConnector({"command": ["/bin/false"]})
    res = pc.call(None)
    assert isinstance(res, dict)
    assert res["data"] == "hello\n"
    assert res["meta"]["stderr"] == "err"
    assert res["status"]["code"] == 2
    assert res["status"]["success"] is False


def test_pass_to_stdin(monkeypatch):
    captured = {}

    def fake_run(cmd, input, stdout, stderr, timeout=None):
        # capture the input passed to subprocess
        captured["input"] = input
        return DummyCompleted(stdout=b"res", stderr=b"", returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    pc = ProcessConnector({"command": ["/usr/bin/cat"], "pass_to": "stdin"})
    res = pc.call("payload-data")
    # ensure the connector passed input via stdin
    assert captured.get("input") == b"payload-data"
    assert res["data"] == "res"
    assert res["meta"]["returncode"] == 0
    assert res["status"]["success"] is True


def test_timeout_raises_runtimeerror(monkeypatch):
    def fake_run(cmd, input, stdout, stderr, timeout=None):
        raise subprocess.TimeoutExpired(cmd, 1)

    monkeypatch.setattr(subprocess, "run", fake_run)
    pc = ProcessConnector({"command": ["/bin/sleep"], "timeout": 1})
    res = pc.call(None)
    assert isinstance(res, dict)
    assert res["status"]["success"] is False
    assert res["status"]["notes"] == ["timeout"]
    assert res["meta"]["timeout"] is True
