---
title: Providers Overview
description: Understanding flowtoy's provider system
---

# Providers Overview

Providers are the building blocks of flowtoy flows. They interface with external systems to fetch, transform, and send data.

## Built-in Providers

flowtoy ships with three built-in providers:

- **[REST](rest.md)**: HTTP/REST API calls
- **[Process](process.md)**: Execute shell commands and scripts
- **[Environment](env.md)**: Read environment variables

## Third-Party Providers

Additional providers can be installed as Python packages for databases, cloud services, message queues, directory services, and more.

See the [Creating Custom Providers](extensions.md) documentation to create your own providers.

## Provider Interface

All providers implement a simple interface:

```python
class MyProvider:
    def __init__(self, configuration: dict):
        """Initialize with configuration from sources section."""
        self.config = configuration

    def call(self, input_payload=None):
        """Execute the provider logic.

        Returns:
            dict: Result with structure:
                {
                    "status": {"success": bool, "code": int, "notes": list},
                    "data": <any>,
                    "meta": {}
                }
        """
        pass
```

## Using Providers

Define providers in the `sources` section:

```yaml
sources:
  my_api:
    type: rest
    configuration:
      url: https://api.example.com
      method: GET
```

Use them in flow steps:

```yaml
flow:
  - name: fetch_data
    source: my_api
```

## Next Steps

- [REST Provider](rest.md): HTTP/REST API integration
- [Process Provider](process.md): Execute commands
- [Environment Provider](env.md): Read environment variables
- [Creating Custom Providers](extensions.md): Extend flowtoy with your own providers
