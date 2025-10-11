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
    # build richer per-step info: include timestamps and available output keys
    steps_info = {}
    for k, v in r.status.steps.items():
        outputs = {}
        try:
            # flows may be mutated concurrently; guard with getattr checks
            outputs = (
                list(r.flows.get(k, {}).keys())
                if getattr(r, "flows", None) is not None
                else []
            )
        except Exception:
            outputs = []
        steps_info[k] = {
            "state": v.state,
            "started_at": v.started_at,
            "ended_at": v.ended_at,
            "notes": ([v.error] if v.error else []),
            "outputs": outputs,
        }

    # determine current running step (first with state == 'running')
    current_step = None
    for name, info in steps_info.items():
        if info.get("state") == "running":
            current_step = name
            break

    total = len(steps_info)
    completed = sum(
        1 for s in steps_info.values() if s.get("state") in ("succeeded", "failed")
    )

    return {
        "run_id": r.status.run_id,
        "started_at": r.status.started_at,
        "ended_at": r.status.ended_at,
        "total_steps": total,
        "completed_steps": completed,
        "current_step": current_step,
        "steps": steps_info,
    }


@app.get("/outputs")
def outputs():
    r = _get_runner()
    if r is None:
        return {}
    # return a shallow copy to avoid concurrent mutation during JSON serialization
    return dict(r.flows)
