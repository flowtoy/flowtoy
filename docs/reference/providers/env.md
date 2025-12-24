---
title: Environment Variables Provider
description: Read environment variables and make them available to flows
---

The `env` provider reads environment variables and makes them available as source data in your flows.

## Configuration

```yaml
sources:
  my_config:
    type: env
    configuration:
      vars: [VAR1, VAR2, VAR3]
```

### Parameters

- `vars` (required): List of environment variable names to read

Note: The source name (`my_config` in the example above) can be any valid identifier. Choose a name that describes what the variables are used for.

## Behavior

The provider reads the specified environment variables and returns them as a dictionary. If an environment variable is not set, its value will be `null`.

## Referencing Environment Variables

Once defined as a source, environment variables can be referenced in other sources and flow steps using Jinja2 templating syntax: `{{ sources.<source_name>.<VAR_NAME> }}`.

### Example: Using in Other Sources

```yaml
sources:
  api_credentials:
    type: env
    configuration:
      vars: [API_BASE_URL, API_TOKEN]

  external_api:
    type: rest
    configuration:
      url: "{{ sources.api_credentials.API_BASE_URL }}"
      method: GET
      headers:
        Authorization: "Bearer {{ sources.api_credentials.API_TOKEN }}"
```

### Example: Using in Flow Steps

```yaml
sources:
  app_secrets:
    type: env
    configuration:
      vars: [API_KEY, DATABASE_URL]

  database_api:
    type: rest
    configuration:
      url: "{{ sources.app_secrets.DATABASE_URL }}"
      headers:
        Authorization: "Bearer {{ sources.app_secrets.API_KEY }}"

flow:
  - name: load_secrets
    source: app_secrets
    output:
      - name: config
        type: json

  - name: query_database
    source: database_api
    output:
      - name: response
        type: json
```

### Example: Database Connection with Dynamic Configuration

```yaml
sources:
  db_config:
    type: env
    configuration:
      vars: [DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]

  database_query:
    type: process
    configuration:
      command: ["psql", "-h", "{{ flows.get_config.db.DB_HOST }}",
                "-d", "{{ flows.get_config.db.DB_NAME }}",
                "-U", "{{ flows.get_config.db.DB_USER }}",
                "-c", "SELECT * FROM users"]
```

## Common Use Cases

- Reading API keys and tokens
- Loading database connection strings
- Accessing deployment-specific configuration
- Separating secrets from YAML files
