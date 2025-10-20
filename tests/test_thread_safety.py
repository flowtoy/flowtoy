"""Test thread safety of runner status updates during concurrent execution."""

import threading
import time

from evans.runner import LocalRunner


def test_concurrent_status_reads_during_execution():
    """
    Test that reading status concurrently while steps execute doesn't cause
    errors.
    """
    # Create a flow with multiple parallel steps that take some time
    cfg = {
        "sources": {
            "slow_env": {
                "type": "process",
                "configuration": {
                    "command": [
                        "python",
                        "-c",
                        "import time,json;time.sleep(0.1);print(json.dumps({'v':'X'}))",
                    ],
                },
            }
        },
        "flow": [
            {
                "name": "step1",
                "source": "slow_env",
                "output": [{"name": "v", "type": "json"}],
            },
            {
                "name": "step2",
                "source": "slow_env",
                "output": [{"name": "v", "type": "json"}],
            },
            {
                "name": "step3",
                "source": "slow_env",
                "depends_on": ["step1"],
                "output": [{"name": "v", "type": "json"}],
            },
            {
                "name": "step4",
                "source": "slow_env",
                "depends_on": ["step2"],
                "output": [{"name": "v", "type": "json"}],
            },
        ],
    }

    runner = LocalRunner(cfg)

    # Track any exceptions from reader threads
    exceptions = []
    stop_reading = threading.Event()

    def read_status_repeatedly():
        """Continuously read runner status and flows while execution happens."""
        try:
            while not stop_reading.is_set():
                # Read status
                _ = runner.status.started_at
                _ = runner.status.ended_at
                _ = runner.status.run_id

                # Read step statuses
                for _step_name, step_status in list(runner.status.steps.items()):
                    _ = step_status.state
                    _ = step_status.started_at
                    _ = step_status.ended_at
                    _ = step_status.error

                # Read flows
                _ = dict(runner.flows)

                time.sleep(0.001)  # Small delay to allow other threads to run
        except Exception as e:
            exceptions.append(e)

    # Start multiple reader threads
    reader_threads = []
    for _ in range(5):
        t = threading.Thread(target=read_status_repeatedly, daemon=True)
        t.start()
        reader_threads.append(t)

    # Run the flow (this will update status concurrently with readers)
    runner.run()

    # Stop readers
    stop_reading.set()
    for t in reader_threads:
        t.join(timeout=1.0)

    # Check that no exceptions occurred during concurrent reads
    assert len(exceptions) == 0, f"Concurrent reads caused exceptions: {exceptions}"

    # Verify run completed successfully
    assert runner.status.started_at is not None
    assert runner.status.ended_at is not None
    assert all(s.state in ("succeeded", "failed") for s in runner.status.steps.values())


def test_step_status_updates_are_atomic():
    """Test that the _update_step_status helper provides atomic updates."""
    cfg = {
        "sources": {},
        "flow": [
            {"name": "test_step", "output": []},
        ],
    }

    runner = LocalRunner(cfg)

    # Initialize step status
    from evans.runner import StepStatus

    with runner._lock:
        runner.status.steps["test_step"] = StepStatus("test_step")

    # Track updates from concurrent threads
    update_count = 0
    updates_lock = threading.Lock()

    def update_status():
        nonlocal update_count
        for i in range(100):
            runner._update_step_status(
                "test_step",
                state=f"state_{threading.current_thread().name}_{i}",
                started_at=time.time(),
            )
            with updates_lock:
                update_count += 1

    # Run multiple threads updating the same step status
    threads = []
    for i in range(10):
        t = threading.Thread(target=update_status, name=f"updater_{i}")
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    # Verify all updates completed without errors
    assert update_count == 1000  # 10 threads * 100 updates each

    # Verify status is consistent (not corrupted)
    st = runner.status.steps["test_step"]
    assert st.state.startswith("state_")
    assert st.started_at is not None


def test_run_timestamps_set_atomically():
    """Test that run start and end timestamps are set under lock."""
    cfg = {
        "sources": {
            "fast_env": {
                "type": "env",
                "configuration": {"vars": []},
            }
        },
        "flow": [
            {"name": "step1", "source": "fast_env", "output": []},
        ],
    }

    runner = LocalRunner(cfg)

    # Verify started_at is None before run
    assert runner.status.started_at is None

    runner.run()

    # Verify timestamps are set after run
    assert runner.status.started_at is not None
    assert runner.status.ended_at is not None
    assert runner.status.ended_at >= runner.status.started_at
