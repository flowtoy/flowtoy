---
title: CLI
description: Command-line interface reference
---

# CLI

flowtoy provides a command-line interface for running flows and serving web interfaces.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```bash
flowtoy [COMMAND] [OPTIONS] [ARGS]
```

## Commands

### run

Execute a flow from YAML configuration files.

**Usage:**
```bash
flowtoy run [OPTIONS] CONFIG...
```

**Arguments:**
- `CONFIG...` - One or more YAML configuration file paths (required)

**Options:**
- `-j, --json` - Print outputs as JSON
- `-o, --output-file <PATH>` - Write JSON outputs to file
- `-q, --quiet` - Suppress stdout printing
- `--status-port <PORT>` - Start HTTP status server on specified port
- `--max-workers <N>` - Maximum number of worker threads

**Exit behavior:**
- Without `--status-port`: Exits after flow completes
- With `--status-port`: Continues running until interrupted (Ctrl-C)

### serve

Start HTTP status API server and execute flow at startup.

**Usage:**
```bash
flowtoy serve [OPTIONS] CONFIG...
```

**Arguments:**
- `CONFIG...` - One or more YAML configuration file paths (required)

**Options:**
- `--host <HOST>` - Server host (default: `127.0.0.1`)
- `--port <PORT>` - Server port (default: `8000`)

**Endpoints:**
- `/status` - Flow execution status
- `/outputs` - Flow step outputs

Flow runs once in background thread. Server continues running until interrupted.

### webui

Start web UI server to monitor flow execution.

**Usage:**
```bash
# All-in-one mode (run flow and serve UI)
flowtoy webui [OPTIONS] CONFIG...

# External monitoring mode (serve UI for remote flow)
flowtoy webui --status-url <URL>
```

**Arguments:**
- `CONFIG...` - One or more YAML configuration file paths (optional)

**Options:**
- `--host <HOST>` - Server host (default: `127.0.0.1`)
- `--port <PORT>` - Server port (default: `8000`)
- `--status-url <URL>` - Monitor a remote runner status endpoint
- `--max-workers <N>` - Maximum number of worker threads (all-in-one mode only)

**Modes:**

1. **All-in-one mode**: `flowtoy webui flow.yaml`
   - Runs the flow in background
   - Serves web UI on specified host/port
   - UI polls local `/status` and `/outputs` endpoints

2. **External monitoring mode**: `flowtoy webui --status-url http://...`
   - Serves UI only (doesn't run a flow)
   - Proxies requests to remote status server
   - Useful for monitoring flows running elsewhere

**Endpoints:**
- `/` - Web UI (HTML interface)
- `/status` - Flow execution status (JSON)
- `/outputs` - Flow step outputs (JSON)

Flow runs once in background thread. Server continues running until interrupted.

### tui

Start terminal UI to monitor flow execution with real-time updates.

**Usage:**
```bash
# All-in-one mode (run flow and monitor it)
flowtoy tui [OPTIONS] CONFIG...

# External monitoring mode (monitor remote flow)
flowtoy tui --status-url <URL>
```

**Arguments:**
- `CONFIG...` - One or more YAML configuration file paths (optional)

**Options:**
- `--status-url <URL>` - Monitor a remote runner status endpoint
- `--max-workers <N>` - Maximum number of worker threads (all-in-one mode only)
- `--show-logs` - Display server logs in a panel (all-in-one mode only)

**Modes:**

1. **All-in-one mode**: `flowtoy tui flow.yaml`
   - Runs the flow in background with auto-assigned status port
   - Displays TUI monitoring the flow
   - Similar to `webui` but with terminal interface

2. **External monitoring mode**: `flowtoy tui --status-url http://...`
   - Monitors a flow running elsewhere
   - Requires running instance with status API (via `run --status-port` or `serve`)
   - Useful for monitoring remote flows

**Interactive Features:**

The TUI uses the Textual framework and provides:
- **Compact status table**:
  - Step states shown with icons (◷ pending, ▶ running, ✓ succeeded, ✗ failed)
  - Human-readable timestamps (HH:MM:SS for start time, +X.Xs for duration)
- **Scrollable Outputs panel**: Use arrow keys, page up/down, or mouse wheel to scroll through outputs independently
- **Scrollable Logs panel**: When `--show-logs` is used, logs are also independently scrollable
- **Keyboard shortcuts**:
  - `q` - Quit the TUI
  - `r` - Force immediate refresh
  - Arrow keys / Page Up/Down - Scroll the focused panel
  - Tab - Switch focus between panels

**Log Display:**

Use `--show-logs` to see server startup messages and access logs in a scrollable panel at the bottom:

```bash
flowtoy tui flow.yaml --show-logs
```

This displays up to 100 recent uvicorn log messages, useful for debugging server connectivity issues.

If `--status-url` not provided and no config files given, reads `RUNNER_STATUS_URL` environment variable.

## Multiple Configuration Files

All commands accept multiple YAML files. Files are merged with later files overriding earlier ones:

```bash
flowtoy run base.yaml overrides.yaml
```

## Global Options

- `-h, --help` - Show help message
- `--install-completion` - Install shell completion
- `--show-completion` - Show shell completion script
