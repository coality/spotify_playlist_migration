"""Configuration store."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

STORE_DIR = Path.home() / ".spotify_migrator" / "store"
STORE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class AppConfig:
    """Application configuration."""

    source_client_id: str
    source_client_secret: str | None
    source_redirect_uri: str
    target_client_id: str
    target_client_secret: str | None
    target_redirect_uri: str
    log_level: str = "INFO"


class ConfigStore:
    """Stores application configuration."""

    def __init__(self) -> None:
        self.config_file = STORE_DIR / "config.json"

    def save(self, config: AppConfig) -> None:
        """Save configuration."""
        data = {
            "source_client_id": config.source_client_id,
            "source_client_secret": config.source_client_secret,
            "source_redirect_uri": config.source_redirect_uri,
            "target_client_id": config.target_client_id,
            "target_client_secret": config.target_client_secret,
            "target_redirect_uri": config.target_redirect_uri,
            "log_level": config.log_level,
        }
        with open(self.config_file, "w") as f:
            json.dump(data, f)
        os.chmod(self.config_file, 0o600)

    def load(self) -> AppConfig | None:
        """Load configuration."""
        if not self.config_file.exists():
            return None

        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)
            return AppConfig(**data)
        except (json.JSONDecodeError, TypeError):
            return None

    def clear(self) -> None:
        """Clear configuration."""
        if self.config_file.exists():
            self.config_file.unlink()
