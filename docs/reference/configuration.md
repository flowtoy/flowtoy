---
title: Configuration
description: Complete guide to flowtoy YAML configuration
---

# Configuration

flowtoy uses YAML files to configure data sources and flows. Multiple configuration files can be specified and will be deep-merged.

## Basic Structure

A flowtoy configuration file has two main sections:

```yaml
sources:
  # Define your data sources here

flow:
  # Define your flow steps here
```

## Configuration Merging

Multiple YAML files are deep-merged from left to right:

```bash
flowtoy run base.yaml secrets.yaml overrides.yaml
```

This allows you to:
- Keep base configuration in version control
- Store secrets separately
- Override settings per environment

## Sources Section

See [Sources](sources.md) for complete documentation on defining data sources.

## Flow Section

See [Flows](flows.md) for complete documentation on defining flow steps.

## Next Steps

- [Sources](sources.md): Define data sources
- [Flows](flows.md): Create flow steps
- [Templating](templating.md): Use Jinja2 templates
