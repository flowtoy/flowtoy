from __future__ import annotations

from typing import Any, Dict, List, Optional
import threading
import time

from .config import get_flow_steps, get_sources
from .templating import render_template, extract_jmespath
from .connectors import create_connector


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

    def run(self):
        self.status.started_at = time.time()
        for step in self.steps:
            name = step.get("name")
            if not isinstance(name, str):
                # skip malformed steps
                continue
            st = StepStatus(name)
            st.started_at = time.time()
            st.state = "running"
            self.status.steps[name] = st

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
                    st.state = "failed"
                    st.error = "invalid source type"
                    st.ended_at = time.time()
                    break
                cfg = source_def.get("configuration") or {}
                if not isinstance(cfg, dict):
                    cfg = {}
                connector = create_connector(src_type, cfg)

                # build input payload
                input_def = step.get("input") or {}
                payload = None
                itype = input_def.get("type")
                if itype == "parameter":
                    val = input_def.get("value")
                    payload = render_template(
                        str(val), {"flows": self.flows, "sources": self.sources}
                    )
                elif itype == "filter":
                    template = input_def.get("template")
                    payload = render_template(
                        str(template or ""),
                        {"flows": self.flows, "sources": self.sources},
                    )
                elif itype == "body":
                    template = input_def.get("template")
                    payload = render_template(
                        str(template or ""),
                        {"flows": self.flows, "sources": self.sources},
                    )

                result = connector.call(payload)

                # unify result structure: expect dict with 'status' and 'data'
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
                    st.state = "failed"
                    st.error = error_msg or (
                        f"connector reported failure (code={code})"
                    )
                    st.ended_at = time.time()
                    break

                # extract outputs
                outputs = step.get("output") or []
                self.flows[name] = {}
                for out in outputs:
                    oname = out.get("name")
                    if not isinstance(oname, str):
                        # skip unnamed outputs
                        continue
                    otype = out.get("type")
                    if otype == "jmespath":
                        expr = out.get("value")
                        val = extract_jmespath(str(expr or ""), data)
                    elif otype == "json":
                        val = data
                    else:
                        val = data
                    self.flows[name][oname] = val

                st.state = "succeeded"
                st.ended_at = time.time()
            except Exception as e:
                st.state = "failed"
                st.error = str(e)
                st.ended_at = time.time()
                # fail-fast for now
                break

        self.status.ended_at = time.time()
