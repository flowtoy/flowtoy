from __future__ import annotations

import threading
from typing import List, Optional, Tuple
import json

import typer
import uvicorn

from .config import load_yaml_files
from .runner import LocalRunner
from .api import attach_runner, app

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
):
    """Run a flow from one or more YAML config files."""
    # create the runner, attach it so the API exposes the live instance, then run
    cfg = load_yaml_files(config)
    r = LocalRunner(cfg)
    attach_runner(r)
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
