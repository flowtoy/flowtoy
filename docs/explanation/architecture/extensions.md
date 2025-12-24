---
title: Extension System Architecture
description: Design and implementation of the flowtoy extension system
---

## Overview

flowtoy uses an entry point-based extension system for providers which reduces core dependencies.

## Extension Development Workflow

### Creating an Extension

1. **Create package structure**:
   ```bash
   mkdir flowtoy-myprovider
   cd flowtoy-myprovider
   ```

2. **Implement provider** (`flowtoy_myprovider.py`):
   ```python
   class MyProvider:
       def __init__(self, configuration):
           self.config = configuration

       def call(self, input_payload=None):
           # Validate config (RAISE if missing)
           if "api_key" not in self.config:
               raise KeyError("myprovider requires 'api_key'")

           # Runtime logic (RETURN errors)
           try:
               result = do_work()
               return make_result(success=True, data=result)
           except RequestException as e:
               return result_from_exception(e)
   ```

3. **Register entry point** (`pyproject.toml`):
   ```toml
   [project.entry-points."flowtoy.providers"]
   myprovider = "flowtoy_myprovider:MyProvider"
   ```

4. **Install**:
   ```bash
   pip install -e .  # Development mode
   ```

5. **Use in workflows**:
   ```yaml
   sources:
     my_source:
       type: myprovider  # Automatically discovered
       api_key: "{{ env.API_KEY }}"
   ```

## Future Enhancements

### Potential Improvements
3. **CLI command**: `flowtoy extensions list` to show installed extensions
4. **Validation**: `flowtoy validate-extension <name>` to check extension structure
5. **Templates**: `flowtoy create-extension <name>` scaffolding tool

## References

- **Entry Point Spec**: [Python Packaging User Guide](https://packaging.python.org/specifications/entry-points/)
- **Extension Documentation**: `docs/reference/providers/extensions.md`

## Commands

### Verify Extension Installation
```bash
python -c "from importlib.metadata import entry_points; print(list(entry_points(group='flowtoy.providers')))"
```

### Run Tests
```bash
bash -l -c 'PYTHONPATH="$(pwd)" pytest -q'
```
