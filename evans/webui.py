import os
from pathlib import Path

import requests
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from . import api as core_api

app = FastAPI()

# static files served under /static so dynamic endpoints like /status are not
# shadowed by the static mount.
ui_path = Path(__file__).resolve().parents[1] / "ui"
if ui_path.exists():
    app.mount(
        "/static", StaticFiles(directory=str(ui_path), html=True), name="ui_static"
    )


@app.get("/")
def index():
    idx = ui_path / "index.html"
    if idx.exists():
        return FileResponse(str(idx))
    return {"message": "UI not available"}


@app.get("/status")
def status():
    # if RUNNER_STATUS_URL is set, proxy requests to that runner status server
    runner_url = os.getenv("RUNNER_STATUS_URL")
    if runner_url:
        try:
            target = runner_url.rstrip("/") + "/status"
            r = requests.get(target, timeout=5)
            try:
                return JSONResponse(r.json(), status_code=r.status_code)
            except Exception:
                return Response(
                    r.text, status_code=r.status_code, media_type="text/plain"
                )
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=502)
    return core_api.status()


@app.get("/outputs")
def outputs():
    runner_url = os.getenv("RUNNER_STATUS_URL")
    if runner_url:
        try:
            target = runner_url.rstrip("/") + "/outputs"
            r = requests.get(target, timeout=5)
            try:
                return JSONResponse(r.json(), status_code=r.status_code)
            except Exception:
                return Response(
                    r.text, status_code=r.status_code, media_type="text/plain"
                )
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=502)
    return core_api.outputs()
