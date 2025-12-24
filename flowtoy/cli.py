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
from .tui import run_tui
from .webui import app as ui_app

cli = typer.Typer(
    name="flowtoy", context_settings={"help_option_names": ["-h", "--help"]}
)

HELP_TEXT = """
flowtoy CLI

Commands:
  run [CONFIG...]       Run a flow from YAML config files
  serve [CONFIG...]     Serve the status API and run the flow at startup
  webui [CONFIG...]  Serve the UI and run the flow in background

Options:
  -j, --json            Print outputs as JSON
  -o, --output-file     Write JSON outputs to file
  -q, --quiet           Suppress stdout printing
  -h, --help            Show this help message

Examples:
  flowtoy run flow.yaml
  flowtoy run flow.yaml -j -o outputs.json
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
        "Start an HTTP status server on this port so external UIs can poll runner state"
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
        # enable logging so provider diagnostics are visible
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
    config: Optional[List[str]] = typer.Argument(
        None, help="Flow config files to run and monitor"
    ),
    status_url: Optional[str] = typer.Option(
        None, "--status-url", help="Monitor a remote runner status endpoint"
    ),
    max_workers: Optional[int] = typer.Option(
        None, "--max-workers", help="Maximum number of worker threads for the runner"
    ),
    show_logs: bool = typer.Option(
        False, "--show-logs", help="Display server logs in the TUI"
    ),
):
    """Run the terminal UI to monitor flow execution.

    Two modes:
    1. All-in-one: flowtoy tui flow.yaml (runs flow and monitors it)
    2. External: flowtoy tui --status-url http://... (monitors remote flow)
    """
    # Mode 1: All-in-one - run flow and monitor it
    if config:
        if status_url:
            typer.echo(
                "Error: Cannot specify both config files and --status-url", err=True
            )
            raise typer.Exit(1)

        # Find available port
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            s.listen(1)
            port = s.getsockname()[1]

        # Load config and start runner
        cfg = load_yaml_files(config)
        r = LocalRunner(cfg)
        if max_workers:
            r._max_workers = int(max_workers)
        attach_runner(r)

        # Create log capture if --show-logs is enabled
        from .runner_api import LogCapture

        log_capture = LogCapture(maxlen=100) if show_logs else None

        # Start status server in background (capture logs if requested)
        if log_capture:
            serve_runner_api_in_thread(
                r,
                host="127.0.0.1",
                port=port,
                log_level="info",
                log_capture=log_capture,
            )
        else:
            serve_runner_api_in_thread(
                r, host="127.0.0.1", port=port, log_level="error"
            )

        # Run flow in background thread
        def _run():
            r.run()

        t = threading.Thread(target=_run, daemon=True)
        t.start()

        # Run TUI monitoring the local status server
        run_tui(
            status_url=f"http://127.0.0.1:{port}/status",
            show_logs=show_logs,
            log_capture=log_capture,
        )

    # Mode 2: External monitoring
    else:
        if not status_url:
            typer.echo(
                "Error: Must specify either config files or --status-url", err=True
            )
            raise typer.Exit(1)

        if show_logs:
            typer.echo(
                "Warning: --show-logs only works in all-in-one mode, with config files",
                err=True,
            )

        run_tui(status_url=status_url)


@cli.command()
def webui(
    config: Optional[List[str]] = typer.Argument(
        None, help="Flow config files to run and monitor"
    ),
    host: str = "127.0.0.1",
    port: int = 8000,
    status_url: Optional[str] = typer.Option(
        None,
        "--status-url",
        help="Monitor a remote runner status endpoint instead of running a flow",
    ),
    max_workers: Optional[int] = typer.Option(
        None, "--max-workers", help="Maximum number of worker threads for the runner"
    ),
):
    """Serve the web UI to monitor flow execution.

    Two modes:
    1. All-in-one: flowtoy webui flow.yaml (runs flow and serves UI)
    2. External: flowtoy webui --status-url http://... (serves UI for remote flow)
    """
    # Mode 1: External monitoring - serve UI for remote flow
    if status_url:
        if config:
            typer.echo(
                "Error: Cannot specify both config files and --status-url", err=True
            )
            raise typer.Exit(1)

        # Set environment variable for webui app to proxy requests
        import os

        os.environ["RUNNER_STATUS_URL"] = status_url

        uvicorn.run(ui_app, host=host, port=port)

    # Mode 2: All-in-one - run flow and serve UI
    else:
        if not config:
            typer.echo(
                "Error: Must specify either config files or --status-url", err=True
            )
            raise typer.Exit(1)

        # enable basic INFO logging so provider logs are visible in the demo
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
