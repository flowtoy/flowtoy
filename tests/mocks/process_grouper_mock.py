from typing import Any, Dict, Optional
from flow.connectors.result import make_result


class ProcessConnector:
    type_name = "process"

    def __init__(self, configuration: Dict[str, Any]):
        self.configuration = configuration or {}

    def call(self, input_payload: Optional[Any] = None) -> Any:
        uid = input_payload
        data = {"groups": [f"group-for-{uid}"]}
        return make_result(success=True, code=0, data=data, notes=[], meta={})
