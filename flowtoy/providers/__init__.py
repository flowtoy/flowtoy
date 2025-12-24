"""Dynamic provider loading with lazy imports and entry point discovery.

Providers are intentionally imported only when they are first requested so
that heavy optional dependencies don't get imported at package import time.

This module exposes:
- create_provider(type_name, configuration)
  dynamically loads and instantiates providers

- discover_entry_points()
  finds providers registered via entry points
"""

from __future__ import annotations

from importlib.metadata import entry_points
from typing import Any, Callable, Dict

# Track if entry points have been discovered
_entry_points_discovered = False
# Cache for discovered entry points
_entry_point_providers: Dict[str, Callable[[dict], Any]] = {}


def discover_entry_points() -> Dict[str, Callable[[dict], Any]]:
    """Discover providers registered via entry points.

    Returns a dict mapping provider names to their constructor functions.
    Entry points should be registered in the 'flowtoy.providers' group.
    """
    discovered = {}
    try:
        # Python 3.10+ API
        eps = entry_points(group="flowtoy.providers")
    except TypeError:
        # Python 3.9 fallback - entry_points() returns SelectableGroups
        all_eps = entry_points()
        # SelectableGroups allows dictionary-style access
        eps = all_eps["flowtoy.providers"] if "flowtoy.providers" in all_eps else []

    for ep in eps:
        try:
            provider_class = ep.load()  # type: ignore
            discovered[ep.name] = provider_class  # type: ignore
        except Exception as e:
            # Log but don't fail if a provider can't load
            import sys

            print(
                f"Warning: Failed to load provider '{ep.name}': {e}",
                file=sys.stderr,
            )

    return discovered


def create_provider(type_name: str, configuration: dict):
    """Create an instance of the named provider.

    Providers are loaded via entry points in the 'flowtoy.providers' group.
    This applies to both built-in and third-party providers.

    Providers are only imported when first requested (lazy loading).
    """
    global _entry_points_discovered

    # Discover all providers on first use
    if not _entry_points_discovered:
        discovered = discover_entry_points()
        _entry_point_providers.update(discovered)
        _entry_points_discovered = True

    if type_name not in _entry_point_providers:
        available = ", ".join(sorted(_entry_point_providers.keys()))
        raise ImportError(
            f"Unknown provider type '{type_name}'. Available providers: {available}"
        )

    return _entry_point_providers[type_name](configuration)


__all__ = ["create_provider", "discover_entry_points"]
