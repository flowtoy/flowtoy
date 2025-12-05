# flowtoy - local flow runner prototype

Minimal prototype that implements a YAML-driven flow runner with a local runner and a small status API.

## Installation

### Core Framework

Install dependencies (recommend a venv):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Connector Plugins

flowtoy supports optional connector plugins. Built-in connectors include:
- **rest**: HTTP/REST API calls
- **process**: Execute shell commands
- **env**: Read environment variables

Additional connectors via plugins:
- **ldap**: LDAP directory queries (install with `pip install flowtoy-ldap`)

See [Connector Plugin System](docs/connector-plugins.md) for creating your own connectors.

## Usage

Run a flow:

```bash
flowtoy run config.yaml secrets.yaml
```

Serve status API and run flow once on startup:

```bash
flowtoy serve config.yaml secrets.yaml
```

The API exposes:
- GET /status
- GET /outputs

## Architecture

### Core Components

- **Runner**: Executes workflows with dependency-aware parallel scheduling
- **Connectors**: Pluggable interfaces to external systems (REST, Process, Env, etc.)
- **Templating**: Jinja2-based template engine for dynamic values
- **Config**: YAML configuration with deep merge support

### Connector Plugin System

flowtoy uses Python entry points to discover connector plugins. This keeps the core lightweight while allowing optional functionality.

**Creating a plugin:**
```python
# flowtoy_custom.py
class CustomConnector:
    def __init__(self, configuration):
        self.config = configuration

    def call(self, input_payload=None):
        # Your logic here
        return {"status": {"success": True}, "data": {...}, "meta": {}}
```

**Register in pyproject.toml:**
```toml
[project.entry-points."flowtoy.connectors"]
custom = "flowtoy_custom:CustomConnector"
```

See [docs/connector-plugins.md](docs/connector-plugins.md) for complete documentation.

## Documentation

- [Connector Plugin System](docs/connector-plugins.md) - Create and publish connector plugins
- [Secret Redaction](docs/secret-redaction.md) - Configure secret redaction in ProcessConnector
- [Major Issue #4 Analysis](docs/major-issue-4-analysis.md) - Error handling consistency analysis
