---
title: Creating Custom Providers
description: Create and publish custom providers for flowtoy
---

flowtoy supports extending its provider ecosystem through Python entry points. This allows third-party developers to create and distribute providers without modifying the core framework.

## Creating a Custom Provider

### Project Structure

```
flowtoy-myprovider/
├── pyproject.toml
├── README.md
├── flowtoy_myprovider.py
└── tests/
    └── test_myprovider.py
```

### Implement the Provider

Your provider must implement the call method:

```python
# flowtoy_myprovider.py
from typing import Any, Dict, Optional

class MyProvider:
    """Custom provider for flowtoy framework."""

    type_name = "myprovider"  # Optional: used for documentation

    def __init__(self, configuration: Dict[str, Any]):
        """Initialize with configuration from YAML.

        Args:
            configuration: Dict containing provider config from sources section
        """
        self.configuration = configuration or {}

    def call(self, input_payload: Optional[Any] = None) -> Any:
        """Execute the provider logic.

        Args:
            input_payload: Optional input data from previous step or template

        Returns:
            Result dict with structure:
                {
                    "status": {"success": bool, "code": int, "notes": list},
                    "data": <any>,
                    "meta": {}
                }
        """
        # Import helper functions from flowtoy
        from flowtoy.providers.result import make_result, result_from_exception

        # Validate required configuration
        api_key = self.configuration.get("api_key")
        if not api_key:
            raise KeyError("myprovider requires 'api_key' in configuration")

        try:
            # Your provider logic here
            result_data = {"message": "success"}

            return make_result(
                success=True,
                code=0,
                data=result_data,
                notes=[],
                meta={}
            )
        except Exception as e:
            # Return runtime errors as structured results
            return result_from_exception(e)
```

### Configure Entry Point

In your `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "flowtoy-myprovider"
version = "0.1.0"
description = "My custom provider for flowtoy"
dependencies = [
    "flowtoy>=0.1.0",
    # Add your provider's dependencies here
]

# Register the provider via entry points
[project.entry-points."flowtoy.providers"]
myprovider = "flowtoy_myprovider:MyProvider"

[tool.setuptools.packages.find]
include = ["flowtoy_myprovider*"]
```

The entry point format is:
- **Group**: `flowtoy.providers` (required)
- **Name**: The provider type name used in YAML configs (e.g., `myprovider`)
- **Value**: Import path to the provider class (e.g., `module:ClassName`)

### Installation

Users can install your provider with:

```bash
cd flowtoy-myprovider
pip install -e .
```

## Using Custom Providers in Workflows

Once installed, custom providers are automatically discovered and can be used like built-in providers:

```yaml
sources:
  my_source:
    type: myprovider  # Name from entry point
    configuration:
      api_key: "{{ env.MY_API_KEY }}"
      endpoint: https://api.example.com

flow:
  - name: fetch_data
    source: my_source
    input: '{"query": "test"}'
    output:
      - name: result
        type: jmespath
        value: "message"
```

## Discovery Mechanism

flowtoy discovers all providers (built-in and custom) via Python entry points in the `flowtoy.providers` group.

**Built-in providers** are registered in flowtoy's own `pyproject.toml`:
```toml
[project.entry-points."flowtoy.providers"]
rest = "flowtoy.providers.rest:RestProvider"
process = "flowtoy.providers.process:ProcessProvider"
env = "flowtoy.providers.env:EnvProvider"
```

**Custom providers** are registered in their own `pyproject.toml`:
```toml
[project.entry-points."flowtoy.providers"]
myprovider = "flowtoy_myprovider:MyProvider"
```

### How It Works

Entry points are discovered on first use of any provider. flowtoy uses Python's `importlib.metadata.entry_points()` to find all registered providers in the `flowtoy.providers` group.

If a provider fails to load (e.g., missing dependencies), a warning is printed to stderr, but flowtoy continues with other available providers.

If you request an unknown provider type, flowtoy will list all available providers in the error message.

## Error Handling Policy

Your provider should follow flowtoy's error handling policy:

### Configuration Errors → RAISE
Missing required fields, invalid types, malformed configuration:
```python
if "required_field" not in self.configuration:
    raise KeyError("myprovider requires 'required_field' in configuration")
```

### Missing Dependencies → RAISE
Required libraries not installed:
```python
try:
    import special_library
except ImportError:
    raise ImportError(
        "special_library is required for MyProvider. "
        "Install with: # Install from local custom provider directory
cd custom providers/flowtoy-myprovider
pip install -e ."
    )
```

### Runtime Errors → RETURN
Network failures, timeouts, authentication failures:
```python
try:
    response = make_api_call()
except RequestException as e:
    return result_from_exception(e)
```

### Don't Catch Programming Errors
Let TypeErrors, AttributeErrors propagate - they indicate bugs.

## Suggested Practices

1. **Naming**: Use `flowtoy-<name>` package naming convention
1. **Versioning**: Specify `flowtoy>=X.Y.Z` to indicate compatible flowtoy versions
1. **Error Messages**: Provide actionable error messages with installation instructions
1. **Validation**: Validate configuration in `__init__` or early in `call`
1. **Testing**: Include comprehensive tests for your provider
1. **Secrets**: Document which fields contain secrets (for redaction)
