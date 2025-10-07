from __future__ import annotations

import threading
from typing import List

import typer
import uvicorn

from .config import load_yaml_files
from .runner import LocalRunner
from .api import attach_runner, app

cli = typer.Typer()


@cli.command()
def run(config: List[str]):
    """Run a flow from one or more YAML config files."""
    cfg = load_yaml_files(config)
    r = LocalRunner(cfg)
    attach_runner(r)
    r.run()
    print("run finished. outputs:")
    print(r.flows)


@cli.command()
def serve(config: List[str], host: str = "127.0.0.1", port: int = 8000):
    """Serve the status API and run the flow once at startup."""
    cfg = load_yaml_files(config)
    r = LocalRunner(cfg)
    attach_runner(r)

    def _run():
        r.run()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    uvicorn.run(app, host=host, port=port)


def main():
    cli()
