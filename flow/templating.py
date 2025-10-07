from __future__ import annotations

from jinja2 import Environment, StrictUndefined
import jmespath
from typing import Any, Dict


_jinja = Environment(undefined=StrictUndefined)


def render_template(template: str, context: Dict[str, Any]) -> str:
    tpl = _jinja.from_string(template)
    return tpl.render(**context)


def extract_jmespath(expr: str, data: Any):
    try:
        return jmespath.search(expr, data)
    except Exception:
        return None
