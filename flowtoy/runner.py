from __future__ import annotations

import logging
import re
import threading
import time
from concurrent.futures import (
    FIRST_COMPLETED,
    Future,
    ThreadPoolExecutor,
)
from concurrent.futures import (
    wait as cf_wait,
)
from queue import Queue
from typing import Any, Dict, Optional

from .config import get_flow_steps, get_sources
from .providers import create_provider
from .templating import extract_jmespath, render_template


class StepStatus:
    name: str
    state: str
    started_at: Optional[float]
    ended_at: Optional[float]
    error: Optional[str]

    def __init__(self, name: str):
        self.name = name
        self.state = "pending"
        self.started_at = None
        self.ended_at = None
        self.error = None


class RunStatus:
    steps: Dict[str, StepStatus]
    started_at: Optional[float]
    ended_at: Optional[float]
    run_id: int

    def __init__(self):
        self.steps = {}
        self.started_at = None
        self.ended_at = None
        self.run_id = int(time.time() * 1000)


class LocalRunner:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sources = get_sources(config)
        self.steps = get_flow_steps(config)
        self.flows: Dict[str, Dict[str, Any]] = {}
        self.status = RunStatus()
        # lock to protect self.flows and status updates when running concurrently
        self._lock = threading.RLock()
        # configurable max workers
        self._max_workers = (
            (config.get("runner") or {}).get("max_workers")
            if isinstance((config.get("runner") or {}).get("max_workers"), int)
            else None
        )

    def _update_step_status(
        self, step_name: str, state: Optional[str] = None, **kwargs
    ) -> None:
        """Atomically update step status fields under lock.

        Args:
            step_name: Name of the step to update
            state: New state value (if provided)
            **kwargs: Additional fields to set on the StepStatus object
        """
        with self._lock:
            st = self.status.steps.get(step_name)
            if st:
                if state is not None:
                    st.state = state
                for k, v in kwargs.items():
                    setattr(st, k, v)

    def run(self):
        # Set run start timestamp atomically
        with self._lock:
            self.status.started_at = time.time()

        logging.getLogger(__name__).info("runner starting: %d steps", len(self.steps))
        try:
            step_names = [s.get("name") for s in self.steps]
        except Exception:
            step_names = None
        logging.getLogger(__name__).info("steps: %s", step_names)
        logging.getLogger(__name__).info(
            "runner starting: %d steps -> %s", len(self.steps), step_names
        )

        # Build name->step map and initial structures
        name_to_step: Dict[str, Dict[str, Any]] = {}
        for s in self.steps:
            n = s.get("name")
            if isinstance(n, str):
                name_to_step[n] = s

        # infer dependencies: explicit depends_on or references to
        # flows.<step> in input templates
        dep_re = re.compile(r"flows\.([A-Za-z0-9_]+)\.")
        deps: Dict[str, set] = {name: set() for name in name_to_step}
        dependents: Dict[str, set] = {name: set() for name in name_to_step}

        for name, step in name_to_step.items():
            # explicit depends_on
            explicit = step.get("depends_on") or []
            if isinstance(explicit, list):
                for d in explicit:
                    if isinstance(d, str):
                        deps[name].add(d)

            # scan input fields for flows.<step> references
            input_def = step.get("input") or {}
            for key in ("value", "template"):
                val = input_def.get(key)
                if isinstance(val, str):
                    for m in dep_re.finditer(val):
                        deps[name].add(m.group(1))

        # normalize and validate deps
        invalid_deps: Dict[str, set] = {}
        for name in list(deps.keys()):
            # Track dependencies that don't exist
            missing = deps[name] - set(name_to_step.keys())
            if missing:
                invalid_deps[name] = missing

            # Keep only valid dependencies
            deps[name] = {d for d in deps[name] if d in name_to_step}
            for d in deps[name]:
                dependents[d].add(name)

        # Validate: raise error if any step references non-existent dependencies
        if invalid_deps:
            error_lines = []
            for step_name, missing_deps in invalid_deps.items():
                missing_list = ", ".join(f"'{d}'" for d in sorted(missing_deps))
                error_lines.append(
                    f"  - Step '{step_name}' depends on missing step(s): {missing_list}"
                )
            raise ValueError(
                "Flow configuration has invalid dependencies:\n"
                + "\n".join(error_lines)
            )

        # compute in-degree
        in_degree: Dict[str, int] = {name: len(deps[name]) for name in name_to_step}

        # prepare status entries
        with self._lock:
            for name in name_to_step:
                self.status.steps[name] = StepStatus(name)

        # default on_error policy (per-flow default)
        runner_conf = self.config.get("runner") or {}
        default_on_error = (runner_conf.get("on_error") or "fail").lower()

        # executor
        max_workers = self._max_workers or min(4, (threading.active_count() or 1) + 3)
        executor = ThreadPoolExecutor(max_workers=max_workers)
        futures: Dict[Future, str] = {}
        ready_q = Queue()

        # enqueue initial ready steps
        for name, deg in in_degree.items():
            if deg == 0:
                ready_q.put(name)

        error_occurred = threading.Event()

        def submit_step(step_name: str):
            def task():
                logging.getLogger(__name__).info("starting step: %s", step_name)
                self._update_step_status(
                    step_name, state="running", started_at=time.time()
                )
                step = name_to_step[step_name]
                try:
                    # resolve source
                    src = step.get("source")
                    if isinstance(src, dict) and "base" in src:
                        base = self.sources.get(src["base"]) or {}
                        override = src.get("override") or {}
                        source_def = {**base, **override}
                    elif isinstance(src, str):
                        source_def = self.sources.get(src) or {"type": src}
                    else:
                        source_def = src or {}

                    src_type = source_def.get("type")
                    if not isinstance(src_type, str):
                        raise RuntimeError("invalid source type")
                    cfg = source_def.get("configuration") or {}
                    if not isinstance(cfg, dict):
                        cfg = {}
                    provider = create_provider(src_type, cfg)

                    # build input payload with current snapshot of flows and sources
                    input_def = step.get("input") or {}
                    payload = None
                    itype = input_def.get("type")
                    # render templates under lock to get consistent snapshot
                    with self._lock:
                        flows_snapshot = dict(self.flows)
                        sources_snapshot = dict(self.sources)

                    if itype == "parameter":
                        val = input_def.get("value")
                        payload = render_template(
                            str(val),
                            {"flows": flows_snapshot, "sources": sources_snapshot},
                        )
                    elif itype in ("filter", "body"):
                        template = input_def.get("template")
                        payload = render_template(
                            str(template or ""),
                            {"flows": flows_snapshot, "sources": sources_snapshot},
                        )

                    result = provider.call(payload)

                    # unify result
                    if isinstance(result, dict) and "status" in result:
                        status_obj = result.get("status") or {}
                        success = status_obj.get("success", True)
                        code = status_obj.get("code")
                        notes = status_obj.get("notes") or []
                        error_msg = "; ".join(notes) if notes else None
                        data = result.get("data")
                    else:
                        success = True
                        code = None
                        error_msg = None
                        data = result

                    if not success:
                        raise RuntimeError(
                            error_msg
                            or ("provider reported failure (code=" + str(code) + ")")
                        )

                    # extract outputs
                    outputs = step.get("output") or []
                    out_map: Dict[str, Any] = {}
                    for out in outputs:
                        oname = out.get("name")
                        if not isinstance(oname, str):
                            continue
                        otype = out.get("type")
                        if otype == "jmespath":
                            expr = out.get("value")
                            val = extract_jmespath(str(expr or ""), data)
                        elif otype == "json":
                            val = data
                        else:
                            val = data
                        out_map[oname] = val

                    with self._lock:
                        self.flows[step_name] = out_map
                    self._update_step_status(
                        step_name, state="succeeded", ended_at=time.time()
                    )
                    logging.getLogger(__name__).info("step succeeded: %s", step_name)
                    return True, None, None
                except Exception as e:
                    self._update_step_status(
                        step_name, state="failed", error=str(e), ended_at=time.time()
                    )
                    logging.getLogger(__name__).exception("step failed: %s", step_name)
                    # determine per-step policy
                    policy = (
                        step.get("on_error") or default_on_error or "fail"
                    ).lower()
                    return False, e, policy

            return executor.submit(task)

        # main scheduler loop
        try:
            # seed initial submissions
            while not ready_q.empty():
                n = ready_q.get()
                f = submit_step(n)
                futures[f] = n

            # process completions and submit dependents
            while futures:
                # wait for any future to complete (or timeout)
                done, _ = cf_wait(
                    list(futures.keys()), timeout=0.1, return_when=FIRST_COMPLETED
                )
                to_process = (
                    list(done)
                    if done
                    else [f for f in list(futures.keys()) if f.done()]
                )
                if not to_process:
                    # small sleep to avoid busy loop
                    time.sleep(0.05)
                    continue

                for f in to_process:
                    step_name = futures.pop(f)
                    try:
                        ok, exc, policy = f.result()
                    except Exception:
                        # If the task itself raised unexpectedly, treat as
                        # failure with default policy
                        ok = False

                    if not ok:
                        # handle each dependent according to the dependent's
                        # own on_error
                        def skip_descendants(n):
                            for dep in list(dependents.get(n, [])):
                                if in_degree.get(dep, 0) >= 0:
                                    in_degree[dep] = -1
                                    self._update_step_status(
                                        dep,
                                        state="skipped",
                                        started_at=None,
                                        ended_at=time.time(),
                                    )
                                    skip_descendants(dep)

                        for dep in dependents.get(step_name, set()):
                            dep_step = name_to_step.get(dep) or {}
                            dep_policy = (
                                dep_step.get("on_error") or default_on_error or "fail"
                            ).lower()
                            if dep_policy == "skip":
                                # mark this dependent itself skipped
                                self._update_step_status(
                                    dep,
                                    state="skipped",
                                    started_at=None,
                                    ended_at=time.time(),
                                )
                                # mark descendants skipped as well
                                skip_descendants(dep)
                                in_degree[dep] = -1
                            elif dep_policy == "continue":
                                # allow dependent to be scheduled; we'll decrement
                                # its in_degree below
                                pass
                            elif dep_policy == "fail":
                                # dependent requires fail-on-missing-dependency ->
                                # stop whole run
                                error_occurred.set()
                                with ready_q.mutex:
                                    ready_q.queue.clear()
                                futures.clear()
                                break
                            else:
                                # unknown policy: treat as fail-fast for safety
                                error_occurred.set()
                                with ready_q.mutex:
                                    ready_q.queue.clear()
                                futures.clear()
                                break

                    # on success or handled dependents above, decrement
                    # in_degree for dependents and enqueue if ready
                    for dep in dependents.get(step_name, set()):
                        # only decrement if not already marked skipped
                        if in_degree.get(dep, 0) > 0:
                            in_degree[dep] -= 1
                            if in_degree[dep] == 0:
                                ready_q.put(dep)

                # submit any newly ready (unless an error stopped us)
                while not ready_q.empty() and not error_occurred.is_set():
                    n = ready_q.get()
                    f2 = submit_step(n)
                    futures[f2] = n

                if error_occurred.is_set():
                    break

        finally:
            executor.shutdown(wait=False)

        # Set run end timestamp atomically
        with self._lock:
            self.status.ended_at = time.time()
