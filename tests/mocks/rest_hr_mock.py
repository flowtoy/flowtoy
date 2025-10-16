from typing import Any, Dict, Optional

from evans.connectors.result import make_result


class RestConnector:
    type_name = "rest"

    def __init__(self, configuration: Dict[str, Any]):
        self.configuration = configuration or {}

    def call(self, input_payload: Optional[Any] = None) -> Any:
        # input_payload is uid
        uid = input_payload
        data = {"jobs": [f"job-for-{uid}"]}
        return make_result(success=True, code=200, data=data, notes=[], meta={})
