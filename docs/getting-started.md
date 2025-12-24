---
title: Getting Started
description: Install flowtoy and run your first flow
---

# Getting Started

## Installation

Clone the repository and install:

```bash
git clone https://github.com/flowtoy/flowtoy
cd flowtoy
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Built-in Providers

flowtoy comes with three built-in providers:

- **rest**: HTTP/REST API calls
- **process**: Execute shell commands
- **env**: Read environment variables

## Extension Providers

Additional providers can be created as extensions for databases, cloud services, message queues, and more.

See [Extension System](reference/providers/extensions.md) to create your own.

## Basic Concepts

### Sources

Sources define where your data comes from. Each source has a type and configuration. Use Jinja2 templates (e.g., `{{ env.API_TOKEN }}` or `{{ flows.step1.user_id }}`) to reference environment variables or outputs from previous steps.

```yaml
sources:
  github_api:
    type: rest
    configuration:
      url: https://api.example.com
      method: GET
      headers:
        Authorization: "Bearer {{ env.API_TOKEN }}"
```

### Flows

Flows define the sequence of data operations. Each step uses a provider and can extract data for use in subsequent steps.

```yaml
flow:
  - name: fetch_data
    source: github_api
    output:
      - name: users
        type: jmespath
        value: "@"
```

### Dependencies

Flowtoy automatically determines dependencies based on template references, or you can specify them explicitly:

```yaml
sources:
  inventory_api:
    type: rest

flow:
  - name: step1
    source: inventory_api

  - name: step2
    source: inventory_api
    depends_on: [step1]  # Explicit dependency
```

## Your First Flow

Create a file `hello.yaml`:

```yaml
sources:
  echo_command:
    type: process
    configuration:
      command: ["echo"]

flow:
  - name: hello
    source: echo_command
    input:
      args: ["Hello from flowtoy!"]
    output:
      - name: message
        type: jmespath
        value: "stdout"
```

Run it:

```bash
flowtoy run hello.yaml
```

Output:
```json
{
  "hello": {
    "message": "Hello from flowtoy!\n"
  }
}
```

## CLI Commands

### Run a Flow

```bash
flowtoy run config.yaml [secrets.yaml...]
```

Options:
- `-j, --json`: Output as JSON
- `-o, --output-file FILE`: Write JSON output to file
- `-q, --quiet`: Suppress stdout
- `--max-workers N`: Set max parallel workers
- `--status-port PORT`: Start status API server

### Serve Status API

Run a flow and serve status API:

```bash
flowtoy serve config.yaml
```

Access at `http://localhost:8000/status`

### Web UI

Run a flow with web-based monitoring:

```bash
flowtoy webui config.yaml
```

Access at `http://localhost:8000`

### Terminal UI (TUI)

Monitor a running flow in the terminal:

```bash
# In one terminal:
flowtoy run config.yaml --status-port 8005

# In another terminal:
flowtoy tui --status-url http://localhost:8005/status
```

## Configuration Files

flowtoy supports multiple configuration files that are deep-merged:

```bash
flowtoy run base-config.yaml secrets.yaml overrides.yaml
```

This is useful for separating:
- Base configuration (checked into git)
- Secrets (kept out of version control)
- Environment-specific overrides

Example `base-config.yaml`:

```yaml
sources:
  user_service:
    type: rest
    configuration:
      url: https://api.example.com
      method: GET
```

Example `secrets.yaml`:

```yaml
sources:
  user_service:
    configuration:
      headers:
        Authorization: "Bearer {{ env.API_TOKEN }}"
```

## Next Steps

- **[Tutorial](tutorial.md)**: Build a complete multi-step data integration flow
- **[How-To Guides](how-to/fetch-rest-api-data.md)**: Solve specific problems and accomplish tasks
- **[Reference](reference/configuration.md)**: Complete technical reference for all features
- **[Explanation](explanation/overview.md)**: Understand how flowtoy works under the hood
