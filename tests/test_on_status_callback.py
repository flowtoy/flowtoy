import sys
import threading

from flowtoy.runner import LocalRunner


def _echo_step(name):
    """A process step that prints a fixed string (fast step)."""
    return {
        "name": name,
        "source": {
            "type": "process",
            "configuration": {"command": [sys.executable, "-c", "print('ok')"]},
        },
        "input": "",
    }


def _runner(steps, on_status=None):
    return LocalRunner({"sources": {}, "flow": steps}, on_status=on_status)


def test_on_status_observes_state_transitions():
    """Callback sees running then a terminal state for each step."""
    events = []
    r = _runner(
        [_echo_step("a"), _echo_step("b")],
        on_status=lambda n, s: events.append((n, s)),
    )
    r.run()

    by_step = {}
    for name, state in events:
        by_step.setdefault(name, []).append(state)

    assert set(by_step) == {"a", "b"}
    for states in by_step.values():
        assert states == ["running", "succeeded"]


def test_on_status_sees_committed_state():
    """When the callback fires, the runner's status already reflects it."""
    mismatches = []

    def on_status(name, state):
        if r.status.steps[name].state != state:
            mismatches.append((name, state))

    r = _runner([_echo_step("a")], on_status=on_status)
    r.run()

    assert mismatches == []


def test_on_status_invoked_outside_lock():
    """Another thread can take the runner lock while the callback runs.

    The lock is an RLock, so re-acquiring it from the callback's own thread
    would succeed even if the callback were invoked under the lock. Acquire
    it from a separate thread instead, which blocks if the lock is held.
    """
    blocked = []

    def on_status(name, state):
        def grab():
            with r._lock:
                pass

        t = threading.Thread(target=grab)
        t.start()
        t.join(timeout=2)
        if t.is_alive():
            blocked.append(state)

    r = _runner([_echo_step("a")], on_status=on_status)
    r.run()

    assert blocked == []


def test_on_status_callback_exception_does_not_break_run():
    """A raising callback must not abort the flow."""

    def on_status(name, state):
        raise RuntimeError("boom")

    r = _runner([_echo_step("a")], on_status=on_status)
    r.run()

    assert r.status.steps["a"].state == "succeeded"


def test_on_status_default_none():
    """No on_status means no callback is configured (backward compatible)."""
    r = _runner([_echo_step("a")])
    assert r._on_status is None
    r.run()
    assert r.status.steps["a"].state == "succeeded"
