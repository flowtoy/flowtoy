from __future__ import annotations

from typing import Any, Dict, Optional
import os
from .result import make_result


class EnvConnector:
    type_name = "env"

    def __init__(self, configuration: Dict[str, Any]):
        self.configuration = configuration or {}

    def call(self, input_payload: Optional[Any] = None) -> Any:
        vars = self.configuration.get("vars", [])
        data = {k: os.environ.get(k) for k in vars}
        return make_result(success=True, code=0, data=data, notes=[], meta={})
