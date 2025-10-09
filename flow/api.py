from __future__ import annotations

from fastapi import FastAPI
from typing import Any, Optional
import threading

app = FastAPI()

# runtime-bound runner will be attached here
_RUNNER: Optional[Any] = None
_RUNNER_LOCK = threading.RLock()


def attach_runner(runner: Any):
    """Attach the given runner instance so the API can expose its live state.

    This stores a reference under a lock to make concurrent reads safer.
    """
    global _RUNNER
    with _RUNNER_LOCK:
        _RUNNER = runner


def _get_runner() -> Optional[Any]:
    with _RUNNER_LOCK:
        return _RUNNER


@app.get("/status")
def status():
    r = _get_runner()
    if r is None:
        return {"status": "no-runner"}
    return {
        "run_id": r.status.run_id,
        "started_at": r.status.started_at,
        "ended_at": r.status.ended_at,
        "steps": {
            k: {"state": v.state, "notes": ([v.error] if v.error else [])}
            for k, v in r.status.steps.items()
        },
    }


@app.get("/outputs")
def outputs():
    r = _get_runner()
    if r is None:
        return {}
    # return a shallow copy to avoid concurrent mutation during JSON serialization
    return dict(r.flows)
