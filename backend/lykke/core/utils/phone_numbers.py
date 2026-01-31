"""Phone number parsing and normalization utilities.

We normalize phone numbers from "outside world" inputs into a consistent form
(preferably E.164, e.g. +15551234567). This prevents mismatches between
providers (Twilio), user-entered formats, and database lookups.
"""

from __future__ import annotations

import re

import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException

from lykke.core.config import settings

_NON_DIGITS = re.compile(r"\D+")


def digits_only(phone_number: str) -> str:
    """Return only digits from a phone number-like string."""
    return _NON_DIGITS.sub("", phone_number)


def normalize_phone_number(
    phone_number: str, *, default_region: str | None = None
) -> str:
    """Normalize a phone number to a stable representation.

    Behavior:
    - If parseable and valid, returns E.164 (e.g. +15551234567)
    - Otherwise returns a best-effort normalized string:
      - If it starts with '+', returns '+' + digits
      - Else returns digits-only (or original trimmed if no digits)
    """
    raw = phone_number.strip()
    if not raw:
        return raw

    region = default_region or settings.DEFAULT_PHONE_REGION
    parse_region = None if raw.startswith("+") else region
    try:
        parsed = phonenumbers.parse(raw, parse_region)
        if phonenumbers.is_possible_number(parsed) and phonenumbers.is_valid_number(
            parsed
        ):
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
    except NumberParseException:
        pass

    digits = digits_only(raw)
    if not digits:
        return raw
    if raw.startswith("+"):
        return f"+{digits}"
    return digits
