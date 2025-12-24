---
title: Use the Python API
description: Run flows programmatically from Python code
---

# Use the Python API

This guide shows how to run flowtoy flows from Python code instead of using the CLI.

## Basic Usage

The simplest way to run a flow is using the `run_flow()` function:

```python
from flowtoy.cli import run_flow

# Run flow and get results
flows, status = run_flow(["flow.yaml"])

# Access outputs
user_count = flows["fetch_users"]["count"]
print(f"Found {user_count} users")
```

The function returns:
- `flows` - Dictionary of step outputs: `{step_name: {output_name: value}}`
- `status` - Execution metadata (run ID, timestamps, step states)

## Multiple Configuration Files

Pass multiple YAML files to merge configurations:

```python
flows, status = run_flow(["base.yaml", "dev-overrides.yaml"])
```

Later files override earlier ones (same as CLI behavior).

## Using LocalRunner

For more control, use the `LocalRunner` class directly:

```python
from flowtoy.config import load_yaml_files
from flowtoy.runner import LocalRunner

# Load configuration
config = load_yaml_files(["flow.yaml"])

# Create and run
runner = LocalRunner(config)
runner.run()

# Access results
for step_name, outputs in runner.flows.items():
    print(f"{step_name}: {outputs}")
```

## Checking Execution Status

Inspect the status object to check if steps succeeded:

```python
flows, status = run_flow(["flow.yaml"])

# Check overall timing
duration = status.ended_at - status.started_at
print(f"Flow completed in {duration:.2f} seconds")

# Check individual steps
for step_name, step_status in status.steps.items():
    if step_status.state == "succeeded":
        step_duration = step_status.ended_at - step_status.started_at
        print(f"✓ {step_name} ({step_duration:.2f}s)")
    elif step_status.state == "failed":
        print(f"✗ {step_name}: {step_status.error}")
```

## Error Handling

Handle flow failures gracefully:

```python
from flowtoy.cli import run_flow

try:
    flows, status = run_flow(["flow.yaml"])

    # Check for step failures
    failed_steps = [
        name for name, step in status.steps.items()
        if step.state == "failed"
    ]

    if failed_steps:
        print(f"Steps failed: {', '.join(failed_steps)}")
        for name in failed_steps:
            print(f"  {name}: {status.steps[name].error}")
        exit(1)

    # Process outputs
    print("All steps succeeded")
    print(f"Results: {flows}")

except Exception as e:
    print(f"Flow execution failed: {e}")
    exit(1)
```

## Building Configuration Programmatically

Instead of loading YAML files, build the configuration dictionary directly:

```python
from flowtoy.runner import LocalRunner

config = {
    "sources": {
        "api": {
            "type": "rest",
            "configuration": {
                "base_url": "https://api.example.com"
            }
        }
    },
    "flow": [
        {
            "name": "fetch_data",
            "source": "api",
            "input": {
                "type": "parameter",
                "value": "/users"
            },
            "output": [
                {"name": "users", "type": "json"}
            ]
        }
    ]
}

runner = LocalRunner(config)
runner.run()

users = runner.flows["fetch_data"]["users"]
print(f"Fetched {len(users)} users")
```

## Monitoring During Execution

Run the flow in a background thread and monitor progress:

```python
import threading
import time
from flowtoy.runner import LocalRunner
from flowtoy.config import load_yaml_files

config = load_yaml_files(["flow.yaml"])
runner = LocalRunner(config)

# Run in background
def run_flow():
    runner.run()

thread = threading.Thread(target=run_flow)
thread.start()

# Monitor progress
while thread.is_alive():
    completed = sum(
        1 for s in runner.status.steps.values()
        if s.state in ("succeeded", "failed")
    )
    total = len(runner.status.steps)
    print(f"Progress: {completed}/{total}")
    time.sleep(1)

thread.join()
print("Flow completed")
```

## Serving the Status API

Combine programmatic execution with the HTTP status API:

```python
from flowtoy.runner import LocalRunner
from flowtoy.runner_api import serve_runner_api_in_thread
from flowtoy.config import load_yaml_files

# Create runner
config = load_yaml_files(["flow.yaml"])
runner = LocalRunner(config)

# Start status API server
api_thread = serve_runner_api_in_thread(runner, port=8080)
print("Status API available at http://localhost:8080/status")

# Run flow
runner.run()

print("Flow completed. Status API still available.")
print("Press Ctrl-C to exit.")

# Keep server running
try:
    api_thread.join()
except KeyboardInterrupt:
    print("Shutting down.")
```

While the flow runs, you can:
- Poll `http://localhost:8080/status` for progress
- Fetch outputs from `http://localhost:8080/outputs`
- Use `flowtoy tui --status-url http://localhost:8080` to monitor with the TUI

See the [Status API reference](/reference/api/status) for endpoint details.

## Running UI and Runner Separately

For more advanced setups, you can run the web UI and runner as separate processes with full programmatic control.

This is useful for:
- Distributed monitoring (UI on laptop, runner on server)
- Running multiple UI instances for the same flow
- Custom threading and lifecycle management

### Basic Setup

```python
import threading
import time
import os
import uvicorn

from flowtoy.runner import LocalRunner
from flowtoy.runner_api import serve_runner_api_in_thread
from flowtoy.config import load_yaml_files
from flowtoy.webui import app as ui_app


def run_ui_in_thread(port=8006):
    """Start uvicorn for the web UI app."""
    uvicorn.run(ui_app, host="127.0.0.1", port=port, log_level="info")


# Load configuration
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
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Shutting down")
```

The key points:
1. **Runner API** - Started with `serve_runner_api_in_thread()` on its own port
2. **UI Server** - Started with `uvicorn.run(ui_app, ...)` on a different port
3. **Connection** - The `RUNNER_STATUS_URL` environment variable tells the UI where to find the runner
4. **Port Independence** - Runner and UI can be on any ports; they communicate via HTTP

This gives you full control over:
- Port selection
- Threading behavior
- Error handling
- Lifecycle management

See [Run UI and Runner Separately](/how-to/separate-ui-runner) for more patterns and use cases.

## Integration Example

Use flowtoy as part of a larger application:

```python
from flowtoy.cli import run_flow
import json

def sync_user_data():
    """Sync user data from external systems."""

    # Run the flow
    flows, status = run_flow(["sync-users.yaml"])

    # Check for failures
    if any(s.state == "failed" for s in status.steps.values()):
        raise RuntimeError("User sync flow failed")

    # Extract results
    users = flows["fetch_users"]["users"]
    groups = flows["fetch_groups"]["groups"]

    # Process results
    user_ids = [u["id"] for u in users]

    return {
        "user_count": len(users),
        "group_count": len(groups),
        "user_ids": user_ids,
        "duration": status.ended_at - status.started_at
    }

# Use in your application
if __name__ == "__main__":
    result = sync_user_data()
    print(json.dumps(result, indent=2))
```
