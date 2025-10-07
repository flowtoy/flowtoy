from __future__ import annotations

from typing import Any, Dict, Optional
import json
from .result import make_result, result_from_exception


class LdapConnector:
    type_name = "ldap"

    def __init__(self, configuration: Dict[str, Any]):
        self.configuration = configuration or {}

    def call(self, input_payload: Optional[Any] = None) -> Any:
        try:
            import ldap3
        except Exception as e:
            return result_from_exception(e)

        try:
            cfg = self.configuration
            uri = cfg.get("uri")
            if not uri:
                return make_result(
                    success=False,
                    code=400,
                    data=None,
                    notes=["missing ldap uri"],
                    meta={},
                )
            server = ldap3.Server(uri)
            conn = None
            bind_dn = cfg.get("bind_dn")
            bind_pw = cfg.get("bind_password")
            if bind_dn and bind_pw:
                conn = ldap3.Connection(
                    server, user=bind_dn, password=bind_pw, auto_bind=True
                )
            else:
                conn = ldap3.Connection(server, auto_bind=True)

            search_base = cfg.get("base_dn")
            if not search_base:
                return make_result(
                    success=False,
                    code=400,
                    data=None,
                    notes=["missing base_dn"],
                    meta={},
                )
            search_filter = input_payload or cfg.get("filter", "(objectClass=*)")
            attributes = cfg.get("attributes")
            conn.search(str(search_base), search_filter, attributes=attributes)
            entries = []
            for entry in conn.entries:
                try:
                    entries.append(json.loads(entry.entry_to_json()))
                except Exception:
                    entries.append(str(entry))
            return make_result(success=True, code=0, data=entries, notes=[], meta={})
        except Exception as e:
            return result_from_exception(e)
