---
title: Flows Reference
description: Technical specification for flow step configuration
---

# Flows

Flow steps define data operations executed by providers. Steps are executed according to their dependencies.

## Structure

```yaml
flow:
  - name: <step_name>
    source: <source_reference>
    input: <input_spec>
    output: <output_spec>
    depends_on: [<step_name>, ...]
    on_error: <policy>
```

## Step Fields

### `name` (required)

Type: `string`

Unique identifier for the step. Used to reference step outputs in templates.

### `source` (required)

Type: `string | object`

Provider to execute. Three forms:

**Named source reference:**
```yaml
source: <source_name>
```

**Inline source:**
```yaml
source:
  type: <provider_type>
  configuration: {...}
```

**Source override:**
```yaml
source:
  base: <source_name>
  override:
    configuration: {...}
```

### `input` (optional)

Type: `object`

Data passed to the provider. Structure depends on provider type.

See provider documentation for input specification:
- [REST Provider](providers/rest.md)
- [Process Provider](providers/process.md)
- [Environment Provider](providers/env.md)

### `output` (optional)

Type: `array[object]`

Extracts and names data from provider results.

```yaml
output:
  - name: <output_name>
    type: <extraction_type>
    value: <extraction_value>
```

**Extraction types:**

- **`json`**: Returns entire result as JSON
  ```yaml
  - name: data
    type: json
  ```

- **`jmespath`**: Extracts using JMESPath query
  ```yaml
  - name: user_id
    type: jmespath
    value: user.id
  ```

Extracted outputs are accessible via templates: `{{ flows.<step_name>.<output_name> }}`

### `depends_on` (optional)

Type: `array[string]`

Explicit step dependencies. Step waits for all listed steps to complete.

```yaml
depends_on:
  - step1
  - step2
```

**Implicit dependencies:** Steps that reference other steps' outputs via templates automatically depend on them.

### `on_error` (optional)

Type: `string`

Error handling policy for this step. Overrides global `runner.on_error`.

Values:
- **`fail`** (default): Halt entire flow on failure
- **`skip`**: Mark this step and dependents as skipped
- **`continue`**: Allow dependents to execute despite failure

## Execution Order

Steps execute based on dependency resolution:

1. Steps with no dependencies run immediately
2. Steps run when all dependencies complete
3. Independent steps execute in parallel
4. Failed steps affect dependents according to error policy

## Runner Configuration

Global flow settings:

```yaml
runner:
  on_error: <policy>
  max_workers: <integer>
```

### `runner.on_error`

Default error policy for all steps without explicit `on_error`.

### `runner.max_workers`

Maximum concurrent step executions. Default: `4` or `(active_threads + 3)`, whichever is smaller.

Override via CLI: `flowtoy run config.yaml --max-workers 10`

## Template Context

Templates have access to:

- **`flows.<step_name>.<output_name>`**: Outputs from completed steps
- **`sources.<source_name>.<key>`**: Values from source configurations

See [Templating Reference](templating.md) for template syntax.

## Examples

### Sequential Execution

```yaml
flow:
  - name: step1
    source: api
    output:
      - name: id
        type: jmespath
        value: user_id

  - name: step2
    source: api
    input:
      user_id: "{{ flows.step1.id }}"
```

Step2 runs after step1 completes (implicit dependency via template reference).

### Parallel Execution

```yaml
flow:
  - name: fetch_users
    source: users_api

  - name: fetch_products
    source: products_api
```

Both steps run concurrently (no dependencies).

### Explicit Dependencies

```yaml
flow:
  - name: setup
    source: init_script

  - name: process
    source: main_script
    depends_on: [setup]
```

Process waits for setup (explicit dependency).

### Error Handling

```yaml
flow:
  - name: optional_step
    source: api
    on_error: continue

  - name: required_step
    source: api
```

Required_step executes even if optional_step fails.
