---
title: Run Steps in Parallel
description: Speed up flows by executing independent steps concurrently
---

# How to run steps in parallel

This guide shows you how to optimize your flows by running independent steps in parallel.

## Automatic parallel execution

flowtoy automatically runs steps in parallel when they don't depend on each other:

```yaml
sources:
  ecommerce_api:
    type: rest

flow:
  # These three steps run in parallel automatically
  - name: fetch_users
    source: ecommerce_api
    input:
      url: https://api.example.com/users
    output:
      - name: users
        type: json

  - name: fetch_products
    source: ecommerce_api
    input:
      url: https://api.example.com/products
    output:
      - name: products
        type: json

  - name: fetch_orders
    source: ecommerce_api
    input:
      url: https://api.example.com/orders
    output:
      - name: orders
        type: json
```

No configuration needed - these steps have no dependencies, so they execute concurrently.

## Mix parallel and sequential steps

Combine parallel and sequential execution in the same flow:

```yaml
sources:
  oauth_service:
    type: rest
  data_service:
    type: rest
  etl_script:
    type: process

flow:
  # Step 1: Runs first
  - name: authenticate
    source: oauth_service
    input:
      url: https://api.example.com/auth
    output:
      - name: token
        type: jmespath
        value: access_token

  # Steps 2 & 3: Run in parallel after step 1 completes
  - name: fetch_users
    source: data_service
    input:
      url: https://api.example.com/users
      headers:
        Authorization: "Bearer {{ flows.authenticate.token }}"
    output:
      - name: users
        type: json

  - name: fetch_products
    source: data_service
    input:
      url: https://api.example.com/products
      headers:
        Authorization: "Bearer {{ flows.authenticate.token }}"
    output:
      - name: products
        type: json

  # Step 4: Runs after steps 2 & 3 complete
  - name: combine_data
    source: etl_script
    depends_on:
      - fetch_users
      - fetch_products
    input:
      command: ["python", "merge.py"]
    output:
      - name: combined
        type: json
```

Execution order:
1. `authenticate` runs first
2. `fetch_users` and `fetch_products` run in parallel (both reference `authenticate`)
3. `combine_data` runs after both complete (explicit `depends_on`)

## Control parallelism with explicit dependencies

Force sequential execution when needed using `depends_on`:

```yaml
sources:
  database_admin_api:
    type: rest

flow:
  - name: create_database
    source: database_admin_api
    input:
      url: https://api.example.com/databases
      method: POST
    output:
      - name: db_id
        type: jmespath
        value: id

  - name: create_schema
    source: database_admin_api
    depends_on:
      - create_database
    input:
      url: https://api.example.com/databases/{{ flows.create_database.db_id }}/schema
      method: POST
    output:
      - name: schema_id
        type: json
```

Even though `create_schema` doesn't reference data from `create_database` in templates, it waits due to `depends_on`.

## Limit concurrent workers

Control maximum parallelism with the `--max-workers` option:

```bash
# Run with up to 2 concurrent steps
flowtoy run config.yaml --max-workers 2

# Run with up to 10 concurrent steps
flowtoy run config.yaml --max-workers 10
```

Default: 4 workers or (active threads + 3), whichever is smaller.

## When to use parallel execution

**Good candidates for parallelism:**
- Fetching data from multiple independent APIs
- Running multiple database queries
- Processing different data sources simultaneously
- Executing independent data transformations

**Avoid parallelism when:**
- Steps modify shared resources
- Order of execution matters for correctness
- Rate limits apply to your APIs

## Monitor parallel execution

Use the web UI to visualize parallel execution:

```bash
flowtoy webui config.yaml
```

Open http://localhost:8000 to see steps running concurrently in real-time.

## Related

- [Dependencies in flows](../reference/flows.md#dependencies)
- [CLI reference](../reference/cli.md)
- [Web UI reference](../reference/api/web-ui.md)
