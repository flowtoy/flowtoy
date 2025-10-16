from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from .result import make_result, result_from_exception


class RestConnector:
    type_name = "rest"

    def __init__(self, configuration: Dict[str, Any]):
        self.configuration = configuration or {}

    def call(self, input_payload: Optional[Any] = None) -> Any:
        cfg = self.configuration
        method = cfg.get("method", "GET").upper()
        url = cfg["url"]
        params = None
        json_body = None
        headers = cfg.get("headers") or {}
        if cfg.get("input_mode") == "parameter" and input_payload is not None:
            params = {cfg.get("param_name", "id"): input_payload}
        elif cfg.get("input_mode") == "body" and input_payload is not None:
            json_body = input_payload

        try:
            resp = requests.request(
                method, url, params=params, json=json_body, headers=headers
            )
        except Exception as e:
            return result_from_exception(e)

        status_code = resp.status_code
        meta = {"status_code": status_code, "headers": dict(resp.headers)}
        try:
            data = resp.json()
        except Exception:
            data = resp.text

        notes = []
        if not (200 <= status_code < 300):
            notes.append(f"HTTP status {status_code}")

        return make_result(
            success=(200 <= status_code < 300),
            code=status_code,
            data=data,
            notes=notes,
            meta=meta,
        )
