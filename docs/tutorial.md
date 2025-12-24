---
title: Tutorial
description: Build a complete data integration flow step-by-step
downloads:
  - file: tutorial-files/step1.yaml
    title: step1.yaml
    filename: step1.yaml
  - file: tutorial-files/step2.yaml
    title: step2.yaml
    filename: step2.yaml
  - file: tutorial-files/step3.yaml
    title: step3.yaml
    filename: step3.yaml
  - file: tutorial-files/step4.yaml
    title: step4.yaml
    filename: step4.yaml
  - file: tutorial-files/process.py
    title: process.py
    filename: process.py
  - file: tutorial-files/step5.yaml
    title: step5.yaml
    filename: step5.yaml
  - file: tutorial-files/step6.yaml
    title: step6.yaml
    filename: step6.yaml
  - file: tutorial-files/step7.yaml
    title: step7.yaml
    filename: step7.yaml
---

This tutorial walks you through building a realistic data integration flow that fetches data from multiple sources, processes it, and combines the results.

## Scenario

We'll build a flow that:
1. Fetches a list of users from a REST API
2. For each user, looks up additional details from another API
3. Runs a local script to process the combined data
4. Outputs the final results

## Prerequisites

This tutorial assumes you have flowtoy installed. If not, see [Getting Started](getting-started.md) for installation instructions.

Create a project directory for the tutorial:

```bash
mkdir flowtoy-tutorial
cd flowtoy-tutorial
```

## Step 1: Create a Simple Flow

Download [step1.yaml](tutorial-files/step1.yaml) or create it with the following content:

```{literalinclude} tutorial-files/step1.yaml
:language: yaml
```

Run it:

```bash
flowtoy run step1.yaml
```

You should see output showing the URL that was called:

```python
{'test_connection': {'url': 'https://httpbin.org/get'}}
```

This confirms flowtoy can reach external APIs.

## Step 2: Fetch User Data

Let's fetch some mock user data. Download [step2.yaml](tutorial-files/step2.yaml):

```{literalinclude} tutorial-files/step2.yaml
:language: yaml
```

Run it:

```bash
flowtoy run step2.yaml -j
```

You'll see JSON output with user data:

```json
{
  "fetch_users": {
    "users": [
      {
        "id": 1,
        "name": "Leanne Graham",
        "username": "Bret",
        "email": "Sincere@april.biz",
        ...
      },
      ...
    ],
    "user_count": 10,
    "first_user_id": 1
  }
}
```

Notice we extracted three outputs: the full user list, the count, and the first user's ID.

## Step 3: Add Dependencies and Sequential Steps

Now let's fetch details for a specific user. Download [step3.yaml](tutorial-files/step3.yaml):

```{literalinclude} tutorial-files/step3.yaml
:language: yaml
```

Note that `fetch_user_posts` automatically depends on `fetch_users` because it references data from that step.

Run it:

```bash
flowtoy run step3.yaml -j
```

You'll see posts for the first user:

```json
{
  "fetch_users": {
    "first_user_id": 1
  },
  "fetch_user_posts": {
    "posts": [
      {
        "userId": 1,
        "id": 1,
        "title": "sunt aut facere repellat provident...",
        "body": "quia et suscipit..."
      },
      ...
    ],
    "post_count": 10
  }
}
```

Notice `fetch_user_posts` ran after `fetch_users` because it references `flows.fetch_users.first_user_id`.

## Step 4: Add Parallel Steps

Let's fetch multiple data sources in parallel. Download [step4.yaml](tutorial-files/step4.yaml):

```{literalinclude} tutorial-files/step4.yaml
:language: yaml
```

Run it:

```bash
flowtoy run step4.yaml
```

Watch the output - you'll see both `fetch_posts` and `fetch_todos` execute simultaneously:

```python
{
  'fetch_user': {'user_id': 1},
  'fetch_posts': {'post_count': 10},
  'fetch_todos': {'todo_count': 20}
}
```

Since `fetch_posts` and `fetch_todos` both depend only on `fetch_user`, flowtoy executes them in parallel.

## Step 5: Process Data with a Script

Let's create a Python script to process our data. Download [process.py](tutorial-files/process.py):

```{literalinclude} tutorial-files/process.py
:language: python
```

If you downloaded the file, make it executable:

```bash
chmod +x process.py
```

Download [step5.yaml](tutorial-files/step5.yaml):

```{literalinclude} tutorial-files/step5.yaml
:language: yaml
```

Run it:

```bash
flowtoy run step5.yaml -j
```

You'll see the processed data:

```json
{
  "fetch_user": {
    "user_id": 1,
    "username": "Bret"
  },
  "process_data": {
    "summary": "Processed data for user Bret (ID: 1)"
  }
}
```

The `process_data` step ran your Python script with the user data as input.

## Step 6: Add Error Handling

Let's add error handling for cases where an API call might fail. Download [step6.yaml](tutorial-files/step6.yaml):

```{literalinclude} tutorial-files/step6.yaml
:language: yaml
```

Run it:

```bash
flowtoy run step6.yaml -j
```

Even though `fetch_invalid_endpoint` fails, the flow continues:

```json
{
  "fetch_user": {
    "user_id": 1
  },
  "fetch_invalid_endpoint": null,
  "fetch_user_posts": {
    "post_count": 10
  }
}
```

The failed step returns `null`, but `fetch_user_posts` still executes because we set `on_error: continue`.

## Step 7: Use Environment Variables

Create a secrets file. Create `.env`:

```bash
API_KEY=your-secret-key-here
```

Download [step7.yaml](tutorial-files/step7.yaml):

```{literalinclude} tutorial-files/step7.yaml
:language: yaml
```

Run it (this will fail without a real API, but shows the pattern):

```bash
export API_KEY=test-key
flowtoy run step7.yaml -j
```

The output shows that environment variables are loaded and available:

```json
{
  "load_secrets": {
    "API_KEY": "***REDACTED***"
  },
  "fetch_with_auth": {
    "status": "authenticated"
  }
}
```

Notice the API key is automatically redacted in the output for security.

## Step 8: Monitor with Web UI

Run a flow with the web UI:

```bash
flowtoy webui step4.yaml
```

Open http://localhost:8000 in your browser to see real-time progress!

## Next Steps

You've learned the basics of flowtoy! Now explore:

- **[How-To Guides](../how-to/fetch-rest-api-data.md)**: Solve specific problems
- **[Reference](../reference/configuration.md)**: Complete technical documentation
- **[Explanation](../explanation/overview.md)**: Understand how flowtoy works
