# CLI demo: run a flow from the command line

This example focuses on running a YAML-defined flow from the command line using the project's CLI. It demonstrates running the flow, exposing a status server for UIs, and using the terminal UI.

## Files

This example uses the canonical long demo flow defined in `examples/flows/university-directory.yaml`.

## Run the flow with the CLI

From the repository root you can run the shared flow and optionally start a status server that UIs can poll. Example:

```bash
evans run examples/flows/university-directory.yaml --status-port 8005
```

Options of interest:

- `--status-port <port>`: starts a small HTTP server serving `/status` and `/outputs` so the web UI or terminal UI can poll it.
- `--max-workers <n>`: control concurrency for the runner.
- `--json` or `--output-file`: capture outputs as JSON.

## Use the terminal UI

After starting the runner with `--status-port` you can open another terminal and run the terminal UI. Example:

```bash
export RUNNER_STATUS_URL="http://127.0.0.1:8005"
evans tui
```

This shows a live, updating table of step states and timestamps.

## Notes

- If you prefer a web UI, start the UI server and point `RUNNER_STATUS_URL` at the runner's status API (see `examples/01-web-long-flow/README.md` for details).
