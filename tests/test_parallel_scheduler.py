import os
import sys
import tempfile
import time

from flowtoy.cli import run_flow


def test_parallel_steps_run():
    # create a small flow where two steps depend on a single parent and sleep
    py = sys.executable
    cmd_parent = "import time, json; time.sleep(1); print(json.dumps({'ok': True}))"

    cmd_child = (
        "import time, json, sys; time.sleep(2); "
        "uid=sys.argv[1] if len(sys.argv)>1 else 'x'; "
        "print(json.dumps({'val': 'child-for-' + uid}))"
    )

    tpl = f"""
sources:
  parent_src:
    type: process
    configuration:
      command: ["{py}", "-c", "{cmd_parent}"]
  child_src:
    type: process
    configuration:
      command: ["{py}", "-c", "{cmd_child}"]

flow:
  - name: parent
    source: parent_src
    output:
      - name: data
        type: json

  - name: child_a
    source: child_src
    depends_on: [parent]
    input:
      type: parameter
      value: "{{ flows.parent.data.val if flows.parent.data else 'uid' }}"
    output:
      - name: val
        type: json

  - name: child_b
    source: child_src
    depends_on: [parent]
    input:
      type: parameter
      value: "{{ flows.parent.data.val if flows.parent.data else 'uid' }}"
    output:
      - name: val
        type: json
"""

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as fh:
        path = fh.name
        fh.write(tpl)

    start = time.time()
    os.environ["SHORTNAME"] = "alice"
    flows, status = run_flow([path])
    elapsed = time.time() - start

    # Each child sleeps 2s, parent sleeps 1s; if children run in parallel total ~3s
    assert elapsed < 5.0, f"expected parallel execution, but took {elapsed}s"
    assert "child_a" in flows and "child_b" in flows
