"""Utility functions for loading user settings."""

from pathlib import Path

from planned.core.config import settings
from planned.domain.entities.user_settings import UserSettings


def load_user_settings(data_path: str | None = None) -> UserSettings:
    """Load user settings from the configuration file.
    
    Args:
        data_path: Optional data path override. If None, uses settings.DATA_PATH.
        
    Returns:
        UserSettings instance loaded from the file.
    """
    path = Path(data_path or settings.DATA_PATH) / "config" / "user-settings.json"
    with open(path) as f:
        return UserSettings.model_validate_json(
            f.read(),
            by_alias=False,
            by_name=True,
        )

