"""Shared metric helpers for user status check-ins."""

from __future__ import annotations

USER_STATUS_DEFAULT_METRICS: tuple[tuple[str, str], ...] = (
    ("cravings", "Urge intensity and frequency."),
    ("depression", "Low mood, hopelessness, and emotional heaviness."),
    ("anxiety", "Stress, worry, and nervous system activation."),
    ("mood", "Overall emotional tone for the day."),
    ("energy", "Mental and physical energy availability."),
    ("focus", "Attention quality and ability to stay on task."),
)


def default_user_status_metrics() -> list[dict[str, str]]:
    """Return default user status metrics as template-friendly dictionaries."""
    return [
        {"name": name, "description": description}
        for name, description in USER_STATUS_DEFAULT_METRICS
    ]


def normalize_user_status_metrics(metrics: object) -> list[dict[str, str]]:
    """Normalize configured metrics into named metric definitions."""
    if not isinstance(metrics, list):
        return default_user_status_metrics()

    deduped: list[dict[str, str]] = []
    seen: set[str] = set()
    for metric in metrics:
        name = ""
        description = ""
        if isinstance(metric, str):
            cleaned_metric = metric.strip()
            if not cleaned_metric:
                continue
            if ":" in cleaned_metric:
                name_part, description_part = cleaned_metric.split(":", 1)
                name = name_part.strip()
                description = description_part.strip()
            else:
                name = cleaned_metric
        elif isinstance(metric, dict):
            raw_name = metric.get("name")
            raw_description = metric.get("description", "")
            if isinstance(raw_name, str):
                name = raw_name.strip()
            if isinstance(raw_description, str):
                description = raw_description.strip()
        else:
            continue

        if not name:
            continue

        key = name.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append({"name": name, "description": description})

    return deduped or default_user_status_metrics()
