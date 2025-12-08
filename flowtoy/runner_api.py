from __future__ import annotations

import logging
import threading
from collections import deque
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse


class LogCapture(logging.Handler):
    """Logging handler that captures log records in a deque."""

    def __init__(self, maxlen: int = 100):
        super().__init__()
        self.records = deque(maxlen=maxlen)

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            self.records.append(msg)
        except Exception:
            self.handleError(record)


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
    runner: Any,
    host: str = "127.0.0.1",
    port: int = 0,
    log_level: str = "info",
    log_capture: Optional[LogCapture] = None,
) -> threading.Thread:
    """Start a uvicorn server for the given runner in a daemon thread.

    Args:
        runner: The runner instance to expose via the API
        host: Host to bind to (default: 127.0.0.1)
        port: Port to bind to (default: 0 for auto-assignment)
        log_level: Uvicorn log level (default: "info", use "error" or
          "critical" to suppress startup messages)
        log_capture: Optional LogCapture handler to capture uvicorn logs
          (useful for TUI display)

    Returns the Thread object. If port==0 uvicorn will pick a free port but
    we cannot easily retrieve it here; prefer specifying a port.
    """
    app = create_app_for_runner(runner)

    def _serve():
        # If log capture is provided, configure uvicorn logging to use it
        if log_capture:
            # Configure uvicorn's loggers to use our capture handler
            uvicorn_logger = logging.getLogger("uvicorn")
            uvicorn_access_logger = logging.getLogger("uvicorn.access")

            # Set level and add handler
            uvicorn_logger.setLevel(getattr(logging, log_level.upper()))
            uvicorn_access_logger.setLevel(getattr(logging, log_level.upper()))

            # Remove existing handlers to avoid duplication
            uvicorn_logger.handlers.clear()
            uvicorn_access_logger.handlers.clear()

            # Add our capture handler
            uvicorn_logger.addHandler(log_capture)
            uvicorn_access_logger.addHandler(log_capture)

            # Run with log_config=None to use our configured loggers
            uvicorn.run(app, host=host, port=port, log_level=log_level, log_config=None)
        else:
            uvicorn.run(app, host=host, port=port, log_level=log_level)

    t = threading.Thread(target=_serve, daemon=True)
    t.start()
    return t
