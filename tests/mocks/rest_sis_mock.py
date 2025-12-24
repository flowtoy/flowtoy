from typing import Any, Dict, Optional

from flowtoy.providers.result import make_result


class RestProvider:
    type_name = "rest"

    def __init__(self, configuration: Dict[str, Any]):
        self.configuration = configuration or {}

    def call(self, input_payload: Optional[Any] = None) -> Any:
        uid = input_payload
        # behavior depends on configured 'endpoint' passed via configuration
        endpoint = self.configuration.get("endpoint")
        if endpoint == "programs":
            data = {"programs": [f"program-for-{uid}"]}
        elif endpoint == "courses":
            data = {"courses": [f"course-for-{uid}"]}
        else:
            data = {}
        return make_result(success=True, code=200, data=data, notes=[], meta={})
