---
title: Python API
description: Python API reference for programmatic flow execution
---

# Python API

flowtoy can be used as a Python library to run flows programmatically.

See [Use the Python API](/how-to/use-python-api) for practical examples and usage patterns.

## Functions

### run_flow

```python
def run_flow(config_paths: List[str]) -> Tuple[dict, object]
```

Run a flow from configuration files and return outputs.

**Parameters:**
- `config_paths` (list of str) - Paths to YAML configuration files

**Returns:**
- Tuple of `(flows, status)`:
  - `flows` (dict) - Step outputs: `{step_name: {output_name: value}}`
  - `status` (RunStatus) - Execution status object

**Module:** `flowtoy.cli`

### load_yaml_files

```python
def load_yaml_files(paths: List[str]) -> Dict[str, Any]
```

Load and merge YAML configuration files.

**Parameters:**
- `paths` (list of str) - Paths to YAML files

**Returns:**
- dict - Merged configuration (later files override earlier ones)

**Module:** `flowtoy.config`

### serve_runner_api_in_thread

```python
def serve_runner_api_in_thread(
    runner: Any,
    host: str = "127.0.0.1",
    port: int = 0,
    log_level: str = "info",
    log_capture: Optional[LogCapture] = None
) -> threading.Thread
```

Start a status API server in a background thread.

**Parameters:**
- `runner` (LocalRunner) - Runner instance to expose
- `host` (str) - Server host (default: `127.0.0.1`)
- `port` (int) - Server port (default: 0 for auto-assignment)
- `log_level` (str) - Uvicorn log level (default: `"info"`). Use `"error"` or `"critical"` to suppress startup messages, which is recommended when using with TUI.
- `log_capture` (LogCapture|None) - Optional LogCapture instance to capture uvicorn logs for display in TUI

**Returns:**
- threading.Thread - Daemon thread running the server

**Module:** `flowtoy.runner_api`

### LogCapture

```python
class LogCapture(logging.Handler):
    def __init__(self, maxlen: int = 100)
```

Logging handler that captures log records in a deque for display in TUI.

**Constructor Parameters:**
- `maxlen` (int) - Maximum number of log records to keep (default: 100)

**Attributes:**
- `records` (deque) - Deque containing formatted log messages

**Usage Example:**

```python
from flowtoy.runner_api import LogCapture, serve_runner_api_in_thread
from flowtoy.runner import LocalRunner
from flowtoy.config import load_yaml_files

# Create log capture
log_capture = LogCapture(maxlen=50)

# Create runner and start API with log capture
config = load_yaml_files(["flow.yaml"])
runner = LocalRunner(config)
serve_runner_api_in_thread(
    runner,
    port=8005,
    log_level="info",
    log_capture=log_capture
)

# Access captured logs
for log_line in log_capture.records:
    print(log_line)
```

**Module:** `flowtoy.runner_api`

## Classes

### LocalRunner

```python
class LocalRunner:
    def __init__(self, config: Dict[str, Any])
    def run(self) -> None
```

Execute a flow with full control over configuration and state.

**Constructor Parameters:**
- `config` (dict) - Flow configuration dictionary

**Attributes:**
- `config` (dict) - Flow configuration
- `flows` (dict) - Step outputs (populated after `run()`)
- `status` (RunStatus) - Execution status
- `sources` (dict) - Configured data sources
- `steps` (list) - Flow steps from configuration

**Methods:**
- `run()` - Execute the flow (blocks until completion)

**Module:** `flowtoy.runner`

### RunStatus

Container for flow execution status.

**Attributes:**
- `run_id` (int) - Unique run identifier (milliseconds since epoch)
- `started_at` (float|None) - Run start timestamp (seconds since epoch)
- `ended_at` (float|None) - Run end timestamp
- `steps` (dict) - Dictionary mapping step names to `StepStatus` objects

**Module:** `flowtoy.runner`

### StepStatus

Container for individual step execution status.

**Attributes:**
- `name` (str) - Step name
- `state` (str) - Current state: `pending`, `running`, `succeeded`, `failed`, `skipped`
- `started_at` (float|None) - Step start timestamp (seconds since epoch)
- `ended_at` (float|None) - Step end timestamp
- `error` (str|None) - Error message (if `state` is `failed`)

**Module:** `flowtoy.runner`

## Status API Integration

The `runner_api` module provides functions for serving the [Status API](/reference/api/status) alongside programmatic execution. See [Use the Python API](/how-to/use-python-api) for integration examples.
