---
title: flowtoy
description: Minimal YAML-driven flow runner for local data integration
site:
  hide_outline: true
  hide_toc: true
  hide_title_block: true
---

+++ {"kind": "split-image"}

## flowtoy

A minimal YAML-driven flow runner with dependency-aware parallel scheduling and an extension-based provider system.

![flowtoy](images/flowtoy-wall.png)

Explore the documentation.

{button}`Getting Started <getting-started.md>`
{button}`Tutorial <tutorial.md>`

{button}`How-To Guides <how-to/fetch-rest-api-data.md>`
{button}`Reference <reference/configuration.md>`
{button}`Explanation <explanation/architecture/overview.md>`
+++

+++ {"kind": "justified"}

## Key Features

**Flow Configuration** - Define data sources and flows in YAML with Jinja2 templating for dynamic values

**Flow Execution** - Dependency-aware parallel scheduler with configurable error handling and automatic secret redaction

**User Interfaces** - Run flows via CLI (`run` command), monitor with interactive TUI, browser-based Web UI, or programmatic Status API

**Extension System** - Extensible provider architecture via Python entry points

![Text user interface screenshot](images/tui-screenshot.svg)

+++

+++ {"kind": "justified"}

## Quick Example

This example fetches a list of users from a REST API and counts them:

```yaml
sources:
  jsonplaceholder:
    type: rest
    configuration:
      url: https://jsonplaceholder.typicode.com/users
      method: GET

flow:
  - name: fetch_users
    source: jsonplaceholder
    output:
      - name: user_count
        type: jmespath
        value: "length(@)"
```

Run it:
```bash
flowtoy run config.yaml
```

**What's happening:**

1. **sources** defines a REST provider named `jsonplaceholder` that fetches from the JSONPlaceholder API
2. **flow** defines a single step that uses this provider
3. **output** extracts data using [JMESPath](https://jmespath.org/):
   - `@` represents the entire response data (an array of users)
   - `length(@)` counts the array length
   - The result is stored as `user_count` for use in subsequent steps

The output will be:
```json
{
  "fetch_users": {
    "user_count": 10
  }
}
```

+++

+++ {"kind": "justified"}

## Installation

Clone and install from source:

```bash
git clone https://github.com/flowtoy/flowtoy
cd flowtoy
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

+++

+++ {"kind": "justified"}

## Built-in Providers

- **rest**: HTTP/REST API calls
- **process**: Execute shell commands
- **env**: Read environment variables

Additional providers can be created as extensions (see [Extension System](reference/providers/extensions.md)).

+++
