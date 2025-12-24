#!/usr/bin/env python3
import json
import sys

# Read JSON from stdin
data = json.load(sys.stdin)

# Process the data
result = {
    "processed": True,
    "user_id": data.get("user_id"),
    "total_items": len(data.get("posts", [])) + len(data.get("todos", [])),
}

# Output JSON to stdout
print(json.dumps(result))
