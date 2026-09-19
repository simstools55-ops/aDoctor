from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Mapping


def _trim(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return [_trim(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _trim(item) for key, item in value.items()}
    return value


def normalize_request(payload: Mapping[str, Any]) -> Dict[str, Any]:
    # Deep-copy protects the raw request retained for audit.
    return _trim(deepcopy(dict(payload)))
