"""Connector registry with lazy imports.

Connectors are intentionally imported only when they are first requested so
that heavy optional dependencies (like ldap3) don't get imported at package
import time.

This module exposes:
- create_connector(type_name, configuration)
- register_connector(name, constructor_or_path)
"""

from __future__ import annotations

import importlib


def _derive_class_name(name: str) -> str:
    # simple heuristic: last segment, capitalize first letter, append 'Connector'
    base = name.split(".")[-1]
    if not base:
        raise ValueError("invalid connector type name")
    return base.capitalize() + "Connector"


def create_connector(type_name: str, configuration: dict):
    """Create an instance of the named connector.

    Loading is dynamic. The function tries, in order:
    1. import module named `type_name` and find a `<Base>Connector` class
    2. import module `evans.connectors.<type_name>` and find `<Base>Connector`

    This means you don't need to pre-register connectors; they are only
    imported when the runtime configuration names them.
    """
    # Support several forms for type_name, in decreasing order of specificity:
    # 1. module:Class (explicit module and class separated by ':')
    # 2. module.Class (fully-qualified class path)
    # 3. module (module that exports a Connector class)
    # 4. fallback to evans.connectors.<type_name>

    last_exc = None

    # 1) module:Class
    if ":" in type_name:
        module_part, class_part = type_name.split(":", 1)
        try:
            mod = importlib.import_module(module_part)
        except Exception as e:
            raise ImportError(
                "could not import module '" + module_part + "': " + str(e)
            ) from e
        ctor = getattr(mod, class_part, None)
        if ctor is None:
            raise ImportError(
                "module '" + module_part + "' has no attribute '" + class_part + "'"
            ) from None
        return ctor(configuration)

    # 2) module.Class (fully-qualified class path)
    if "." in type_name and not type_name.startswith("evans.connectors."):
        parts = type_name.rsplit(".", 1)
        module_part, class_part = parts[0], parts[1]
        try:
            mod = importlib.import_module(module_part)
            ctor = getattr(mod, class_part, None)
            if ctor is not None:
                return ctor(configuration)
        except Exception as e:
            last_exc = e

    # 3) try importing as a module and find Connector in it
    candidates = [
        type_name,
        f"evans.connectors.{type_name}",
    ]
    for mod_name in candidates:
        try:
            mod = importlib.import_module(mod_name)
        except Exception as e:
            last_exc = e
            continue

        # attempt to find a class named <Base>Connector
        cls_name = _derive_class_name(mod_name)
        ctor = getattr(mod, cls_name, None)
        if ctor is None:
            # fallback: try to find any attribute that endswith 'Connector'
            for attr_name in dir(mod):
                if attr_name.lower().endswith("connector"):
                    ctor = getattr(mod, attr_name)
                    break

        if ctor is None:
            raise ImportError(
                "module '" + mod_name + "' does not expose a Connector class"
            )

        return ctor(configuration)

    # if we get here, no candidate worked
    if last_exc is not None:
        raise ImportError(
            f"could not import connector for type '{type_name}': {last_exc}"
        ) from last_exc
    raise ImportError(f"could not import connector for type '{type_name}'")


__all__ = ["create_connector"]
