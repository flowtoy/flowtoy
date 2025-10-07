from __future__ import annotations

from fastapi import FastAPI
from typing import Any

app = FastAPI()

# runtime-bound runner will be attached here
_RUNNER: Any = None


def attach_runner(runner):
    global _RUNNER
    _RUNNER = runner


@app.get("/status")
def status():
    if _RUNNER is None:
        return {"status": "no-runner"}
    return {
        "run_id": _RUNNER.status.run_id,
        "started_at": _RUNNER.status.started_at,
        "ended_at": _RUNNER.status.ended_at,
        "steps": {k: {"state": v.state, "notes": ([v.error] if v.error else [])} for k, v in _RUNNER.status.steps.items()},
    }


@app.get("/outputs")
def outputs():
    if _RUNNER is None:
        return {}
    return _RUNNER.flows
