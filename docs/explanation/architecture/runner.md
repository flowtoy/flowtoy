---
title: Runner Design
description: How the LocalRunner orchestrates workflow execution
---

# Runner Design

The `LocalRunner` is flowtoy's execution engine. It coordinates the entire workflow lifecycle from loading configuration to managing parallel step execution.

## Responsibilities

The runner handles:

1. **Configuration loading** - Parse YAML and build internal structures
2. **Dependency resolution** - Infer dependencies from explicit declarations and template references
3. **State management** - Track step outputs and execution status
4. **Parallel coordination** - Work with the scheduler to execute independent steps concurrently
5. **Error handling** - Implement per-step error policies (fail, skip, continue)

## Initialization

```python
runner = LocalRunner(config)
```

During initialization, the runner:

- Extracts sources from the configuration (provider connection definitions)
- Extracts flow steps (the workflow to execute)
- Initializes the `flows` dictionary to store step outputs
- Creates a `RunStatus` object to track execution state
- Configures thread pool size based on `runner.max_workers` setting

The runner uses a `threading.RLock()` to protect shared state when steps execute concurrently.

## Dependency Inference

flowtoy automatically discovers dependencies in two ways:

### 1. Explicit Dependencies

Steps can declare dependencies using `depends_on`:

```yaml
flow:
  - name: fetch_users
    source: rest
  - name: process_users
    depends_on: [fetch_users]
```

### 2. Implicit Dependencies

The runner scans input templates for references like `{{ flows.step_name.field }}`:

```yaml
- name: process_users
  input:
    template: "{{ flows.fetch_users.data }}"  # Creates implicit dependency
```

The pattern `flows\\.([A-Za-z0-9_]+)\\.` (implemented in `runner.py:109`) detects these references.

### Dependency Validation

At startup, the runner validates all dependencies:

- Checks that referenced steps exist
- Raises `ValueError` with detailed messages for missing dependencies
- Prevents execution if the dependency graph is invalid

This **fail-fast** approach catches configuration errors before any steps run.

## Execution Flow

The `run()` method implements the main execution loop:

### 1. Build Dependency Graph

```python
deps: Dict[str, set]         # name -> set of dependencies
dependents: Dict[str, set]   # name -> set of steps that depend on this
in_degree: Dict[str, int]    # name -> count of unsatisfied dependencies
```

These structures enable topological sorting for execution order.

### 2. Initialize Status Tracking

The runner creates a `StepStatus` object for each step to track:

- Current state (pending, running, succeeded, failed, skipped)
- Timestamps (started_at, ended_at)
- Error messages if failures occur

### 3. Submit Ready Steps

Steps with `in_degree == 0` (no unsatisfied dependencies) are immediately ready. The runner submits these to the thread pool executor.

### 4. Process Completions

As steps complete:

1. **On success**: Decrement `in_degree` for dependent steps; submit newly ready ones
2. **On failure**: Apply error policy (fail/skip/continue) to determine what happens next
3. **Update state**: Store outputs in `self.flows[step_name]` and update status

This loop continues until all steps complete or an error forces early termination.

## Step Execution Details

Each step runs in its own thread via the executor. The `submit_step()` function:

### 1. Resolves the Source

Sources can be:

- A string reference: `source: my_rest_api`
- Inline definition: `source: {type: rest, configuration: {...}}`
- Base with override: `source: {base: my_api, override: {url: ...}}`

The runner merges base configuration with overrides to build the final source definition.

### 2. Creates the Provider

```python
provider = create_provider(src_type, cfg)
```

The provider is instantiated with configuration from the source definition. This happens lazily (only when the step runs), which enables:

- Faster startup (no need to initialize unused providers)
- Extension dependencies only loaded when actually used

### 3. Renders Input Templates

The runner takes a **snapshot** of `self.flows` and `self.sources` under lock, then renders templates outside the lock:

```python
with self._lock:
    flows_snapshot = dict(self.flows)
    sources_snapshot = dict(self.sources)

payload = render_template(template, {
    "flows": flows_snapshot,
    "sources": sources_snapshot
})
```

This approach:

- Ensures consistent input data (no changes during rendering)
- Minimizes lock contention (rendering happens outside the lock)
- Enables true parallel execution

### 4. Calls the Provider

```python
result = provider.call(payload)
```

The provider performs the actual work (HTTP request, process execution, etc.) and returns a standardized result structure.

### 5. Processes the Result

The runner:

- Checks the `status.success` field
- Raises an exception if the provider reported failure
- Extracts outputs using JMESPath expressions
- Stores outputs in `self.flows[step_name]`

### 6. Updates Status

Status updates happen atomically under the lock:

```python
self._update_step_status(
    step_name,
    state="succeeded",
    ended_at=time.time()
)
```

## Error Handling

flowtoy supports three error policies:

### fail (default)

When a step fails, all descendant steps are skipped and execution stops. This is the safest default.

### skip

When a dependency fails, skip this step and all descendants. Other branches of the workflow continue.

### continue

When a dependency fails, allow this step to run anyway. Useful when a step has fallback logic or can handle missing data.

Error policies cascade: when a step fails, each dependent applies its own policy to decide whether to run, skip, or fail.

## Thread Safety

The runner uses several techniques to ensure thread safety:

1. **RLock protection** - Shared state (`self.flows`, `self.status`) is modified only under lock
2. **Snapshot semantics** - Steps render templates from consistent snapshots
3. **Atomic updates** - Status changes use the `_update_step_status()` helper
4. **Immutable references** - Step definitions are read-only after initialization

This design enables high concurrency without race conditions.

## Configuration Options

The runner respects these configuration settings:

```yaml
runner:
  max_workers: 4          # Thread pool size (default: min(4, cpu_count+1))
  on_error: fail          # Default error policy for all steps
```

Individual steps can override the error policy:

```yaml
flow:
  - name: optional_step
    on_error: skip        # Override for this step
```

## Performance Characteristics

- **Startup cost**: O(n) where n is the number of steps (build dependency graph)
- **Memory usage**: O(n + e) where e is edges in the dependency graph
- **Parallelism**: Limited by `max_workers` and available dependencies
- **Overhead**: Minimal locking (only for state updates, not during provider calls)

## Example Execution Trace

Given this flow:

```yaml
flow:
  - name: fetch_users
  - name: fetch_orders
  - name: join_data
    depends_on: [fetch_users, fetch_orders]
```

Execution proceeds:

1. **t=0**: Submit `fetch_users` and `fetch_orders` (both have `in_degree=0`)
2. **t=1**: `fetch_users` completes; decrement `join_data` in_degree to 1
3. **t=2**: `fetch_orders` completes; decrement `join_data` in_degree to 0
4. **t=2**: Submit `join_data` (now ready)
5. **t=3**: `join_data` completes; workflow done

The runner achieves maximum parallelism while respecting dependencies.

## References

- Implementation: `flowtoy/runner.py`
- Scheduler details: [Scheduler](scheduler.md)
- Configuration format: [Configuration Reference](/reference/configuration.md)
