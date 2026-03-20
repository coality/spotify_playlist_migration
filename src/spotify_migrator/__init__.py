"""Spotify Playlist Migrator - TUI Application."""

__version__ = "2.0.0"

from spotify_migrator.models import (
    Track,
    Playlist,
    PlaylistVisibility,
    MigrationResult,
    MigrationSummary,
    MigrationStatus,
)
from spotify_migrator.auth import (
    SpotifyAuthManager,
    SpotifyAppConfig,
    AuthState,
    AuthError,
    TokenExpiredError,
    InvalidTokenError,
    AuthenticationFailedError,
    AuthorizationError,
)
from spotify_migrator.api import (
    SpotifyAPIClient,
    APIError,
    RateLimitError,
    NetworkError,
    PlaylistNotFoundError,
    TrackNotFoundError,
)
from spotify_migrator.services import (
    PlaylistMigrator,
    MigrationProgress,
    chunk_list,
)
from spotify_migrator.store import (
    TokenStore,
    TokenData,
    ConfigStore,
    AppConfig,
)
from spotify_migrator.tui import SpotifyMigratorApp

__all__ = [
    "__version__",
    "Track",
    "Playlist",
    "PlaylistVisibility",
    "MigrationResult",
    "MigrationSummary",
    "MigrationStatus",
    "SpotifyAuthManager",
    "SpotifyAppConfig",
    "AuthState",
    "AuthError",
    "TokenExpiredError",
    "InvalidTokenError",
    "AuthenticationFailedError",
    "AuthorizationError",
    "SpotifyAPIClient",
    "APIError",
    "RateLimitError",
    "NetworkError",
    "PlaylistNotFoundError",
    "TrackNotFoundError",
    "PlaylistMigrator",
    "MigrationProgress",
    "chunk_list",
    "TokenStore",
    "TokenData",
    "ConfigStore",
    "AppConfig",
    "SpotifyMigratorApp",
]
