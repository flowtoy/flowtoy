from __future__ import annotations

from typing import Any, Dict, Optional
import subprocess
import shlex
import json
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

        # allow passing payload either via stdin or as extra arg
        pass_to = cfg.get("pass_to", "arg")  # "arg" or "stdin"
        if input_payload is not None:
            if pass_to == "stdin":
                input_bytes = str(input_payload).encode("utf-8")
            else:
                # append as final arg
                cmd_list.append(str(input_payload))
                input_bytes = None
        else:
            input_bytes = None

        timeout = cfg.get("timeout")
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
        return make_result(
            success=(proc.returncode == 0),
            code=proc.returncode,
            data=data,
            notes=notes,
            meta=meta,
        )
