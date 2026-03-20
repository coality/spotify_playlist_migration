"""Token storage."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from spotify_migrator.auth import SpotifyAppConfig

logger = logging.getLogger(__name__)

STORE_DIR = Path.home() / ".spotify_migrator" / "store"
STORE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TokenData:
    """Stored token data."""

    access_token: str
    token_type: str
    expires_in: int
    expires_at: float | None
    refresh_token: str | None
    scope: str
    user_id: str | None = None
    display_name: str | None = None


class TokenStore:
    """Stores authentication tokens securely."""

    def __init__(self, account: str) -> None:
        self.account = account
        self.token_file = STORE_DIR / f"{account}_tokens.json"

    def save(self, token_data: TokenData) -> None:
        """Save token data to secure storage."""
        data = asdict(token_data)
        with open(self.token_file, "w") as f:
            json.dump(data, f)
        os.chmod(self.token_file, 0o600)
        logger.info(f"Token saved for {self.account}")

    def load(self) -> TokenData | None:
        """Load token data from storage."""
        if not self.token_file.exists():
            return None

        try:
            with open(self.token_file, "r") as f:
                data = json.load(f)
            return TokenData(**data)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Could not load token for {self.account}: {e}")
            return None

    def clear(self) -> None:
        """Clear stored tokens."""
        if self.token_file.exists():
            self.token_file.unlink()
            logger.info(f"Token cleared for {self.account}")

    def exists(self) -> bool:
        """Check if tokens are stored."""
        return self.token_file.exists()
