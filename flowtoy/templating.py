from __future__ import annotations

from typing import Any, Dict

import jmespath
from jinja2 import Environment, StrictUndefined

_jinja = Environment(undefined=StrictUndefined)


def render_template(template: str, context: Dict[str, Any]) -> str:
    tpl = _jinja.from_string(template)
    return tpl.render(**(context or {}))


def extract_jmespath(expr: str, data: Any):
    try:
        return jmespath.search(expr, data)
    except Exception:
        return None
