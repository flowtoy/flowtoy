# Dependency Validation Examples

## Valid Flow

This flow will execute successfully:

```yaml
sources:
  env_source:
    type: env
    configuration:
      vars:
        - USER

flow:
  - name: get_env
    source: env_source
    output:
      - name: user
        type: json

  - name: use_env
    source: env_source
    depends_on: [get_env]
    input:
      type: parameter
      value: "{{ flows.get_env.user.USER }}"
    output:
      - name: result
        type: json
```

## Invalid Flow - Explicit Dependency

This flow will fail validation before execution:

```yaml
flow:
  - name: step1
    output: []

  - name: step2
    depends_on: [step1, nonexistent_step]  # ERROR: nonexistent_step doesn't exist
    output: []
```

**Error**:
```
ValueError: Flow configuration has invalid dependencies:
  - Step 'step2' depends on non-existent step(s): 'nonexistent_step'
```

## Invalid Flow - Template Reference

This flow will also fail validation:

```yaml
sources:
  dummy:
    type: env
    configuration:
      vars: []

flow:
  - name: step1
    source: dummy
    input:
      type: parameter
      value: "{{ flows.missing_step.value }}"  # ERROR: missing_step doesn't exist
    output: []
```

**Error**:
```
ValueError: Flow configuration has invalid dependencies:
  - Step 'step1' depends on non-existent step(s): 'missing_step'
```

## Case Sensitivity

Step names are case-sensitive:

```yaml
flow:
  - name: MyStep
    output: []

  - name: step2
    depends_on: [mystep]  # ERROR: 'mystep' != 'MyStep'
    output: []
```

**Error**:
```
ValueError: Flow configuration has invalid dependencies:
  - Step 'step2' depends on non-existent step(s): 'mystep'
```

## Multiple Invalid Dependencies

All invalid dependencies are reported at once:

```yaml
flow:
  - name: step1
    depends_on: [missing1, missing2]
    output: []

  - name: step2
    depends_on: [missing3]
    output: []
```

**Error**:
```
ValueError: Flow configuration has invalid dependencies:
  - Step 'step1' depends on non-existent step(s): 'missing1', 'missing2'
  - Step 'step2' depends on non-existent step(s): 'missing3'
```
