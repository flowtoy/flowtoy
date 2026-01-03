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

Type: `any`

Data passed to the provider. Can be a string, number, dict, list, or any other value. How the input is used depends on the provider and its configuration.

**Examples:**
```yaml
# String
input: "hello"

# Number
input: 42

# Template string
input: "{{ flows.step1.value }}"

# Dict (YAML)
input:
  name: "Alice"
  age: 30

# List (YAML)
input:
  - item1
  - item2
  - item3

# Multi-line string
input: |
  Line 1
  Line 2
```

See provider documentation for input handling:
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
sources:
  users_api:
    type: rest
    configuration:
      url: https://api.example.com/users/1
      method: GET
  posts_api:
    type: rest
    configuration:
      url: https://api.example.com/posts
      method: GET
      input_mode: parameter
      param_name: userId

flow:
  - name: get_user
    source: users_api
    output:
      - name: user_id
        type: jmespath
        value: id

  - name: get_user_posts
    source: posts_api
    input: "{{ flows.get_user.user_id }}"
    output:
      - name: posts
        type: json
```

The second step runs after the first completes (implicit dependency via template reference).

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
