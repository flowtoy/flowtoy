from __future__ import annotations

import threading
from typing import List, Optional, Tuple
import json

import typer
import uvicorn
import logging

from .config import load_yaml_files
from .runner import LocalRunner
from .api import attach_runner, app
from .ui_server import app as ui_app
from .runner_api import serve_runner_api_in_thread

cli = typer.Typer()


def run_flow(config_paths: List[str]) -> Tuple[dict, object]:
    """Programmatic helper: load config, run the flow, and return (flows, status).

    Returns a tuple (flows_dict, status_object).
    """
    cfg = load_yaml_files(config_paths)
    r = LocalRunner(cfg)
    r.run()
    return r.flows, r.status


@cli.command()
def run(
    config: List[str],
    as_json: bool = typer.Option(False, "--json", "-j", help="Print outputs as JSON"),
    output_file: Optional[str] = typer.Option(
        None, "--output-file", "-o", help="Write JSON outputs to file"
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress stdout printing"),
    status_port: Optional[int] = typer.Option(
        None,
        "--status-port",
        help="Start an HTTP status server on this port so external UIs can poll runner state",
    ),
):
    """Run a flow from one or more YAML config files."""
    # create the runner, attach it so the API exposes the live instance, then run
    cfg = load_yaml_files(config)
    # print a short summary to stdout so users can see what was loaded
    flow_steps = cfg.get("flow") or []
    print(f"loaded config from {config}, flow steps: {len(flow_steps)}")
    r = LocalRunner(cfg)
    attach_runner(r)

    # optionally start a simple runner status server the UI can poll
    if status_port:
        # enable logging so connector diagnostics are visible
        logging.basicConfig(level=logging.INFO)
        serve_runner_api_in_thread(r, host="127.0.0.1", port=status_port)

    r.run()
    flows = r.flows
    status = r.status

    if not quiet:
        print("run finished. outputs:")

    if as_json or output_file:
        payload = json.dumps(flows, indent=2)
        if output_file:
            with open(output_file, "w") as f:
                f.write(payload)
            if not quiet:
                print(f"wrote outputs to {output_file}")
        else:
            print(payload)
    else:
        if not quiet:
            print(flows)
    # If we started a status server, keep the process alive so external UIs can poll it
    if status_port:
        try:
            if not quiet:
                print(
                    f"status server running on http://127.0.0.1:{status_port} (press Ctrl-C to exit)"
                )
            # block until interrupted
            while True:
                import time

                time.sleep(1)
        except KeyboardInterrupt:
            if not quiet:
                print("shutting down")


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


@cli.command()
def serve_ui(config: List[str], host: str = "127.0.0.1", port: int = 8000):
    """Serve the UI (static) and status endpoints and run the flow in background.

    This attaches the runner to the core API so the UI can poll /status and /outputs.
    """
    # enable basic INFO logging so connector logs are visible in the demo
    logging.basicConfig(level=logging.INFO)
    cfg = load_yaml_files(config)
    r = LocalRunner(cfg)
    attach_runner(r)
    # if STATUS_PORT env var or option is set via CLI later, we could also start
    # a standalone runner status server; keep it simple for now and attach to API

    def _run():
        r.run()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    uvicorn.run(ui_app, host=host, port=port)


if __name__ == "__main__":
    main()
