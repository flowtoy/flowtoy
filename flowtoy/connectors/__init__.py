"""Connector registry with lazy imports and entry point discovery.

Connectors are intentionally imported only when they are first requested so
that heavy optional dependencies (like ldap3) don't get imported at package
import time.

This module exposes:
- create_connector(type_name, configuration)
- discover_entry_points() - finds connectors registered via entry points
- register_connector(name, constructor_or_path) - for runtime registration
"""

from __future__ import annotations

import importlib
from importlib.metadata import entry_points
from typing import Any, Callable, Dict

# Registry for connectors registered at runtime
_connector_registry: Dict[str, Callable[[dict], Any]] = {}
# Track if entry points have been discovered
_entry_points_discovered = False


def _derive_class_name(name: str) -> str:
    # simple heuristic: last segment, capitalize first letter, append 'Connector'
    base = name.split(".")[-1]
    if not base:
        raise ValueError("invalid connector type name")
    return base.capitalize() + "Connector"


def discover_entry_points() -> Dict[str, Callable[[dict], Any]]:
    """Discover connectors registered via entry points.

    Returns a dict mapping connector names to their constructor functions.
    Entry points should be registered in the 'flowtoy.connectors' group.
    """
    discovered = {}
    try:
        # Python 3.10+ API
        eps = entry_points(group="flowtoy.connectors")
    except TypeError:
        # Python 3.9 fallback - entry_points() returns SelectableGroups
        all_eps = entry_points()
        # SelectableGroups allows dictionary-style access
        eps = all_eps["flowtoy.connectors"] if "flowtoy.connectors" in all_eps else []

    for ep in eps:
        try:
            connector_class = ep.load()  # type: ignore
            discovered[ep.name] = connector_class  # type: ignore
        except Exception as e:
            # Log but don't fail if a plugin can't load
            import sys

            print(
                f"Warning: Failed to load connector plugin '{ep.name}': {e}",
                file=sys.stderr,
            )

    return discovered


def register_connector(name: str, constructor: Callable[[dict], Any]) -> None:
    """Register a connector at runtime.

    Args:
        name: The connector type name (e.g., "ldap", "custom")
        constructor: A callable that takes a configuration dict and returns a
                     connector instance
    """
    _connector_registry[name] = constructor


def create_connector(type_name: str, configuration: dict):
    """Create an instance of the named connector.

    Loading is dynamic. The function tries, in order:
    1. Check runtime-registered connectors (via register_connector)
    2. Check entry point plugins (via discover_entry_points)
    3. module:Class (explicit module and class separated by ':')
    4. module.Class (fully-qualified class path)
    5. module (module that exports a Connector class)
    6. fallback to flowtoy.connectors.<type_name>

    This means you don't need to pre-register connectors; they are only
    imported when the runtime configuration names them.
    """
    global _entry_points_discovered

    # 1) Check runtime-registered connectors
    if type_name in _connector_registry:
        return _connector_registry[type_name](configuration)

    # 2) Check entry point plugins (discover on first use)
    if not _entry_points_discovered:
        discovered = discover_entry_points()
        _connector_registry.update(discovered)
        _entry_points_discovered = True

    if type_name in _connector_registry:
        return _connector_registry[type_name](configuration)

    # Support several forms for type_name, in decreasing order of specificity:
    # 3. module:Class (explicit module and class separated by ':')
    # 4. module.Class (fully-qualified class path)
    # 5. module (module that exports a Connector class)
    # 6. fallback to flowtoy.connectors.<type_name>

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
    if "." in type_name and not type_name.startswith("flowtoy.connectors."):
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
        f"flowtoy.connectors.{type_name}",
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


__all__ = ["create_connector", "register_connector", "discover_entry_points"]
