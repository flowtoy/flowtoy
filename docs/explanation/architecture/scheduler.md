---
title: Parallel Scheduler
description: How flowtoy achieves concurrent step execution
---

# Parallel Scheduler

flowtoy's parallel scheduler is the core algorithm that enables concurrent workflow execution. It's not a separate class—rather, it's the execution logic embedded in `LocalRunner.run()` that implements parallel dependency resolution.

## Goals

The scheduler aims to:

1. **Maximize parallelism** - Execute independent steps concurrently
2. **Respect dependencies** - Never run a step before its dependencies complete
3. **Handle failures gracefully** - Apply error policies when steps fail
4. **Minimize overhead** - Use efficient data structures and avoid busy loops

## Scheduling Algorithm

The scheduler uses a **topological sort with parallel execution** algorithm based on Kahn's algorithm.

### Core Data Structures

```python
# Dependency tracking
deps: Dict[str, set]         # step -> set of steps it depends on
dependents: Dict[str, set]   # step -> set of steps that depend on it
in_degree: Dict[str, int]    # step -> count of unsatisfied dependencies

# Execution management
ready_q: Queue               # Steps ready to execute
futures: Dict[Future, str]   # Running tasks mapped to step names
executor: ThreadPoolExecutor # Thread pool for parallel execution
```

### Algorithm Overview

1. **Initialize**: Calculate `in_degree` for each step (count of dependencies)
2. **Seed**: Enqueue all steps with `in_degree == 0` into `ready_q`
3. **Loop**:
   - Submit ready steps to executor
   - Wait for any step to complete
   - On completion, decrement `in_degree` for dependents
   - Enqueue newly ready steps (those with `in_degree == 0`)
   - Repeat until all steps complete or error occurs

This approach guarantees:

- Steps execute only after dependencies complete
- Maximum parallelism (limited only by `max_workers` and available dependencies)
- Correct execution order

## Dependency Resolution

### Topological Sort

The scheduler sorts steps into execution order at runtime. Unlike static sorting, the dynamic approach:

- Handles multiple independent branches naturally
- Adapts to step completion timing
- Supports max parallelism without pre-computing levels

### In-Degree Tracking

Each step's `in_degree` represents unsatisfied dependencies:

```
in_degree = 0: Ready to execute
in_degree > 0: Waiting for dependencies
in_degree < 0: Skipped (dependency failed)
```

When a step completes successfully, the scheduler decrements `in_degree` for each dependent. When `in_degree` reaches zero, the step is ready.

### Example Execution

Consider this dependency graph:

```
    A     B
     \   /
      \ /
       C
       |
       D
```

Execution timeline:

- **t=0**: `in_degree: {A:0, B:0, C:2, D:1}` → Submit A and B
- **t=1**: A completes → `in_degree: {C:1, D:1}`
- **t=2**: B completes → `in_degree: {C:0, D:1}` → Submit C
- **t=3**: C completes → `in_degree: {D:0}` → Submit D
- **t=4**: D completes → Done

The scheduler achieves optimal parallelism: A and B run concurrently, then C, then D.

## Thread Pool Management

The scheduler uses Python's `ThreadPoolExecutor` for concurrency.

### Worker Count

Default worker count:

```python
max_workers = min(4, threading.active_count() + 3)
```

This heuristic:

- Caps at 4 workers to avoid excessive context switching
- Scales based on existing thread count (important for embedded use)
- Can be overridden via `runner.max_workers` configuration

### Task Submission

The scheduler submits each step as a separate task:

```python
def submit_step(step_name: str):
    def task():
        # Execute step (render templates, call provider, process results)
        return success, exception, error_policy
    return executor.submit(task)
```

Tasks run independently in the thread pool. The scheduler tracks them via the `futures` dictionary.

### Completion Handling

The scheduler waits for task completion using:

```python
done, pending = cf_wait(futures.keys(), timeout=0.1, return_when=FIRST_COMPLETED)
```

This approach:

- Returns immediately when any task completes
- Uses a short timeout (0.1s) to avoid blocking forever
- Allows the scheduler to process completions as they happen

## Error Propagation

When a step fails, the scheduler applies error policies to decide what happens next.

### Per-Step Error Policies

Each step can specify `on_error`:

- **fail**: Stop execution; skip all descendants
- **skip**: Skip this step and descendants if a dependency fails
- **continue**: Run this step even if dependencies failed

### Failure Cascade

When a step fails with `on_error: fail`:

1. Scheduler sets `error_occurred` event
2. Clears `ready_q` (no new submissions)
3. Clears `futures` (cancels pending tasks)
4. Marks all descendants as `skipped`
5. Exits the scheduling loop

