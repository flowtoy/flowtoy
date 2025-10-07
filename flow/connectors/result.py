from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional


def _make_notes(notes: Optional[Iterable[str]]) -> List[str]:
    if notes is None:
        return []
    out: List[str] = []
    for n in notes:
        if n is None:
            continue
        if isinstance(n, (list, tuple)):
            out.extend([str(x) for x in n if x is not None])
        else:
            out.append(str(n))
    return out


DEFAULT_REDACT = ("password", "secret", "token", "bind_password", "pw")


def sanitize_meta(
    meta: Optional[Dict[str, Any]], redact_keys: Optional[Iterable[str]] = None
) -> Dict[str, Any]:
    if meta is None:
        return {}
    redact = list(redact_keys or DEFAULT_REDACT)
    out: Dict[str, Any] = dict(meta)
    for k in list(out.keys()):
        lk = k.lower()
        if any(r in lk for r in redact):
            out[k] = "<redacted>"
    return out


def make_result(
    *,
    success: bool,
    code: Optional[int] = None,
    data: Any = None,
    notes: Optional[Iterable[str]] = None,
    meta: Optional[Dict[str, Any]] = None,
    redact_meta_keys: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """Build canonical connector result.

    Returns:
      {"status": {"success": bool, "code": int|None, "notes": [str,...]},
       "data": ..., "meta": {...}}
    """
    notes_list = _make_notes(notes)
    meta_s = sanitize_meta(meta, redact_meta_keys) if meta is not None else {}
    return {
        "status": {"success": bool(success), "code": code, "notes": notes_list},
        "data": data,
        "meta": meta_s,
    }


def result_from_exception(exc: Exception, code: Optional[int] = None) -> Dict[str, Any]:
    return make_result(
        success=False,
        code=code,
        data=None,
        notes=[str(exc)],
        meta={"exception": repr(exc)},
    )
