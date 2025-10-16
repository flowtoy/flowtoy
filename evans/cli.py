from __future__ import annotations

import json
import logging
import threading
from typing import List, Optional, Tuple

import typer
import uvicorn

from .api import app, attach_runner
from .config import load_yaml_files
from .runner import LocalRunner
from .runner_api import serve_runner_api_in_thread
from .terminal_ui import run_terminal_ui
from .ui_server import app as ui_app

cli = typer.Typer(
    name="evans", context_settings={"help_option_names": ["-h", "--help"]}
)

HELP_TEXT = """
evans CLI

Commands:
  run [CONFIG...]       Run a flow from YAML config files
  serve [CONFIG...]     Serve the status API and run the flow at startup
  serve-ui [CONFIG...]  Serve the UI and run the flow in background

Options:
  -j, --json            Print outputs as JSON
  -o, --output-file     Write JSON outputs to file
  -q, --quiet           Suppress stdout printing
  -h, --help            Show this help message

Examples:
  evans run flow.yaml
  evans run flow.yaml -j -o outputs.json
"""


@cli.command("help")
def help_cmd():
    """Show this CLI help."""
    typer.echo(HELP_TEXT)


@cli.command("h")
def h_cmd():
    """Alias for help."""
    typer.echo(HELP_TEXT)


def run_flow(config_paths: List[str]) -> Tuple[dict, object]:
    """Programmatic helper: load config, run the flow, and return (flows, status).

    Returns a tuple (flows_dict, status_object).
    """
    cfg = load_yaml_files(config_paths)
    r = LocalRunner(cfg)
    r.run()
    return r.flows, r.status


run_as_json_opt = typer.Option(False, "--json", "-j", help="Print outputs as JSON")
run_output_file_opt = typer.Option(
    None, "--output-file", "-o", help="Write JSON outputs to file"
)
run_quiet_opt = typer.Option(False, "--quiet", "-q", help="Suppress stdout printing")
run_status_port_opt = typer.Option(
    None,
    "--status-port",
    help=(
        "Start an HTTP status server on this port so external UIs can poll "
        "runner state"
    ),
)
run_max_workers_opt = typer.Option(
    None, "--max-workers", help="Maximum number of worker threads for the runner"
)


@cli.command()
def run(
    config: List[str],
    as_json: bool = run_as_json_opt,
    output_file: Optional[str] = run_output_file_opt,
    quiet: bool = run_quiet_opt,
    status_port: Optional[int] = run_status_port_opt,
    max_workers: Optional[int] = run_max_workers_opt,
):
    """Run a flow from one or more YAML config files."""
    # create the runner, attach it so the API exposes the live instance, then run
    cfg = load_yaml_files(config)
    logger = logging.getLogger(__name__)
    # print a short summary to stdout so users can see what was loaded
    flow_steps = cfg.get("flow") or []
    logger.info(f"loaded config from {config}, flow steps: {len(flow_steps)}")
    r = LocalRunner(cfg)
    if max_workers:
        r._max_workers = int(max_workers)
    attach_runner(r)

    status_host = "127.0.0.1"
    # optionally start a simple runner status server the UI can poll
    if status_port:
        # enable logging so connector diagnostics are visible
        logging.basicConfig(level=logging.INFO)
        serve_runner_api_in_thread(r, host=status_host, port=status_port)

    r.run()
    flows = r.flows

    if not quiet:
        logger.info("run finished. outputs:")

    if as_json or output_file:
        payload = json.dumps(flows, indent=2)
        if output_file:
            with open(output_file, "w") as f:
                f.write(payload)
            if not quiet:
                logger.info(f"wrote outputs to {output_file}")
        else:
            print(payload)
    else:
        if not quiet:
            print(flows)
    # If we started a status server, keep the process alive so external UIs can poll it
    if status_port:
        try:
            if not quiet:
                logger.info(
                    "status server running on http://%s:%d (press Ctrl-C to exit)",
                    status_host,
                    status_port,
                )
            # block until interrupted
            while True:
                import time

                time.sleep(1)
        except KeyboardInterrupt:
            if not quiet:
                logger.info("shutting down")


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
def tui(
    status_url: Optional[str] = typer.Option(
        None,
        "--status-url",
        help="Runner status endpoint URL (e.g. http://127.0.0.1:8005/status)",
    )
):
    """Run the terminal UI that polls a runner status endpoint."""
    # If not provided, `run_terminal_ui` will read `RUNNER_STATUS_URL` env var
    run_terminal_ui(status_url=status_url)


@cli.command()
def serve_ui(
    config: List[str],
    host: str = "127.0.0.1",
    port: int = 8000,
    max_workers: Optional[int] = typer.Option(
        None, "--max-workers", help="Maximum number of worker threads for the runner"
    ),
):
    """Serve the UI (static) and status endpoints and run the flow in background.

    This attaches the runner to the core API so the UI can poll /status and /outputs.
    """
    # enable basic INFO logging so connector logs are visible in the demo
    logging.basicConfig(level=logging.INFO)
    cfg = load_yaml_files(config)
    r = LocalRunner(cfg)
    if max_workers:
        r._max_workers = int(max_workers)
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
