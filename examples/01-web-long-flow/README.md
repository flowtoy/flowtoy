# Run the long demo flow with a web UI (two terminals)

This example demonstrates the UI and runner working in separate processes. The UI proxies to the runner status API so the web interface can be run independently.

## Overview

- The runner exposes a small status API that serves `/status` and `/outputs`.
- The web UI runs on its own port and proxies status requests to the runner using the `RUNNER_STATUS_URL` environment variable.
- The UI port and the runner status port are independent — they do not have to match. However, `RUNNER_STATUS_URL` must point to the runner's status server (the `--status-port` you start the runner with).

## Steps

1) Open Terminal A — start the web UI (it will poll the runner status API)

   Start the UI (from the repository root):

   ```bash
   # point the UI at the runner status server we will start in Terminal B
   export RUNNER_STATUS_URL="http://127.0.0.1:8005"
   uvicorn evans.webui:app --host 127.0.0.1 --port 8006 --log-level info
   ```

   Open http://127.0.0.1:8006 in your browser. The UI will show "No runner attached" until a runner is serving a status API at the configured `RUNNER_STATUS_URL`.

2) Open Terminal B — start the runner and status server

   From the repository root run:

   ```bash
   evans run examples/flows/university-directory.yaml --status-port 8005
   ```

   The runner will start a status API on http://127.0.0.1:8005 and then execute the flow. When it is running, the UI from Terminal A will show live step progress.

## Quick single-process alternative

If you prefer to run the UI and runner in the same process for quick debugging, use the CLI command `webui`:

```bash
evans webui examples/flows/university-directory.yaml --host 127.0.0.1 --port 8006
```

This serves the UI and the runner status API together on the UI port.

## Notes

- Choose any ports that work for you. Just make sure the value in `RUNNER_STATUS_URL` (UI side) matches the `--status-port` you pass to the runner.
