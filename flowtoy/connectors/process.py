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

    def _sanitize_for_logging(self, cmd_list: list, cfg: Dict[str, Any]) -> list:
        """Sanitize command arguments for logging based on configuration.

        Configuration options:
          - log_full_command: bool (default False) - if True, log everything
          - redact_args: list[int] - indices of arguments to redact
          - redact_patterns: list[str] - redact args containing these substrings

        Examples:
          configuration:
            command: ["curl", "-H", "Authorization: Bearer TOKEN"]
            redact_args: [2]  # Redact 3rd arg (index 2)

          configuration:
            command: ["curl", "-H", "Authorization: Bearer TOKEN"]
            redact_patterns: ["Authorization:", "Bearer"]
        """
        # If explicitly configured to log everything, return as-is
        if cfg.get("log_full_command"):
            return cmd_list

        # Default: only log command name and arg count
        redact_indices = cfg.get("redact_args")
        redact_patterns = cfg.get("redact_patterns")

        # If no redaction config specified, use safe default
        if redact_indices is None and redact_patterns is None:
            if len(cmd_list) <= 1:
                return cmd_list
            return [cmd_list[0], f"<{len(cmd_list)-1} args>"]

        # User has configured specific redaction
        sanitized = []
        for i, arg in enumerate(cmd_list):
            arg_str = str(arg)

            # Check if this index should be redacted
            if redact_indices and i in redact_indices:
                sanitized.append("[REDACTED]")
                continue

            # Check if this arg matches any redaction patterns
            if redact_patterns:
                should_redact = any(pattern in arg_str for pattern in redact_patterns)
                if should_redact:
                    sanitized.append("[REDACTED]")
                    continue

            # No redaction needed for this arg
            sanitized.append(arg)

        return sanitized

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

        # Prepare sanitized command for logging
        log_cmd = self._sanitize_for_logging(cmd_list, cfg)
        logging.getLogger(__name__).info(
            "ProcessConnector running command: %s", log_cmd
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
            log_cmd,  # Use sanitized version
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
