from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import requests
from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

DEFAULT_STATUS_URL = "http://127.0.0.1:8005/status"


def fetch_status(url: str, timeout: float = 3.0) -> Dict[str, Any]:
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"_error": str(e)}


def render_status_panel(status: Dict[str, Any]) -> Panel:
    if not status or status.get("status") == "no-runner":
        return Panel("No runner attached", title="Runner")

    run_id = status.get("run_id")
    total = status.get("total_steps")
    completed = status.get("completed_steps")
    running_count = status.get("running_count")
    current = status.get("current_step")
    header = (
        f"run {run_id} — {completed}/{total} completed — "
        f"current: {current or '-'} — running: {running_count or 0}"
    )

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Step", style="cyan", no_wrap=True)
    table.add_column("State", style="yellow")
    table.add_column("Started", style="green")
    table.add_column("Ended", style="red")
    table.add_column("Outputs", style="white")
    table.add_column("Notes", style="bright_black")

    steps = status.get("steps") or {}
    for name in sorted(steps.keys()):
        info = steps[name]
        state = str(info.get("state") or "-")
        started = str(info.get("started_at") or "-")
        ended = str(info.get("ended_at") or "-")
        outputs = ", ".join(info.get("outputs") or []) or "-"
        notes = ", ".join(info.get("notes") or []) or "-"
        table.add_row(name, state, started, ended, outputs, notes)

    panel = Panel(Align.left(table), title=header)
    return panel


def run_terminal_ui(
    status_url: Optional[str] = None, poll_interval: float = 1.0
) -> None:
    console = Console()
    url = status_url or os.getenv("RUNNER_STATUS_URL") or DEFAULT_STATUS_URL
    # allow RUNNER_STATUS_URL to be either the base runner URL or the full /status path
    if url and not url.rstrip().endswith("/status"):
        url = url.rstrip("/") + "/status"

    console.print(f"Terminal UI polling: [bold]{url}[/bold] (press Ctrl-C to quit)")

    with Live(console=console, refresh_per_second=4) as live:
        try:
            while True:
                status = fetch_status(url)
                if status is None:
                    status = {"_error": "no data"}
                if "_error" in status:
                    live.update(
                        Panel(
                            f"Error fetching status: {status.get('_error')}",
                            title="Runner",
                        )
                    )
                else:
                    panel = render_status_panel(status)
                    live.update(panel)
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            console.print("\nExiting terminal UI")


if __name__ == "__main__":
    run_terminal_ui()