When a step fails with `on_error: skip`:

1. Scheduler marks the step's dependents as `skipped`
2. Recursively marks descendants as `skipped`
3. Sets their `in_degree = -1` (ensures they won't run)
4. Continues executing other branches

When a step fails with `on_error: continue`:

1. Dependent steps run normally
2. Missing data causes template rendering errors (which they can handle)

### Skip Propagation

The `skip_descendants()` helper recursively marks steps as skipped:

```python
def skip_descendants(n):
    for dep in dependents.get(n, []):
        if in_degree.get(dep, 0) >= 0:
            in_degree[dep] = -1  # Mark as skipped
            update_status(dep, state="skipped")
            skip_descendants(dep)  # Recurse
```

This ensures that when a step is skipped, all steps that transitively depend on it are also skipped.

## Performance Optimizations

### Lock Minimization

The scheduler minimizes lock contention by:

- Only locking during state updates (`self.flows`, `self.status`)
- Taking snapshots before template rendering (rendering happens outside lock)
- Using atomic status update helpers

This design allows maximum parallel execution without race conditions.

### Busy Loop Avoidance

The scheduler uses efficient waiting:

```python
done, _ = cf_wait(futures.keys(), timeout=0.1, return_when=FIRST_COMPLETED)
if not done:
    time.sleep(0.05)  # Avoid busy loop
```

If no tasks complete within 0.1s, the scheduler sleeps briefly before checking again. This prevents CPU spinning while waiting for completions.

### Queue-Based Ready List

Using a `Queue` for ready steps:

- Provides thread-safe enqueue/dequeue
- Efficiently blocks when empty
- Supports atomic clear operations (for error handling)

## Concurrency Model

### Thread Safety Guarantees

The scheduler ensures:

1. **Dependency order preserved**: Steps run only after dependencies complete
2. **No data races**: Shared state protected by locks
3. **Consistent snapshots**: Template rendering uses frozen copies of state
4. **Atomic status updates**: State transitions are indivisible

### Limitations

The scheduler does NOT provide:

- **Distributed execution**: All steps run on the local machine
- **Step retry logic**: Failed steps are not automatically retried
- **Resource limits**: No memory or CPU quotas per step
- **Step cancellation**: Running steps cannot be interrupted

These features are intentionally omitted to keep flowtoy simple.

## Comparison to Other Schedulers

### vs. Airflow

Airflow uses:

- Database-backed state (persistent across restarts)
- Distributed worker pools (Celery or Kubernetes)
- Rich retry/backoff logic
- Web UI for monitoring

flowtoy uses:

- In-memory state (simpler but not persistent)
- Local thread pool (simpler but not distributed)
- No automatic retry (fails fast)
- Optional TUI/Web UI

Tradeoff: Airflow is more powerful but much more complex to set up and maintain.

### vs. make

`make` uses:

- File timestamps to determine what's stale
- Process-based parallelism (`-j` flag)
- Filesystem-based dependency tracking

flowtoy uses:

- Explicit dependency declarations
- Thread-based parallelism (more lightweight)
- Data-based dependencies (pass outputs between steps)

Tradeoff: `make` is simpler for file-based tasks, flowtoy is better for API/data workflows.

## Observability

The scheduler provides visibility through:

### Status API

The `RunStatus` object tracks:

- Per-step state (pending, running, succeeded, failed, skipped)
- Timestamps (started_at, ended_at)
- Error messages

This data powers the TUI and Web UI displays.

### Logging

The scheduler logs key events:

```
INFO: runner starting: 5 steps
INFO: starting step: fetch_users
INFO: step succeeded: fetch_users
ERROR: step failed: process_users
```

Use `--log-level DEBUG` for detailed tracing.

## Configuration

The scheduler respects these settings:

```yaml
runner:
  max_workers: 4      # Thread pool size
  on_error: fail      # Default error policy
```

Individual steps can override error policy:

```yaml
flow:
  - name: optional_step
    on_error: continue
```

## Future Enhancements

Potential scheduler improvements (not currently planned):

1. **Priority scheduling**: Execute high-priority steps first
2. **Resource quotas**: Limit memory/CPU per step
3. **Retry logic**: Automatically retry failed steps with backoff
4. **Distributed execution**: Run steps across multiple machines
5. **Dynamic DAG updates**: Add/remove steps during execution

These would increase complexity significantly, so they're not in scope for flowtoy's minimal design.

## References

- Implementation: `flowtoy/runner.py` (lines 288-391)
- Runner design: [Runner](runner.md)
- Thread safety: `_lock` usage in `LocalRunner`
- Error handling: [On-Error Policy Reference](/reference/configuration.md)
