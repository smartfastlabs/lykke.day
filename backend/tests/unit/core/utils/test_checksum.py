"""Tests for deterministic checksum utilities."""

from __future__ import annotations

import math

import pytest

from lykke.core.utils.checksum import canonicalize_json, jcs_sha256


def test_canonicalize_json_sorts_keys_and_preserves_unicode() -> None:
    payload = {
        "z": "last",
        "a": "first",
        "nested": {"b": 2, "a": "alpha", "emoji": "I ❤ Lykke"},
        "list": [3, {"y": "two", "x": "one"}, True],
        "accents": "café",
    }

    canonical = canonicalize_json(payload)

    assert (
        canonical
        == '{"a":"first","accents":"café","list":[3,{"x":"one","y":"two"},true],'
        '"nested":{"a":"alpha","b":2,"emoji":"I ❤ Lykke"},"z":"last"}'
    )


def test_jcs_sha256_matches_expected_cross_platform_vector() -> None:
    payload = {
        "z": "last",
        "a": "first",
        "nested": {"b": 2, "a": "alpha", "emoji": "I ❤ Lykke"},
        "list": [3, {"y": "two", "x": "one"}, True],
        "accents": "café",
    }

    assert (
        jcs_sha256(payload)
        == "59668ca164948c95d7eb33c8b652979171b134dd2106fa0de0a9b1a351cfa540"
    )


def test_canonicalize_json_rejects_non_finite_numbers() -> None:
    with pytest.raises(ValueError):
        canonicalize_json({"x": math.nan})
