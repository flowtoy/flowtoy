---
title: Design Philosophy
description: Understanding the principles behind flowtoy's design
---

# Design Philosophy

flowtoy is built around two core principles: **simplicity** and **extensibility**. These principles guide every design decision in the project.

## Simplicity

### Minimal Core

The flowtoy core intentionally remains small and focused. It provides:

- A YAML-based configuration format that's human-readable and version-controllable
- A dependency-aware parallel scheduler for executing workflow steps
- Three essential built-in providers (REST, Process, Environment)
- A Jinja2 templating engine for dynamic values

This minimal approach means:
- **Fewer dependencies** - The core only depends on what's absolutely necessary
- **Easier to understand** - New users can grasp the entire system quickly
- **Lower maintenance burden** - Less code means fewer bugs and easier updates
- **Faster installation** - No heavy dependencies unless you need them

### YAML Over Code

flowtoy uses YAML configuration rather than requiring users to write code. This decision reflects a tradeoff:

**Benefits:**
- Declarative workflows are easier to read and audit
- Non-developers can understand and modify flows
- Version control diffs are meaningful and reviewable
- No need to learn a DSL or programming constructs

**Tradeoffs:**
- Complex conditional logic can be harder to express
- Dynamic behavior requires templating rather than direct code
- Some power users might prefer programmatic control

The YAML approach serves flowtoy's target use case: orchestrating well-defined, repeatable workflows where clarity and maintainability matter more than dynamic complexity.

### One Responsibility Per Component

Each component in flowtoy has a single, clear purpose:

- **Runner** loads configuration and coordinates execution
- **Scheduler** manages parallel execution and dependencies
- **Providers** interface with external systems
- **Templating** handles dynamic value interpolation

This separation means you can understand each piece independently, and changes to one component rarely ripple through the system.

## Extensibility

### Extension Architecture

While the core is minimal, flowtoy is designed to grow through extensions rather than by adding features to the core.

The provider extension system uses Python entry points, which means:
- **No central registry** - Providers register themselves when installed
- **Lazy loading** - Providers are only imported when actually used
- **Independent development** - Anyone can publish a provider package
- **Zero core impact** - New providers don't affect core code or dependencies

This architecture allows the ecosystem to expand without bloating the base installation.

### Provider Interface

The provider interface is deliberately simple:

```python
class Provider:
    def __init__(self, configuration: dict):
        """Initialize with configuration from sources section."""
        pass

    def call(self, input_payload=None) -> dict:
        """Execute and return standardized result."""
        pass
```

This simplicity means:
- **Easy to implement** - Creating a provider requires minimal boilerplate
- **Easy to test** - Providers can be tested in isolation
- **Consistent behavior** - All providers follow the same contract
- **Predictable results** - Standardized return format across all providers

### Entry Point Discovery

The entry point mechanism provides extensibility without coupling:

```toml
[project.entry-points."flowtoy.providers"]
myprovider = "flowtoy_myprovider:MyProvider"
```

When installed, providers automatically become available. Users don't need to:
- Modify core code
- Update configuration files with extension paths
- Manually register providers

This "install and use" model removes friction from extending flowtoy.

## Balancing Simplicity and Extensibility

These two principles sometimes create tension:

### When to Extend the Core vs Create an Extension

**Built into core when:**
- The functionality is universally needed (REST, Process, Env providers)
- It affects the execution model (parallel scheduling, dependency resolution)
- It's foundational to the system (templating, configuration loading)

**Implemented as extension when:**
- The functionality serves specific use cases (databases, message queues)
- It requires external dependencies (cloud SDKs, specialized protocols)
- Different users might want different implementations

### Configuration Complexity

flowtoy configuration can get complex as workflows grow. This is an intentional tradeoff:
- Simple workflows remain very simple
- Complex workflows are possible but might become verbose
- Users who need programmatic control should consider alternative tools

The design accepts this limitation rather than compromising the clarity of the YAML format.

### Error Handling Philosophy

flowtoy distinguishes between:
- **Configuration errors** (raise exceptions, fail fast) - Problems in YAML or missing required fields
- **Runtime errors** (return structured results) - Problems during execution like network failures

This approach provides:
- **Clear separation** between setup problems and execution problems
- **Graceful degradation** for runtime issues
- **Actionable feedback** at configuration time

## Alternatives and When Not to Use flowtoy

Understanding flowtoy's design helps identify when it's the right tool:

**Use flowtoy when:**
- You need orchestration for well-defined, repeatable workflows
- Clarity and maintainability are priorities
- You want minimal setup and dependencies
- YAML configuration fits your team's skills

**Consider alternatives when:**
- You need complex branching logic or dynamic workflows
- You require extensive conditional execution
- You need features like retries, distributed execution, or persistent state
- You prefer programmatic workflow definition

Tools like Airflow, Prefect, or Dagster offer more features at the cost of more complexity. flowtoy intentionally stays simple.

## Looking Forward

flowtoy's design principles create a foundation that can grow sustainably:

- The minimal core remains stable and maintainable
- The extension ecosystem can expand independently
- New providers don't impact existing users
- The system remains understandable even as it grows

This approach trades immediate feature richness for long-term maintainability and clarity.
