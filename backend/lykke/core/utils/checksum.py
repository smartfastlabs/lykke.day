"""Utilities for deterministic JSON checksums used in sync integrity."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any


def _canonicalize_json_value(value: Any) -> str:
    """Canonicalize JSON value using RFC 8785-style key ordering."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("Non-finite numbers are not valid JSON.")
        return json.dumps(value, ensure_ascii=False, allow_nan=False)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ",".join(_canonicalize_json_value(item) for item in value) + "]"
    if isinstance(value, dict):
        keys = sorted(value.keys())
        serialized_items = []
        for key in keys:
            if not isinstance(key, str):
                raise TypeError("JSON object keys must be strings.")
            serialized_items.append(
                f"{json.dumps(key, ensure_ascii=False)}:{_canonicalize_json_value(value[key])}"
            )
        return "{" + ",".join(serialized_items) + "}"

    raise TypeError(f"Unsupported JSON value type: {type(value).__name__}")


def canonicalize_json(value: Any) -> str:
    """Return canonical JSON string suitable for cross-platform hashing."""
    return _canonicalize_json_value(value)


def sha256_hex(payload: str) -> str:
    """Return SHA-256 hex digest for UTF-8 payload."""
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def jcs_sha256(value: Any) -> str:
    """Compute JCS canonical JSON + SHA-256 checksum."""
    return sha256_hex(canonicalize_json(value))
