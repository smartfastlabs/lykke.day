"""Unit tests for auth cookie configuration helpers."""

from types import SimpleNamespace

from lykke.infrastructure.auth import config


def test_is_local_web_domain_true_for_localhost(monkeypatch) -> None:
    monkeypatch.setattr(
        config,
        "settings",
        SimpleNamespace(WEB_DOMAIN="http://localhost:5173"),
    )

    assert config._is_local_web_domain() is True


def test_is_local_web_domain_false_for_public_domain(monkeypatch) -> None:
    monkeypatch.setattr(
        config,
        "settings",
        SimpleNamespace(WEB_DOMAIN="https://lykke.day"),
    )

    assert config._is_local_web_domain() is False


def test_cookie_settings_for_production_non_local_domain() -> None:
    cookie_domain, cookie_secure = config._cookie_settings(
        "production",
        local_web_domain=False,
    )

    assert cookie_domain == "lykke.day"
    assert cookie_secure is True


def test_cookie_settings_for_production_local_domain() -> None:
    cookie_domain, cookie_secure = config._cookie_settings(
        "production",
        local_web_domain=True,
    )

    assert cookie_domain is None
    assert cookie_secure is False
