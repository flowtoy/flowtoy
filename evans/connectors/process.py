from __future__ import annotations

import json
import logging
import shlex
import subprocess
import time as _time
from typing import Any, Dict, Optional

import jinja2
import jmespath

from .result import make_result, result_from_exception


class ProcessConnector:
    type_name = "process"

    def __init__(self, configuration: Dict[str, Any]):
        self.configuration = configuration or {}

    def call(self, input_payload: Optional[Any] = None) -> Any:
        cfg = self.configuration or {}
        cmd = cfg.get("command")
        if cmd is None:
            raise KeyError("process connector requires 'command' in configuration")

        # normalize command into a list
        if isinstance(cmd, str):
            cmd_list = shlex.split(cmd)
        else:
            cmd_list = list(cmd)

        # allow passing payload either via stdin, as extra arg, or via templates
        pass_to = cfg.get("pass_to", "arg")  # "arg", "stdin", or "template"

        input_bytes = None
        parsed_json = None

        # handle stdin and arg modes when input is provided
        if pass_to == "stdin":
            if input_payload is not None:
                input_bytes = str(input_payload).encode("utf-8")
        elif pass_to == "arg":
            if input_payload is not None:
                # append as final arg
                cmd_list.append(str(input_payload))
        elif pass_to == "template":
            # prepare jinja2 environment with StrictUndefined (missing
            # variables should raise)
            template_strict = cfg.get("template_strict", True)
            undefined = jinja2.StrictUndefined if template_strict else jinja2.Undefined
            env = jinja2.Environment(undefined=undefined)

            # try to parse input as json for jmespath queries (only if provided
            # and looks like text)
            try:
                parsed_json = (
                    json.loads(input_payload)
                    if input_payload is not None
                    and isinstance(input_payload, (str, bytes, bytearray))
                    else None
                )
            except Exception:
                parsed_json = None

            # helper exposing jmespath search against parsed_json
            def _jmespath(expr):
                if parsed_json is None:
                    return None
                return jmespath.search(expr, parsed_json)

            env.globals["jmespath"] = _jmespath

            # context available to templates
            ctx = {
                "raw": str(input_payload),
                "input": input_payload,
                "json": parsed_json,
            }

            # render each arg as a template (render even if input_payload is
            # None so missing vars raise)
            rendered = []
            for a in cmd_list:
                try:
                    tmpl = env.from_string(a)
                    rendered_arg = tmpl.render(ctx)
                except jinja2.exceptions.UndefinedError:
                    # re-raise to respect strict undefined behaviour
                    raise
                rendered.append(rendered_arg)
            cmd_list = rendered
        else:
            # unknown pass_to - fall back to arg behaviour
            if input_payload is not None:
                cmd_list.append(str(input_payload))

        timeout = cfg.get("timeout")
        start_ts = _time.time()
        logging.getLogger(__name__).info(
            "ProcessConnector running command: %s", cmd_list
        )
        try:
            proc = subprocess.run(
                cmd_list,
                input=input_bytes,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as e:
            # Return structured error result for timeouts (runtime failure)
            return make_result(
                success=False,
                code=None,
                data=None,
                notes=["timeout"],
                meta={"timeout": True, "exception": str(e)},
            )
        except Exception as e:
            # Non-programmer runtime errors (e.g. OSError) returned as structured result
            return result_from_exception(e)

        stdout = (
            proc.stdout.decode("utf-8", errors="ignore")
            if isinstance(proc.stdout, (bytes, bytearray))
            else proc.stdout
        )
        stderr = (
            proc.stderr.decode("utf-8", errors="ignore")
            if isinstance(proc.stderr, (bytes, bytearray))
            else proc.stderr
        )

        # try to parse stdout as json
        meta = {"stderr": stderr, "returncode": proc.returncode}
        try:
            data = json.loads(stdout)
        except Exception:
            data = stdout

        notes = (
            []
            if proc.returncode == 0
            else [f"process exited with code {proc.returncode}"]
        )
        elapsed = _time.time() - start_ts
        logging.getLogger(__name__).info(
            "ProcessConnector finished command: %s returncode=%s elapsed=%.3fs",
            cmd_list,
            proc.returncode,
            elapsed,
        )
        return make_result(
            success=(proc.returncode == 0),
            code=proc.returncode,
            data=data,
            notes=notes,
            meta=meta,
        )
