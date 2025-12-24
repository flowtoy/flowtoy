---
title: Run UI and Runner Separately
description: Run the web UI and flow runner in separate processes for distributed monitoring
---

# Run UI and Runner Separately

This guide shows how to run the web UI and flow runner as separate processes. This is useful for:

- Monitoring flows running on remote servers
- Running multiple UI instances for the same flow
- Separating concerns in production deployments
- Debugging UI and runner independently

## Architecture Overview

The flowtoy architecture supports separation between the UI and runner:

1. **Runner** - Executes the flow and exposes a status API (HTTP endpoints for `/status` and `/outputs`)
2. **UI** - Displays flow progress by polling the runner's status API
3. **Connection** - The UI uses `RUNNER_STATUS_URL` environment variable to locate the runner

The UI and runner can run:
- On different ports on the same machine
- On different machines entirely
- At different times (runner first, UI later)

## Method 1: Two Terminals (Same Machine)

This is the simplest approach for local development.

### Terminal 1: Start the Runner with Status API

```bash
flowtoy run flow.yaml --status-port 8005
```

This runs your flow and starts a status API server on port 8005. The endpoints available are:
- `http://127.0.0.1:8005/status` - Flow execution status
- `http://127.0.0.1:8005/outputs` - Step output values

### Terminal 2: Start the Web UI

```bash
export RUNNER_STATUS_URL="http://127.0.0.1:8005"
flowtoy webui --status-url http://127.0.0.1:8005
```

Open `http://127.0.0.1:8000` in your browser. The UI polls the runner's status API and displays:
- Real-time step progress
- Step outputs as they complete
- Error messages and diagnostics
- Overall flow timing

### Port Independence

The UI port and runner status port are independent:
- Runner status API: `--status-port 8005`
- UI server: `--port 8000` (default)

Just ensure `RUNNER_STATUS_URL` points to the runner's status server.

## Method 2: Remote Monitoring

Monitor a flow running on a remote server.

### On the Server

Start the runner with status API exposed:

```bash
# Bind to all interfaces so remote clients can connect
flowtoy run flow.yaml --status-port 8005
```

If running on a server with a firewall, ensure port 8005 is accessible.

### On Your Laptop

Start the UI to monitor the remote flow:

```bash
flowtoy webui --status-url http://server-hostname:8005
```

Open `http://127.0.0.1:8000` in your browser to monitor the remote flow.

## Method 3: Programmatic Setup with Python

For full control, use Python to run the UI and runner programmatically.

Create `run_separate.py`:

```python
"""Run flow with separate UI server in threaded setup."""
import threading
import time
import os
import sys
import uvicorn

from flowtoy.runner import LocalRunner
from flowtoy.runner_api import serve_runner_api_in_thread
from flowtoy.config import load_yaml_files

# Import the web UI app
from flowtoy.webui import app as ui_app


def run_ui_in_thread(port=8006):
    """Start uvicorn for the UI app."""
    uvicorn.run(ui_app, host="127.0.0.1", port=port, log_level="info")


def main():
    # Load and create runner
    config = load_yaml_files(["flow.yaml"])
    runner = LocalRunner(config)

    # Start runner API on port 8005
    print("Starting runner API on http://127.0.0.1:8005")
    serve_runner_api_in_thread(runner, host="127.0.0.1", port=8005)

    # Configure UI to proxy to runner status API
    os.environ["RUNNER_STATUS_URL"] = "http://127.0.0.1:8005"

    # Start UI server on port 8006
    print("Starting UI server on http://127.0.0.1:8006")
    ui_thread = threading.Thread(target=run_ui_in_thread, kwargs={"port": 8006}, daemon=True)
    ui_thread.start()

    # Wait for servers to start
    time.sleep(1)

    # Run the flow
    print("Running flow")
    runner.run()
    print("Flow completed")

    # Keep servers running for viewing results
    print("UI available at http://127.0.0.1:8006")
    print("Press Ctrl-C to exit")

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down")


if __name__ == "__main__":
    main()
```

Run it:

```bash
python run_separate.py
```

This gives you full programmatic control over:
- Port selection
- Threading behavior
- Error handling
- Lifecycle management

## Method 4: Terminal UI Instead of Web UI

You can also use the terminal UI (TUI) instead of the web UI.

### Terminal 1: Run the Flow

```bash
flowtoy run flow.yaml --status-port 8005
```

### Terminal 2: Monitor with TUI

```bash
export RUNNER_STATUS_URL="http://127.0.0.1:8005"
flowtoy tui --status-url http://127.0.0.1:8005
```

The TUI displays a live table of step states in your terminal.

## Example Flow

Save this as `university-directory.yaml` to test with:

```{literalinclude} ../how-to-files/university-directory.yaml
:language: yaml
```

This flow demonstrates parallel execution with multiple dependent steps, making it ideal for testing the monitoring UI.

## Troubleshooting

### UI Shows "No runner attached"

**Problem**: The UI can't connect to the runner status API.

**Solutions**:
- Verify `RUNNER_STATUS_URL` is set correctly
- Check the runner is running with `--status-port`
- Ensure no firewall is blocking the port
- Test the status endpoint manually: `curl http://127.0.0.1:8005/status`

### Ports Already in Use

**Problem**: `Address already in use` error.

**Solutions**:
- Use different ports: `--status-port 8015` and `--port 8016`
- Find and kill the process using the port: `lsof -ti:8005 | xargs kill`

### RUNNER_STATUS_URL Not Working

**Problem**: UI doesn't pick up the environment variable.

**Solutions**:
- Set it before starting the UI: `export RUNNER_STATUS_URL=...` then run `flowtoy webui`
- Or pass it directly: `flowtoy webui --status-url http://...`

## Use Cases

### Development

Run the flow in one terminal while iterating on UI improvements in another.

### Production Monitoring

Deploy the runner on a server and run the UI locally to monitor production flows without SSH access.

### Multiple Viewers

Start multiple UI instances (on different ports) to view the same flow from different browsers or machines.

### CI/CD Integration

Run the flow with `--status-port` in CI, poll the status API to wait for completion, then fetch outputs.

## Next Steps

- [Monitor Flow Execution](monitor-flow-execution.md) - All monitoring approaches
- [Python API Reference](../reference/api/programmatic.md) - `serve_runner_api_in_thread()` details
- [Status API Reference](../reference/api/status.md) - Status endpoint documentation
