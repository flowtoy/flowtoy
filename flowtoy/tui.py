from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import requests
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static

DEFAULT_STATUS_URL = "http://127.0.0.1:8005/status"

# Unicode icons for step states (simple symbols, all 1 character)
STATE_ICONS = {
    "pending": "◷",  # wait/clock
    "running": "▶",  # play button
    "succeeded": "✓",  # check mark
    "failed": "✗",  # cross mark
}


def format_start_time(ts: Optional[float]) -> str:
    """Format a start timestamp as HH:MM:SS.

    Args:
        ts: Unix timestamp

    Returns:
        Formatted time string or "-" if None
    """
    if ts is None:
        return "-"
    try:
        from datetime import datetime

        dt = datetime.fromtimestamp(ts)
        return dt.strftime("%H:%M:%S")
    except (ValueError, TypeError, OSError):
        return "-"


def format_duration(start_ts: Optional[float], end_ts: Optional[float]) -> str:
    """Format duration between start and end as +X.Xs.

    Args:
        start_ts: Start timestamp
        end_ts: End timestamp

    Returns:
        Formatted duration string like "+3.9s" or "-" if incomplete
    """
    if start_ts is None or end_ts is None:
        return "-"
    try:
        duration = end_ts - start_ts
        return f"+{duration:.1f}s"
    except (ValueError, TypeError):
        return "-"


class StatusTable(VerticalScroll):
    """Scrollable widget to display status information in a table."""

    status_data: reactive[Dict[str, Any]] = reactive({})

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Runner"

    def watch_status_data(self, status: Dict[str, Any]) -> None:
        """React to status data changes."""
        # Remove existing content
        self.remove_children()

        if not status or status.get("status") == "no-runner":
            self.mount(Static("No runner attached"))
            return

        if "_error" in status:
            error_msg = status.get("_error", "Unknown error")
            # Show a friendlier connection message
            if "Connection refused" in error_msg or "Max retries" in error_msg:
                self.mount(Static("Waiting for runner to start..."))
            else:
                self.mount(Static(f"Error: {error_msg}"))
            return

        run_id = status.get("run_id")
        total = status.get("total_steps")
        completed = status.get("completed_steps")
        running_count = status.get("running_count")
        current = status.get("current_step")

        # Build header with run info
        header_parts = []
        if run_id:
            header_parts.append(f"run {run_id}")
        if total is not None:
            header_parts.append(f"{completed}/{total} completed")
        if current:
            header_parts.append(f"current: {current}")
        elif completed == total:
            header_parts.append("current: -")
        header_parts.append(f"running: {running_count or 0}")

        header = " — ".join(header_parts)

        # Build table with compact state column using icons
        lines = [header, ""]
        lines.append(
            "Step                     ○ Started  Ended     Outputs          Notes"
        )
        lines.append("-" * 90)

        steps = status.get("steps") or {}
        for name in sorted(steps.keys()):
            info = steps[name]
            state = str(info.get("state") or "-")
            # Use icon for state, fallback to first 2 chars if no icon
            state_display = STATE_ICONS.get(state, state[:2])

            started_raw = info.get("started_at")
            ended_raw = info.get("ended_at")
            started = format_start_time(started_raw)
            ended = format_duration(started_raw, ended_raw)

            outputs = ", ".join(info.get("outputs") or []) or "-"
            notes = ", ".join(info.get("notes") or []) or "-"

            line = (
                f"{name:24} {state_display} {started:8} {ended:9} {outputs:16} {notes}"
            )
            lines.append(line)

        self.mount(Static("\n".join(lines)))


class OutputsPanel(VerticalScroll):
    """Scrollable widget to display outputs as JSON."""

    outputs_data: reactive[Dict[str, Any]] = reactive({})

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Outputs (Scrollable)"

    def watch_outputs_data(self, outputs: Dict[str, Any]) -> None:
        """React to outputs data changes."""
        if not outputs or "_error" in outputs:
            content = "(no outputs)"
        else:
            content = json.dumps(outputs, indent=2)

        # Update the content
        self.remove_children()
        self.mount(Static(content))


