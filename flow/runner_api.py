from __future__ import annotations

from typing import Any
import threading
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn


def create_app_for_runner(runner: Any) -> FastAPI:
    app = FastAPI()

    @app.get("/status")
    def status():
        # delegate to the runner's status snapshot
        try:
            r = runner
            if r is None:
                return JSONResponse({"status": "no-runner"})

            steps_info = {}
            for k, v in r.status.steps.items():
                outputs = []
                try:
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

            current_step = None
            for name, info in steps_info.items():
                if info.get("state") == "running":
                    current_step = name
                    break

            total = len(steps_info)
            completed = sum(
                1
                for s in steps_info.values()
                if s.get("state") in ("succeeded", "failed")
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
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.get("/outputs")
    def outputs():
        try:
            r = runner
            if r is None:
                return {}
            return dict(r.flows)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    return app


def serve_runner_api_in_thread(
    runner: Any, host: str = "127.0.0.1", port: int = 0
) -> threading.Thread:
    """Start a uvicorn server for the given runner in a daemon thread.

    Returns the Thread object. If port==0 uvicorn will pick a free port but
    we cannot easily retrieve it here; prefer specifying a port.
    """
    app = create_app_for_runner(runner)

    def _serve():
        uvicorn.run(app, host=host, port=port, log_level="info")

    t = threading.Thread(target=_serve, daemon=True)
    t.start()
    return t
