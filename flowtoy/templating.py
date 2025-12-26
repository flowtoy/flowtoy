from __future__ import annotations

from typing import Any, Dict

import jmespath
from jinja2 import Environment, StrictUndefined

_jinja = Environment(undefined=StrictUndefined)


def render_template(template: str, context: Dict[str, Any]) -> str:
    tpl = _jinja.from_string(template)
    return tpl.render(**(context or {}))


def render_dict_templates(obj: Any, context: Dict[str, Any]) -> Any:
    """Recursively render Jinja2 templates in dict/list structures.

    Args:
        obj: The object to render (dict, list, str, or other)
        context: Template context (e.g., {"flows": ..., "sources": ...})

    Returns:
        New object with all string templates rendered
    """
    if isinstance(obj, dict):
        return {k: render_dict_templates(v, context) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [render_dict_templates(item, context) for item in obj]
    elif isinstance(obj, str):
        # Only render if it looks like it contains template syntax
        if "{{" in obj or "{%" in obj:
            return render_template(obj, context)
        return obj
    else:
        return obj


def extract_jmespath(expr: str, data: Any):
    try:
        return jmespath.search(expr, data)
    except Exception:
        return None