class LogsPanel(VerticalScroll):
    """Scrollable widget to display server logs."""

    logs_data: reactive[list] = reactive([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Server Logs (Scrollable)"

    def watch_logs_data(self, logs: list) -> None:
        """React to logs data changes."""
        if not logs:
            content = "(no logs)"
        else:
            # Show last 100 log entries
            content = "\n".join(list(logs)[-100:])

        # Update the content
        self.remove_children()
        self.mount(Static(content))


class FlowToyTUI(App):
    """Textual TUI for monitoring FlowtToy flow execution."""

    CSS = """
    Screen {
        layout: vertical;
    }

    StatusTable {
        height: auto;
        max-height: 15;
        border: solid $accent;
        padding: 1;
        margin-bottom: 1;
    }

    #main_container {
        height: 1fr;
        layout: vertical;
    }

    OutputsPanel {
        height: 1fr;
        border: solid $accent;
        padding: 1;
        margin-bottom: 1;
    }

    LogsPanel {
        height: 1fr;
        border: solid $accent;
        padding: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh Now"),
    ]

    def __init__(
        self,
        status_url: Optional[str] = None,
        poll_interval: float = 1.0,
        show_logs: bool = False,
        log_capture: Optional[Any] = None,
    ):
        super().__init__()
        self.status_url = (
            status_url or os.getenv("RUNNER_STATUS_URL") or DEFAULT_STATUS_URL
        )

        # allow RUNNER_STATUS_URL to be either the base runner URL or the full
        # /status path
        if self.status_url and not self.status_url.rstrip().endswith("/status"):
            self.status_url = self.status_url.rstrip("/") + "/status"

        # Derive outputs URL from status URL
        self.outputs_url = self.status_url.replace("/status", "/outputs")

        self.poll_interval = poll_interval
        self.show_logs = show_logs
        self.log_capture = log_capture

        # Store widget references
        self.status_widget = None
        self.outputs_widget = None
        self.logs_widget = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=False)

        self.status_widget = StatusTable()
        yield self.status_widget

        # Create a container for scrollable panels
        with Container(id="main_container"):
            self.outputs_widget = OutputsPanel()
            yield self.outputs_widget

            if self.show_logs and self.log_capture:
                self.logs_widget = LogsPanel()
                yield self.logs_widget

        yield Footer()

    def on_mount(self) -> None:
        """Start the update timer when app is mounted."""
        self.set_interval(self.poll_interval, self.update_data)
        # Do initial fetch immediately
        self.update_data()

    def update_data(self) -> None:
        """Fetch and update all data from the runner API."""
        # Fetch status
        status = self.fetch_status()
        if self.status_widget:
            self.status_widget.status_data = status

        # Fetch outputs
        outputs = self.fetch_outputs()
        if self.outputs_widget:
            self.outputs_widget.outputs_data = outputs

        # Update logs if enabled
        if self.show_logs and self.log_capture and self.logs_widget:
            self.logs_widget.logs_data = list(self.log_capture.records)

    def fetch_status(self, timeout: float = 3.0) -> Dict[str, Any]:
        """Fetch status from the runner API."""
        try:
            r = requests.get(self.status_url, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"_error": str(e)}

    def fetch_outputs(self, timeout: float = 3.0) -> Dict[str, Any]:
        """Fetch outputs from the runner API."""
        try:
            r = requests.get(self.outputs_url, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"_error": str(e)}

    def action_refresh(self) -> None:
        """Manual refresh action."""
        self.update_data()


def run_tui(
    status_url: Optional[str] = None,
    poll_interval: float = 1.0,
    show_logs: bool = False,
    log_capture: Optional[Any] = None,
    max_output_lines: int = 20,  # Kept for API compatibility but not used with Textual
) -> None:
    """Run the terminal UI.

    Args:
        status_url: URL of the status endpoint to poll
        poll_interval: How often to poll for updates (seconds)
        show_logs: Whether to display server logs panel
        log_capture: Optional LogCapture handler to display logs from
        max_output_lines: Ignored (kept for API compatibility)
    """
    app = FlowToyTUI(
        status_url=status_url,
        poll_interval=poll_interval,
        show_logs=show_logs,
        log_capture=log_capture,
    )
    app.run()


if __name__ == "__main__":
    run_tui()
