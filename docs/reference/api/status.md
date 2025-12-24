---
title: Status API
description: HTTP API for flow execution status and outputs
---

# Status API

The status API provides HTTP endpoints for querying flow execution state and step outputs. This API is served by:

- `flowtoy serve` command (default port 8000)
- `flowtoy run --status-port <PORT>` command
- `flowtoy webui` and `flowtoy tui` commands (auto-assigned ports in all-in-one mode)

## Endpoints

### GET /status

Returns current flow execution status including step states, timestamps, and progress.

**Response Format:**

```json
{
  "run_id": 1733524800000,
  "started_at": 1733524800.123,
  "ended_at": 1733524850.456,
  "total_steps": 5,
  "completed_steps": 5,
  "current_step": null,
  "running_steps": [],
  "running_count": 0,
  "steps": {
    "fetch_users": {
      "state": "succeeded",
      "started_at": 1733524800.234,
      "ended_at": 1733524810.567,
      "notes": [],
      "outputs": ["users", "count"]
    },
    "process_data": {
      "state": "running",
      "started_at": 1733524810.678,
      "ended_at": null,
      "notes": [],
      "outputs": []
    }
  }
}
```

**Response Fields:**

- `run_id` (integer) - Unique run identifier (milliseconds since epoch)
- `started_at` (float|null) - Run start timestamp (seconds since epoch)
- `ended_at` (float|null) - Run end timestamp (null if still running)
- `total_steps` (integer) - Total number of steps in flow
- `completed_steps` (integer) - Number of steps finished (succeeded or failed)
- `current_step` (string|null) - First currently running step (backwards compatibility)
- `running_steps` (array) - List of currently running step names
- `running_count` (integer) - Number of currently running steps
- `steps` (object) - Per-step status information

**Step Status Fields:**

- `state` (string) - Step state: `pending`, `running`, `succeeded`, `failed`, `skipped`
- `started_at` (float|null) - Step start timestamp
- `ended_at` (float|null) - Step end timestamp
- `notes` (array) - Error messages (contains error string if failed)
- `outputs` (array) - List of output variable names defined by this step

**Status Codes:**

- `200` - Success
- `500` - Server error (includes `{"error": "message"}` in response)

### GET /outputs

Returns output values from all completed steps.

**Response Format:**

```json
{
  "fetch_users": {
    "users": [
      {"id": 1, "name": "Alice"},
      {"id": 2, "name": "Bob"}
    ],
    "count": 2
  },
  "process_data": {
    "result": "processed"
  }
}
```

**Response Structure:**

Returns an object where:
- Keys are step names
- Values are objects containing the step's output variables

Each step's outputs correspond to the `output` definitions in the flow configuration:

```yaml
flow:
  - name: fetch_users
    output:
      - name: users
        type: jmespath
        value: "data.users"
      - name: count
        type: jmespath
        value: "length(data.users)"
```

**Status Codes:**

- `200` - Success (returns `{}` if no outputs available)
- `500` - Server error (includes `{"error": "message"}` in response)

## Usage Examples

### Polling for Completion

```bash
# Start flow with status server
flowtoy serve flow.yaml --port 8080

# Poll status from another terminal
while true; do
  curl -s http://localhost:8080/status | jq '.completed_steps, .total_steps'
  sleep 1
done
```

### Fetching Final Outputs

```bash
# Wait for completion then get outputs
curl http://localhost:8080/status | jq '.ended_at'
curl http://localhost:8080/outputs | jq '.'
```

### Monitoring Specific Step

```bash
# Check if specific step completed
curl -s http://localhost:8080/status | \
  jq '.steps.fetch_users.state'
```

## Implementation Notes

- Both endpoints are read-only (GET requests only)
- Responses are always JSON
- The API is thread-safe and can handle concurrent requests
- Step outputs are available immediately after step completion
- The `current_step` field shows the first running step for backwards compatibility; use `running_steps` for complete list during parallel execution
