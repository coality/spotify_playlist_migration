"""Auth package."""

from spotify_migrator.auth.manager import SpotifyAuthManager, SpotifyAppConfig, AuthState
from spotify_migrator.auth.exceptions import (
    AuthError,
    TokenExpiredError,
    InvalidTokenError,
    AuthenticationFailedError,
    AuthorizationError,
)

__all__ = [
    "SpotifyAuthManager",
    "SpotifyAppConfig",
    "AuthState",
    "AuthError",
    "TokenExpiredError",
    "InvalidTokenError",
    "AuthenticationFailedError",
    "AuthorizationError",
]
