---
title: Sources Reference
description: Technical specification for source configuration
---

# Sources

Sources define provider configurations that can be referenced by name in flow steps.

## Structure

```yaml
sources:
  <source_name>:
    type: <provider_type>
    configuration:
      <key>: <value>
```

### Fields

- **`<source_name>`** (string, required): Unique identifier for this source
- **`type`** (string, required): Provider type name (registered via entry points)
- **`configuration`** (object, optional): Provider-specific settings

## Provider Types

### Built-in Providers

- **`rest`**: HTTP/REST API provider
- **`process`**: Shell command/script execution
- **`env`**: Environment variable reader

### Third-Party Providers

Additional providers can be installed as Python packages. They register themselves using Python entry points in the `flowtoy.providers` group.

## Configuration Merging

When multiple YAML files are provided, sources with the same name are deep-merged left to right.

Example:
```bash
flowtoy run base.yaml overrides.yaml
```

**base.yaml**:
```yaml
sources:
  api:
    type: rest
    configuration:
      url: https://api.example.com
```

**overrides.yaml**:
```yaml
sources:
  api:
    configuration:
      headers:
        Authorization: Bearer token
```

**Result**:
```yaml
sources:
  api:
    type: rest
    configuration:
      url: https://api.example.com
      headers:
        Authorization: Bearer token
```

## Usage in Flow Steps

Sources are referenced by name in flow steps:

```yaml
flow:
  - name: step1
    source: <source_name>
```

See [Flows Reference](flows.md) for complete flow step specification.

## Provider-Specific Configuration

Each provider type accepts different configuration fields:

- [REST Provider](providers/rest.md)
- [Process Provider](providers/process.md)
- [Environment Provider](providers/env.md)
- [Creating Custom Providers](providers/extensions.md)
