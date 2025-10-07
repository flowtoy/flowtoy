from __future__ import annotations

import copy
import yaml
from typing import Any, Dict, List


def load_yaml_files(paths: List[str]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    for p in paths:
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        merged = deep_merge(merged, data)
    return merged


def deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Deep-merge dict b into a and return the result (new dict)."""
    out = copy.deepcopy(a)
    for k, v in (b or {}).items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def get_flow_steps(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    return cfg.get("flow", []) or []


def get_sources(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return cfg.get("sources", {}) or {}
