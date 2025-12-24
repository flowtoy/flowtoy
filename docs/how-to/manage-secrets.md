---
title: Manage Secrets and Credentials
description: Securely handle sensitive data in your flows
---

# How to manage secrets and credentials

This guide shows you how to securely handle API keys, passwords, and other sensitive credentials in flowtoy.

## Store secrets in environment variables

The safest way to handle secrets is to keep them out of your YAML files entirely:

1. Create an environment source:

```yaml
sources:
  env_secrets:
    type: env
    configuration:
      vars:
        - API_TOKEN
        - DATABASE_PASSWORD
```

2. Set the environment variables before running:

```bash
export API_TOKEN="your-secret-token"
export DATABASE_PASSWORD="your-password"
flowtoy run config.yaml
```

3. Reference the secrets in your flows:

```yaml
sources:
  customer_api:
    type: rest
    configuration:
      headers:
        Authorization: "Bearer {{ sources.env_secrets.API_TOKEN }}"

flow:
  - name: fetch_data
    source: customer_api
    input:
      url: https://api.example.com/data
    output:
      - name: data
        type: json
```

## Separate secrets from configuration

Keep secrets in a separate file that's excluded from version control:

1. Create your main config (`flow.yaml`):

```yaml
sources:
  payment_api:
    type: rest
    configuration:
      base_url: https://api.example.com

flow:
  - name: fetch_data
    source: payment_api
    input:
      url: "{{ sources.payment_api.base_url }}/data"
    output:
      - name: data
        type: json
```

2. Create a secrets file (`secrets.yaml`):

```yaml
sources:
  payment_api:
    configuration:
      headers:
        Authorization: "Bearer sk-1234567890"
```

3. Add `secrets.yaml` to `.gitignore`:

```
secrets.yaml
*.secret.yaml
```

4. Run with both files (configs are merged):

```bash
flowtoy run flow.yaml secrets.yaml
```

## Use secret redaction

flowtoy automatically redacts sensitive values in result metadata:

**Keys that are automatically redacted:**
- Any key containing: `password`, `secret`, `token`, or `pw` (case-insensitive)

Examples of keys that get redacted:
- `password`, `api_password`, `bind_password`
- `secret`, `client_secret`, `shared_secret`
- `token`, `access_token`, `api_token`
- `pw`, `db_pw`

Example result with redaction:
```python
{
  'status': {'success': True, 'code': 200, 'notes': []},
  'data': {...},
  'meta': {'api_token': '<redacted>', 'user': 'john'}
}
```

**Process provider logging:**
By default, process commands only log the command name and argument count (e.g., `['curl', '<2 args>']`) to prevent accidental secret leakage in logs.

See [Secret redaction reference](../reference/secret-redaction.md) for process provider redaction configuration.

## Provide example configuration

For team collaboration, provide a template without secrets:

`flow.yaml.example`:
```yaml
sources:
  env_secrets:
    type: env
    configuration:
      vars:
        - API_TOKEN  # Get from https://dashboard.example.com/api-keys
        - DATABASE_PASSWORD  # Ask team lead

  billing_api:
    type: rest
    configuration:
      headers:
        Authorization: "Bearer {{ sources.env_secrets.API_TOKEN }}"
```

Team members can copy this to `secrets.yaml` and fill in their values.

## Related

- [Environment provider reference](../reference/providers/env.md)
- [Secret redaction reference](../reference/secret-redaction.md)
- [Configuration reference](../reference/configuration.md)
