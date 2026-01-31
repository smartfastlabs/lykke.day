"""Unit tests for phone number normalization utilities."""

from lykke.core.utils.phone_numbers import digits_only, normalize_phone_number


def test_digits_only_strips_non_digits() -> None:
    assert digits_only("+1 (978) 844-4177") == "19788444177"


def test_normalize_phone_number_e164_for_us_numbers() -> None:
    assert normalize_phone_number("(978) 844-4177") == "+19788444177"
    assert normalize_phone_number("9788444177") == "+19788444177"
    assert normalize_phone_number("+19788444177") == "+19788444177"


def test_normalize_phone_number_best_effort_for_garbage() -> None:
    # Best-effort fallback should not crash; returns trimmed original or digits
    assert normalize_phone_number("   ") == ""
    assert normalize_phone_number("abc") == "abc"
    assert normalize_phone_number("+abc") == "+abc"
    assert normalize_phone_number("+1-2-3") == "+123"
