---
title: Architecture Overview
description: Understanding flowtoy's design and components
---

# Architecture Overview

flowtoy is designed as a minimal, modular workflow orchestration system.

## Core Components

### Runner

The `LocalRunner` is responsible for:
- Loading configuration
- Building dependency graph
- Scheduling and executing steps
- Managing state and outputs

See [Runner](runner.md) for details.

### Scheduler

The parallel scheduler:
- Analyzes step dependencies
- Executes independent steps in parallel
- Manages worker thread pool
- Enforces execution order

See [Scheduler](scheduler.md) for details.

### Providers

Providers provide interfaces to external systems:
- Built-in providers (rest, process, env)
- Extension system for extensibility
- Lazy loading and discovery

See [Extension System](extensions.md) for details.

### Templating

Jinja2-based templating engine:
- Reference previous step outputs
- Dynamic configuration
- Filters and expressions

## Design Principles

1. **Simplicity**: Minimal core, extensible via extensions
2. **Modularity**: Clear separation of concerns
3. **Performance**: Parallel execution where possible
4. **Reliability**: Structured error handling

## Next Steps

- [Runner Design](runner.md)
- [Parallel Scheduler](scheduler.md)
- [Extension Architecture](extensions.md)
