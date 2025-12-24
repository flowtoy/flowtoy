---
title: REST Provider
description: Make HTTP/REST API calls
---

# rest Provider

The `rest` provider makes HTTP/REST API calls and captures responses. It supports various HTTP methods, headers, query parameters, and request bodies.

## Configuration

```yaml
sources:
  my_api:
    type: rest
    configuration:
      url: https://api.example.com/endpoint
      method: GET
```

### Parameters

- `url` (required): The URL to call
- `method` (optional): HTTP method - `GET` (default), `POST`, `PUT`, `DELETE`, `PATCH`, etc.
- `headers` (optional): Dictionary of HTTP headers to send
- `input_mode` (optional): How to pass input payload to the request. Options:
  - `"parameter"`: Add input as a URL query parameter
  - `"body"`: Send input as JSON request body
- `param_name` (optional): Query parameter name when `input_mode: "parameter"` (default: `"id"`)

## Output Format

The provider returns:
- `data`: Parsed JSON from response body if valid JSON, otherwise raw response text
- `code`: HTTP status code (e.g., 200, 404, 500)
- `success`: `true` if status code is 2xx, `false` otherwise
- `meta`: Contains `status_code` and response `headers`
- `notes`: Error messages for non-2xx responses

## Usage Examples

### Basic GET Request

```yaml
sources:
  user_api:
    type: rest
    configuration:
      url: https://jsonplaceholder.typicode.com/users/1
      method: GET

flow:
  - name: fetch_user
    source: user_api
    output:
      - name: user_data
        type: json
```

### GET Request with Headers

```yaml
sources:
  auth_credentials:
    type: env
    configuration:
      vars: [API_TOKEN]

  protected_api:
    type: rest
    configuration:
      url: https://api.example.com/data
      method: GET
      headers:
        Authorization: "Bearer {{ sources.auth_credentials.API_TOKEN }}"
        Content-Type: "application/json"

flow:
  - name: load_credentials
    source: auth_credentials
    output:
      - name: token
        type: json

  - name: call_protected_api
    source: protected_api
    output:
      - name: api_response
        type: json
```

### GET Request with Query Parameters from Input

```yaml
sources:
  posts_api:
    type: rest
    configuration:
      url: https://jsonplaceholder.typicode.com/posts
      method: GET
      input_mode: parameter
      param_name: userId

flow:
  - name: fetch_user
    source: user_api
    output:
      - name: user_id
        type: jmespath
        value: "id"

  - name: fetch_user_posts
    source: posts_api
    input: "{{ steps.fetch_user.user_id }}"
    output:
      - name: posts
        type: json
```

This will call: `https://jsonplaceholder.typicode.com/posts?userId=1`

### POST Request with JSON Body

```yaml
sources:
  create_user_api:
    type: rest
    configuration:
      url: https://api.example.com/users
      method: POST
      headers:
        Content-Type: "application/json"
      input_mode: body

flow:
  - name: create_user
    source: create_user_api
    input: {"name": "Alice", "email": "alice@example.com"}
    output:
      - name: created_user
        type: json
```

### PUT Request for Updates

```yaml
sources:
  update_user_api:
    type: rest
    configuration:
      url: https://api.example.com/users/123
      method: PUT
      headers:
        Content-Type: "application/json"
        Authorization: "Bearer {{ sources.auth.API_TOKEN }}"
      input_mode: body

flow:
  - name: update_user
    source: update_user_api
    input: {"name": "Alice Updated", "email": "alice.new@example.com"}
    output:
      - name: updated_user
        type: json
```

### DELETE Request

```yaml
sources:
  delete_user_api:
    type: rest
    configuration:
      url: https://api.example.com/users/123
      method: DELETE
      headers:
        Authorization: "Bearer {{ sources.auth.API_TOKEN }}"

flow:
  - name: delete_user
    source: delete_user_api
    output:
      - name: deletion_result
        type: json
```

### Dynamic URL with Templating

You can use Jinja2 templating in the URL configuration:

```yaml
sources:
  config_vars:
    type: env
    configuration:
      vars: [API_BASE_URL, USER_ID]

  dynamic_api:
    type: rest
    configuration:
      url: "{{ sources.config_vars.API_BASE_URL }}/users/{{ sources.config_vars.USER_ID }}"
      method: GET
```

### Handling API Responses

```yaml
sources:
  api_call:
    type: rest
    configuration:
      url: https://api.example.com/data
      method: GET

flow:
  - name: call_api
    source: api_call
    output:
      - name: success
        type: jmespath
        value: "success"
      - name: status_code
        type: jmespath
        value: "code"
      - name: response_data
        type: jmespath
        value: "data"
      - name: error_message
        type: jmespath
        value: "notes[0]"
```

### Multiple APIs in Parallel

```yaml
sources:
  users_api:
    type: rest
    configuration:
      url: https://jsonplaceholder.typicode.com/users
      method: GET

  posts_api:
    type: rest
    configuration:
      url: https://jsonplaceholder.typicode.com/posts
      method: GET

flow:
  - name: fetch_users
    source: users_api
    output:
      - name: users
        type: json

  # This runs in parallel with fetch_users
  - name: fetch_posts
    source: posts_api
    output:
      - name: posts
        type: json
```

## Common Use Cases

- Fetching data from REST APIs
- Authenticating with API tokens or bearer tokens
- Creating, updating, or deleting resources via HTTP methods
- Integrating with third-party services (GitHub, Slack, AWS, etc.)
- Chaining API calls where one response feeds into another

## Error Handling

The provider handles various error scenarios:

- **Non-2xx status codes**: Returns `success: false` with status code in `notes`
- **Network errors**: Returns exception details in result
- **Connection timeouts**: Returns structured error result
- **Invalid JSON responses**: Falls back to returning raw response text

### Example: Handling Errors

```yaml
flow:
  - name: call_api
    source: my_api
    on_error: continue
    output:
      - name: result
        type: json

  - name: check_result
    source: processor
    input: |
      {% if steps.call_api.result.success %}
        Success: {{ steps.call_api.result.data }}
      {% else %}
        Error: {{ steps.call_api.result.notes[0] }}
      {% endif %}
```

## Response Metadata

Access response metadata in flow steps:

```yaml
flow:
  - name: api_call
    source: my_api
    output:
      - name: data
        type: jmespath
        value: "data"
      - name: status
        type: jmespath
        value: "meta.status_code"
      - name: content_type
        type: jmespath
        value: "meta.headers.'Content-Type'"
```

## Best Practices

1. **Use environment variables for secrets**: Store API keys and tokens in environment variables via the `env` provider
2. **Set appropriate headers**: Always include `Content-Type` for POST/PUT requests
3. **Handle errors gracefully**: Use `on_error: continue` and check `success` field
4. **Use input_mode effectively**: Choose `parameter` for GET requests with IDs, `body` for POST/PUT with data
5. **Parse responses carefully**: Use JMESPath to extract specific fields from JSON responses
6. **Consider rate limits**: Be aware of API rate limits when making multiple calls
7. **Use descriptive source names**: Name sources after the API or resource (e.g., `github_repos`, `slack_messages`)
