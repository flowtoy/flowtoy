---
title: Provider Results
description: Understanding the internal result structure
---

# Provider Results

This page explains the internal data structure that providers return. Understanding this structure helps when debugging complex flows or developing custom providers.

## Why This Matters

When you reference step outputs in templates using `{{ flows.<step>.<key> }}`, flowtoy extracts data from the standardized result structure described below. Knowing this structure helps you:

- Debug unexpected template behavior
- Understand error messages and status codes
- Develop custom provider extensions
- Troubleshoot data transformation issues

## Standard Result Structure

All providers return results in this format:

```json
{
  "status": {
    "success": true,
    "code": 0,
    "notes": []
  },
  "data": <any>,
  "meta": {}
}
```

## Status Section

Contains execution metadata:

- **success** (bool): Whether the operation succeeded
- **code** (int): Numeric status code (0 indicates success)
- **notes** (list): Optional messages, warnings, or diagnostic information

When a step fails, `success` is `false` and `notes` typically contains error details.

## Data Section

Contains the actual output from the provider. The structure varies by provider type:

- **REST provider**: Parsed JSON response body or raw text
- **Process provider**: Object with `stdout`, `stderr`, `returncode`
- **Env provider**: String value of the environment variable
- **Extension providers**: Format defined by the extension

When you write `{{ flows.my_step.users }}`, flowtoy accesses `data.users` from the result.

## Meta Section

Optional metadata about the operation:

- Execution timing information
- Provider-specific diagnostic data
- Internal performance metrics

Most users don't need to access meta fields directly.
