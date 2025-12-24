---
title: Secret Redaction
description: Configure secret redaction in ProcessConnector
---

# Secret Redaction in Process Connector

## Overview

The ProcessConnector includes configurable secret redaction to prevent sensitive information from appearing in logs.

## Default Behavior (Safe by Default)

By default, **only the command name and argument count** are logged:

```yaml
sources:
  api_call:
    type: process
    configuration:
      command: ["curl", "-H", "Authorization: Bearer SECRET_TOKEN"]
```

**Logged output:**
```
INFO - ProcessConnector running command: ['curl', '<2 args>']
```

The actual arguments are **not logged** to prevent accidental secret leakage.

---

## Configuration Options

### 1. Redact by Argument Index

Specify which argument positions contain secrets:

```yaml
sources:
  secure_api:
    type: process
    configuration:
      command: ["curl", "-u", "user:password", "https://api.example.com"]
      redact_args: [2]  # Redact 3rd argument (index 2)
```

**Logged output:**
```
INFO - ProcessConnector running command: ['curl', '-u', '[REDACTED]', 'https://api.example.com']
```

### 2. Redact by Pattern Matching

Redact arguments containing specific substrings:

```yaml
sources:
  secure_api:
    type: process
    configuration:
      command: ["curl", "-H", "X-API-Key: secret_key_123", "-H", "Accept: application/json"]
      redact_patterns: ["X-API-Key:", "secret"]
```

**Logged output:**
```
INFO - ProcessConnector running command: ['curl', '-H', '[REDACTED]', '-H', 'Accept: application/json']
```

```{note}
Pattern matching is case-sensitive.
```

### 3. Combine Both Methods

Use both `redact_args` and `redact_patterns` together:

```yaml
sources:
  secure_tool:
    type: process
    configuration:
      command: ["tool", "--password", "SECRET", "--token", "TOKEN123", "--output", "file.txt"]
      redact_args: [2]  # Redact SECRET
      redact_patterns: ["TOKEN"]  # Redact TOKEN123
```

**Logged output:**
```
INFO - ProcessConnector running command: ['tool', '--password', '[REDACTED]', '--token', '[REDACTED]', '--output', 'file.txt']
```

### 4. Override for Debugging (Use with Caution)

To log the full command (including secrets) for debugging:

```yaml
sources:
  debug_api:
    type: process
    configuration:
      command: ["curl", "-H", "Authorization: Bearer TOKEN"]
      log_full_command: true
```

**Logged output:**
```
INFO - ProcessConnector running command: ['curl', '-H', 'Authorization: Bearer TOKEN']
```

```{warning}
Only use `log_full_command: true` in secure development environments. Never use in production.
```

---

## Best Practices

1. **Default is Safe**: Without any configuration, commands are logged safely (command name + arg count only)

2. **Be Specific**: When using `redact_args` or `redact_patterns`, be explicit about what needs redaction

3. **Test Your Config**: Run your flow with INFO logging enabled to verify secrets are properly redacted

4. **Document Secrets**: Comment your YAML to indicate which args/patterns contain secrets

5. **Never Use `log_full_command` in Production**: This should only be used temporarily for local debugging

---

## Examples

### Example 1: REST API with Bearer Token

```yaml
sources:
  github_api:
    type: process
    configuration:
      command: ["curl", "-H", "Authorization: Bearer ghp_xxxxxxxxxxxx", "https://api.github.com/user"]
      redact_patterns: ["Authorization:", "Bearer"]
```

### Example 2: Database Command with Credentials

```yaml
sources:
  mysql_query:
    type: process
    configuration:
      command: ["mysql", "-u", "admin", "-p", "secret_password", "-e", "SELECT 1"]
      redact_args: [4]  # Redact the password
```

### Example 3: SSH with Key File

```yaml
sources:
  remote_exec:
    type: process
    configuration:
      command: ["ssh", "-i", "/path/to/private_key", "user@host", "command"]
      redact_args: [2]  # Redact the key path if sensitive
```

---

## Troubleshooting

**Q: My secrets are still in logs!**
A: Check that you've configured either `redact_args` or `redact_patterns`. Without these, the default behavior only shows the command name.

**Q: Too much is being redacted**
A: Pattern matching is substring-based. Make your patterns more specific. For example, use `"Authorization:"` instead of `"auth"`.

**Q: I need to see the full command for debugging**
A: Temporarily add `log_full_command: true` to your source configuration, but **remove it** before committing to version control or deploying.

**Q: Can I use environment variables in redaction config?**
A: Not directly. Redaction config is static YAML. However, the command itself can use templating to inject environment variables.
