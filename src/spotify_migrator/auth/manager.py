"""Authentication manager for Spotify OAuth2."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from spotify_migrator.auth.exceptions import (
    AuthenticationFailedError,
    AuthorizationError,
    InvalidTokenError,
    TokenExpiredError,
)

logger = logging.getLogger(__name__)

CACHE_DIR = Path.home() / ".spotify_migrator"
TOKEN_DIR = CACHE_DIR / "tokens"


@dataclass
class SpotifyAppConfig:
    """Configuration for a Spotify app."""

    client_id: str
    client_secret: str | None
    redirect_uri: str

    def has_client_secret(self) -> bool:
        """Check if client secret is available."""
        return bool(self.client_secret)


@dataclass
class AuthState:
    """Authentication state for an account."""

    account: str
    is_authenticated: bool = False
    user_id: str | None = None
    display_name: str | None = None
    token_expires_at: float | None = None
    needs_refresh: bool = False


class SpotifyAuthManager:
    """Manages Spotify OAuth2 authentication without opening browsers."""

    SCOPE = "playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private"

    def __init__(self, account: str, config: SpotifyAppConfig) -> None:
        self.account = account
        self.config = config
        self._sp: spotipy.Spotify | None = None
        self._token_cache: dict[str, Any] | None = None
        self._token_store_path = self._get_token_store_path()

    def _get_token_store_path(self) -> Path:
        """Get path for token storage."""
        TOKEN_DIR.mkdir(parents=True, exist_ok=True)
        safe_id = "".join(c if c.isalnum() else "_" for c in self.config.client_id)
        return TOKEN_DIR / f"{self.account}_{safe_id}.json"

    def _create_auth_manager(self) -> SpotifyOAuth:
        """Create SpotifyOAuth manager."""
        cache_path = str(self._token_store_path.with_suffix(".cache"))
        return SpotifyOAuth(
            client_id=self.config.client_id,
            client_secret=self.config.client_secret if self.config.has_client_secret() else None,
            redirect_uri=self.config.redirect_uri,
            scope=self.SCOPE,
            cache_path=cache_path,
        )

    def get_authorization_url(self) -> str:
        """Get the authorization URL for user to visit."""
        auth_manager = self._create_auth_manager()
        url = auth_manager.get_authorize_url()
        logger.info(f"Generated auth URL for {self.account}")
        return url

    def _parse_callback_url(self, callback_url: str) -> str | None:
        """Extract authorization code from callback URL or return code directly."""
        callback_url = callback_url.strip()

        if not callback_url:
            return None

        if callback_url.startswith("http://") or callback_url.startswith("https://"):
            parsed = urlparse(callback_url)
            params = parse_qs(parsed.query)
            if "code" in params:
                return params["code"][0]
            if "error" in params:
                error = params["error"][0]
                if error == "access_denied":
                    raise AuthorizationError(self.account)
                raise AuthenticationFailedError(self.account, error)
        elif callback_url.startswith("4/"):
            return callback_url[2:].strip()
        elif ":" in callback_url:
            parts = callback_url.split(":")
            if len(parts) >= 2:
                return parts[-1].strip()
        else:
            return callback_url.strip()

        return None

    def authenticate_with_callback(self, callback_url: str) -> AuthState:
        """Authenticate using the callback URL or authorization code."""
        code = self._parse_callback_url(callback_url)

        if not code:
            raise InvalidTokenError(self.account, "Could not extract authorization code from URL")

        try:
            auth_manager = self._create_auth_manager()
            token_info = auth_manager.get_access_token(code)

            if not token_info:
                raise AuthenticationFailedError(self.account, "No token info returned")

            self._token_cache = token_info
            self._sp = spotipy.Spotify(auth=token_info["access_token"])

            user = self._sp.current_user()
            user_id = user.get("id")
            display_name = user.get("display_name", user_id)

            expires_at = token_info.get("expires_at")
            needs_refresh = False
            if expires_at:
                import time
                needs_refresh = time.time() >= expires_at - 60

            logger.info(f"Successfully authenticated {self.account} as {display_name}")

            return AuthState(
                account=self.account,
                is_authenticated=True,
                user_id=user_id,
                display_name=display_name,
                token_expires_at=expires_at,
                needs_refresh=needs_refresh,
            )

        except spotipy.oauth2.SpotifyOauthError as e:
            logger.error(f"OAuth error for {self.account}: {e}")
            raise AuthenticationFailedError(self.account, str(e)) from e
        except Exception as e:
            logger.error(f"Authentication error for {self.account}: {e}")
            raise AuthenticationFailedError(self.account, str(e)) from e

    def load_cached_auth(self) -> AuthState | None:
        """Load authentication from cache if available and valid."""
        if not self._token_store_path.exists():
            return None

        try:
            auth_manager = self._create_auth_manager()
            token_info = auth_manager.get_cached_token()

            if not token_info:
                return None

            self._token_cache = token_info
            self._sp = spotipy.Spotify(auth=token_info["access_token"])

            user = self._sp.current_user()
            user_id = user.get("id")
            display_name = user.get("display_name", user_id)

            expires_at = token_info.get("expires_at")
            needs_refresh = False
            if expires_at:
                import time
                needs_refresh = time.time() >= expires_at - 60

            return AuthState(
                account=self.account,
                is_authenticated=True,
                user_id=user_id,
                display_name=display_name,
                token_expires_at=expires_at,
                needs_refresh=needs_refresh,
            )

        except spotipy.oauth2.SpotifyOauthError as e:
            logger.warning(f"Token cache invalid for {self.account}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Could not load cached auth for {self.account}: {e}")
            return None

    def refresh_token_if_needed(self) -> AuthState:
        """Refresh the access token if it's expired."""
        if not self._sp or not self._token_cache:
            raise InvalidTokenError(self.account, "No active session")

        import time
        if self._token_cache.get("expires_at") and time.time() < self._token_cache["expires_at"] - 60:
            return self.load_cached_auth() or AuthState(account=self.account)

        try:
            auth_manager = self._create_auth_manager()
            new_token = auth_manager.refresh_access_token(self._token_cache["refresh_token"])
            self._token_cache = new_token
            self._sp = spotipy.Spotify(auth=new_token["access_token"])

            user = self._sp.current_user()
            user_id = user.get("id")
            display_name = user.get("display_name", user_id)

            expires_at = new_token.get("expires_at")

            logger.info(f"Token refreshed for {self.account}")

            return AuthState(
                account=self.account,
                is_authenticated=True,
                user_id=user_id,
                display_name=display_name,
                token_expires_at=expires_at,
                needs_refresh=False,
            )

        except spotipy.oauth2.SpotifyOauthError as e:
            logger.error(f"Token refresh failed for {self.account}: {e}")
            raise TokenExpiredError(self.account) from e

    def get_client(self) -> spotipy.Spotify:
        """Get the authenticated Spotify client."""
        if self._sp is None:
            auth_state = self.load_cached_auth()
            if not auth_state or not auth_state.is_authenticated:
                raise InvalidTokenError(self.account, "Not authenticated")
        return self._sp

    def get_auth_state(self) -> AuthState:
        """Get current authentication state."""
        if self._sp:
            return AuthState(
                account=self.account,
                is_authenticated=True,
                user_id=self._sp.current_user().get("id"),
                display_name=self._sp.current_user().get("display_name"),
                needs_refresh=(
                    self._token_cache is not None and
                    self._token_cache.get("expires_at", 0) < time.time()
                ) if self._token_cache else False,
            )

        cached = self.load_cached_auth()
        if cached:
            return cached

        return AuthState(account=self.account, is_authenticated=False)

    def clear_cache(self) -> None:
        """Clear cached tokens."""
        if self._token_store_path.exists():
            self._token_store_path.unlink()
        cache_file = self._token_store_path.with_suffix(".cache")
        if cache_file.exists():
            cache_file.unlink()
        self._sp = None
        self._token_cache = None
        logger.info(f"Cleared cache for {self.account}")
