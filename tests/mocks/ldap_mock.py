from typing import Any, Dict, Optional

from flowtoy.connectors.result import make_result


class LdapConnector:
    type_name = "ldap"

    def __init__(self, configuration: Dict[str, Any]):
        self.configuration = configuration or {}

    def call(self, input_payload: Optional[Any] = None) -> Any:
        # input_payload is the shortname
        shortname = (input_payload or "").strip()
        # return a fake LDAP entry
        data = {
            "uid": f"uid-{shortname}",
            "displayName": f"{shortname.capitalize()} Person",
            "email": f"{shortname}@example.edu",
        }
        return make_result(success=True, code=0, data=data, notes=[], meta={})
