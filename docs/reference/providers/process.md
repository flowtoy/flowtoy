---
title: Process Provider
description: Execute external commands and scripts
---

# process Provider

The `process` provider executes external commands and scripts, capturing their output and return codes. It supports multiple ways to pass data to processes and parse their output.

## Configuration

```yaml
sources:
  my_script:
    type: process
    configuration:
      command: ["python3", "script.py"]
```

### Parameters

- `command` (required): Command to execute. Can be a string (shell-parsed) or array of arguments
- `pass_to` (optional): How to pass input payload to the process. Options:
  - `"arg"` (default): Append payload as final command argument
  - `"stdin"`: Pass payload via standard input
  - `"template"`: Use Jinja2 templating in command arguments
- `timeout` (optional): Timeout in seconds for command execution
- `log_full_command` (optional): If `true`, log the complete command (default: logs command name and arg count)
- `redact_args` (optional): List of argument indices to redact in logs (e.g., `[2, 3]`)
- `redact_patterns` (optional): List of patterns to redact in logs (e.g., `["Authorization:", "Bearer"]`)
- `template_strict` (optional): If `true` (default), raise error on undefined template variables

## Output Format

The provider returns:
- `data`: Parsed JSON from stdout if valid JSON, otherwise raw stdout text
- `code`: Process return code (0 = success)
- `success`: `true` if return code is 0, `false` otherwise
- `meta`: Contains `stderr`, `returncode`, and `status_code`
- `notes`: Error messages if process fails

## Usage Examples

### Basic Command Execution

```yaml
sources:
  list_files:
    type: process
    configuration:
      command: ["ls", "-la", "/tmp"]
```

### Command with String (Shell-Parsed)

```yaml
sources:
  disk_usage:
    type: process
    configuration:
      command: "df -h | grep /dev/sda1"
```

### Passing Input as Argument

```yaml
sources:
  user_lookup:
    type: process
    configuration:
      command: ["./lookup.sh"]
      pass_to: "arg"

flow:
  - name: lookup_user
    source: user_lookup
    input: "alice"
    output:
      - name: user_info
        type: json
```

The command executed will be: `./lookup.sh alice`

### Passing Input via stdin

```yaml
sources:
  json_processor:
    type: process
    configuration:
      command: ["python3", "process.py"]
      pass_to: "stdin"

flow:
  - name: process_data
    source: json_processor
    input: "{{ steps.fetch_data.result.data }}"
    output:
      - name: processed
        type: json
```

Example `process.py`:
```python
#!/usr/bin/env python3
import json
import sys

data = json.load(sys.stdin)
result = {
    "processed": True,
    "count": len(data.get("items", []))
}
print(json.dumps(result))
```

### Using Templates in Commands

```yaml
sources:
  api_curl:
    type: process
    configuration:
      command: ["curl", "-H", "Authorization: Bearer {{ json.token }}", "{{ json.url }}"]
      pass_to: "template"

flow:
  - name: call_api
    source: api_curl
    input: '{"token": "secret123", "url": "https://api.example.com/users"}'
    output:
      - name: api_response
        type: json
```

Available template variables:
- `{{ raw }}`: Raw string representation of input
- `{{ input }}`: Input payload as-is
- `{{ json }}`: Parsed JSON from input (if valid)
- `{{ jmespath('expression') }}`: Query JSON input with JMESPath

### Timeout Configuration

```yaml
sources:
  slow_script:
    type: process
    configuration:
      command: ["./slow_operation.sh"]
      timeout: 30
```

If the command exceeds 30 seconds, it will be terminated and return a timeout error.

### Secure Command Logging

By default, only the command name and argument count are logged to prevent leaking secrets:

```yaml
sources:
  secure_api_call:
    type: process
    configuration:
      command: ["curl", "-H", "Authorization: Bearer SECRET_TOKEN", "https://api.example.com"]
```

Logs: `ProcessProvider running command: ['curl', '<2 args>']`

#### Custom Redaction by Index

```yaml
sources:
  api_with_token:
    type: process
    configuration:
      command: ["curl", "-H", "Authorization: Bearer TOKEN123", "https://api.example.com"]
      redact_args: [2]
```

Logs: `ProcessProvider running command: ['curl', '-H', '[REDACTED]', 'https://api.example.com']`

#### Custom Redaction by Pattern

```yaml
sources:
  api_with_token:
    type: process
    configuration:
      command: ["curl", "-H", "Authorization: Bearer TOKEN123", "https://api.example.com"]
      redact_patterns: ["Authorization:", "Bearer"]
```

Logs: `ProcessProvider running command: ['curl', '-H', '[REDACTED]', 'https://api.example.com']`

#### Log Full Command (Not Recommended for Secrets)

```yaml
sources:
  debug_command:
    type: process
    configuration:
      command: ["echo", "hello"]
      log_full_command: true
```

## Common Use Cases

- Running custom data processing scripts
- Executing system commands for gathering information
- Calling legacy applications or tools
- Integrating with command-line utilities
- Running data transformation pipelines

## Error Handling

The provider handles various error scenarios:

- **Non-zero exit code**: Returns `success: false` with the exit code
- **Timeout**: Returns structured error with `timeout: true` in meta
- **Command not found**: Returns exception details in result
- **Invalid JSON output**: Falls back to returning raw stdout text

## Best Practices

1. **Use arrays for commands**: Prefer `["python3", "script.py"]` over `"python3 script.py"` to avoid shell injection
2. **Secure logging**: Use `redact_args` or `redact_patterns` when passing secrets
3. **Set timeouts**: Always set reasonable timeouts for long-running processes
4. **Output JSON**: Have scripts output JSON for easier data extraction in flows
5. **Check return codes**: Monitor the `success` field in flow steps
6. **Handle stderr**: Check `meta.stderr` for error diagnostics
