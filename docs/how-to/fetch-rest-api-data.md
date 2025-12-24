---
title: Fetch Data From a REST API
description: Retrieve and process data from REST APIs in your flows
---

# How to fetch data from a REST API

This guide shows you how to integrate REST APIs into your flowtoy flows to fetch and process external data.

## Fetch data from a single endpoint

To retrieve data from a REST API endpoint:

1. Define a REST source in your configuration:

```yaml
sources:
  users_api:
    type: rest
```

2. Create a flow step that calls the endpoint:

```yaml
flow:
  - name: get_user
    source: users_api
    input:
      url: https://jsonplaceholder.typicode.com/users/1
    output:
      - name: user
        type: json
```

3. Run the flow:

```bash
flowtoy run config.yaml
```

The `user` output will contain the complete JSON response from the API.

## Extract specific fields from the response

To extract only the fields you need:

```yaml
flow:
  - name: get_user
    source: users_api
    input:
      url: https://jsonplaceholder.typicode.com/users/1
    output:
      - name: username
        type: jmespath
        value: username
      - name: email
        type: jmespath
        value: email
```

This extracts just the `username` and `email` fields from the response.

## Chain API calls using previous results

To use data from one API call in another:

```yaml
sources:
  users_api:
    type: rest
  posts_api:
    type: rest

flow:
  - name: get_user
    source: users_api
    input:
      url: https://jsonplaceholder.typicode.com/users/1
    output:
      - name: user_id
        type: jmespath
        value: id

  - name: get_user_posts
    source: posts_api
    input:
      url: https://jsonplaceholder.typicode.com/posts?userId={{ flows.get_user.user_id }}
    output:
      - name: posts
        type: json
```

The second step automatically waits for the first step to complete.

## Add authentication headers

To authenticate your API requests:

```yaml
sources:
  customer_api:
    type: rest
    configuration:
      headers:
        Authorization: "Bearer {{ sources.env_vars.API_TOKEN }}"

flow:
  - name: fetch_protected_data
    source: customer_api
    input:
      url: https://api.example.com/protected-endpoint
    output:
      - name: data
        type: json
```

See [How to manage secrets](manage-secrets.md) for secure credential handling.

## Handle API errors gracefully

To continue your flow even if an API call fails:

```yaml
sources:
  external_api:
    type: rest

flow:
  - name: optional_api_call
    source: external_api
    on_error: continue
    input:
      url: https://api.example.com/optional-data
    output:
      - name: optional_data
        type: json

  - name: required_step
    source: external_api
    input:
      url: https://api.example.com/required-data
    output:
      - name: required_data
        type: json
```

The `required_step` will execute even if `optional_api_call` fails.

## Related

- [REST provider reference](../reference/providers/rest.md)
- [Templating reference](../reference/templating.md)
- [Error handling in flows](../reference/flows.md#error-handling)
