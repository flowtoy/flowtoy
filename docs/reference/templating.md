---
title: Templating Reference
description: Technical specification for Jinja2 template usage
---

# Templating

flowtoy uses Jinja2 templates for dynamic configuration. Templates are evaluated with `StrictUndefined` mode - referencing undefined variables raises an error.

## Syntax

```yaml
{{ expression }}
```

## Template Context

### `flows`

Access outputs from completed flow steps.

**Structure:**
```
flows.<step_name>.<output_name>
```

**Example:**
```yaml
{{ flows.fetch_user.user_id }}
{{ flows.fetch_data.results[0].name }}
```

### `sources`

Access data from source configurations (typically environment variables).

**Structure:**
```
sources.<source_name>.<key>
```

**Example:**
```yaml
{{ sources.credentials.API_KEY }}
{{ sources.config.DATABASE_URL }}
```

## Template Locations

Templates can be used in:

1. **Source configuration**
   ```yaml
   sources:
     api:
       type: rest
       configuration:
         url: "{{ sources.env_vars.API_URL }}"
   ```

2. **Flow step input**
   ```yaml
   flow:
     - name: step
       source: api
       input:
         param: "{{ flows.previous.output }}"
   ```

3. **Provider-specific fields** (see provider documentation)

## Data Access

### Nested Access

Use dot notation:
```yaml
{{ flows.step1.user.profile.email }}
{{ sources.config.database.host }}
```

### Array Access

Use bracket notation:
```yaml
{{ flows.fetch_users.users[0].id }}
{{ flows.get_list.items[2].name }}
```

## Jinja2 Filters

### `tojson`

Convert Python objects to JSON strings:
```yaml
{{ flows.step1.data | tojson }}
```

### `upper` / `lower`

Change string case:
```yaml
{{ flows.step1.name | upper }}
{{ flows.step1.email | lower }}
```

### `default`

Provide fallback values:
```yaml
{{ flows.step1.optional_field | default("default_value") }}
{{ flows.step1.count | default(0) }}
```

### `length`

Get sequence/string length:
```yaml
{{ flows.step1.users | length }}
```

### `join`

Concatenate sequence elements:
```yaml
{{ flows.step1.names | join(", ") }}
```

### `replace`

Replace substrings:
```yaml
{{ flows.step1.text | replace("old", "new") }}
```

### `trim`

Remove whitespace:
```yaml
{{ flows.step1.input | trim }}
```

### Filter Chaining

Apply multiple filters:
```yaml
{{ flows.step1.name | trim | lower | replace(" ", "_") }}
```

## Conditional Expressions

Inline conditionals:
```yaml
{{ flows.step1.value if flows.step1.value else "default" }}
{{ "active" if flows.step1.status == "running" else "inactive" }}
```

## String Operations

### Concatenation

```yaml
{{ flows.step1.first_name + " " + flows.step1.last_name }}
{{ sources.config.BASE_URL + "/api/v1" }}
```

## Multi-line Templates

### Literal Block Scalar (`|`)

Preserves newlines:
```yaml
input:
  template: |
    Line 1: {{ flows.step1.value }}
    Line 2: {{ flows.step2.value }}
```

### Folded Block Scalar (`>`)

Folds newlines to spaces:
```yaml
input:
  template: >
    This is a long string
    that will be folded
    into a single line.
```

## Error Handling

### Undefined Variables

Undefined variables raise errors:
```yaml
{{ flows.nonexistent.field }}  # Error: undefined
```

### Default Values

Use `default` filter for optional values:
```yaml
{{ flows.step1.optional | default("") }}
```

### Conditional Access

Check existence:
```yaml
{{ flows.step1.data.user.name if flows.step1.data.user else "Unknown" }}
```

## See Also

- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [Flows Reference](flows.md): Where templates are used
- [Sources Reference](sources.md): Source configuration templating
